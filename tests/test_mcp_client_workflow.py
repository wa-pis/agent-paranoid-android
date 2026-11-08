"""Real SDK client acceptance of local source-free generator workflows."""
from __future__ import annotations

import asyncio
import csv
import json
import os
import sys
from datetime import timedelta
from importlib.metadata import version
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import yaml
import pytest


@pytest.mark.parametrize("interrupted", [False, True])
@pytest.mark.parametrize("scalable", [False, True])
def test_client_plans_reviews_and_replays_synthetic_artifacts(
    tmp_path: Path, interrupted: bool, scalable: bool,
) -> None:
    source = tmp_path / "customers.csv"
    source.write_text(
        "customer_id,email,status\n"
        "1,alice@example.com,active\n"
        "2,bob@example.com,paused\n"
    )
    env = {**os.environ, "TEST_DATA_AGENT_WORKSPACE_ROOT": str(tmp_path),
           "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    program = """
import os
from pathlib import Path
import test_data_agent.agent_approval as approval
from test_data_agent.mcp_generator_server import main
Path(os.environ['TEST_PID_PATH']).write_text(str(os.getpid()))
if os.environ['TEST_INTERRUPT'] == '1':
    original = approval.publish_agent_completion
    def interrupt_once(*args, **kwargs):
        approval.publish_agent_completion = original
        raise RuntimeError('synthetic-private-interruption-marker')
    approval.publish_agent_completion = interrupt_once
raise SystemExit(main())
"""
    pid_path = tmp_path / "server.pid"
    env.update(TEST_PID_PATH=str(pid_path), TEST_INTERRUPT="1" if interrupted else "0")
    server = StdioServerParameters(
        command=sys.executable,
        args=["-c", program], env=env,
    )
    responses: list[str] = []

    async def run() -> None:
        with (tmp_path / "stderr.txt").open("w+") as errors:
            async with stdio_client(server, errlog=errors) as (read, write):
                async with ClientSession(
                    read, write, read_timeout_seconds=(timedelta(seconds=15)
                        if int(version("mcp").split(".")[0]) == 1 else 15),
                ) as client:
                    await client.initialize()
                    tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                    assert {"plan_dataset", "inspect_dataset_plan",
                            "approve_dataset_plan", "recover_dataset_plan"} <= tools.keys()
                    assert "human review" in tools["approve_dataset_plan"].description

                    async def call(name: str, args: dict[str, Any]) -> dict[str, Any]:
                        result = await client.call_tool(name, args)
                        responses.append(result.model_dump_json())
                        assert not result.model_dump(by_alias=True)["isError"], responses[-1]
                        text = next(item.text for item in result.content if item.type == "text")
                        return json.loads(text)

                    for workspace in ["agent/first", "agent/replay"]:
                        plan = await call("plan_dataset", {
                            "source_path": "customers.csv", "workspace_path": workspace,
                            "count": 4, "seed": 81, "output_format": "csv",
                            "table_name": "customers",
                            "execution_policy": {"workers": 2, "batch_size": 2} if scalable else None,
                        })
                        assert plan["approval_required"] is True
                        generated = tmp_path / workspace / "generated"
                        assert not generated.exists()
                        state = await call("inspect_dataset_plan", {"workspace_path": workspace})
                        spec_path = tmp_path / plan["spec_path"]
                        if scalable:
                            forecast = await call("estimate_dataset_capacity", {"spec_path": plan["spec_path"]})
                            assert forecast["duration_seconds"] is None
                            assert forecast["entities"][0]["rows"] == 4
                            assert not generated.exists()
                        spec_bytes = spec_path.read_bytes()
                        changed_spec = yaml.safe_load(spec_bytes)
                        if scalable:
                            changed_spec["generation_settings"]["execution_policy"]["max_seconds"] = 60
                        else:
                            changed_spec["entities"][0]["row_count"] = 5
                        spec_path.write_text(yaml.safe_dump(changed_spec))
                        rejected = await client.call_tool("approve_dataset_plan", {
                            "workspace_path": workspace,
                            "reviewed_spec_sha256": state["review"]["current_spec_sha256"],
                        })
                        responses.append(rejected.model_dump_json())
                        assert rejected.model_dump(by_alias=True)["isError"]
                        assert not generated.exists()
                        spec_path.write_bytes(spec_bytes)
                        state = await call("inspect_dataset_plan", {"workspace_path": workspace})
                        # Fictional test approval; not evidence of manual human acceptance.
                        approval_args = {
                            "workspace_path": workspace,
                            "reviewed_spec_sha256": state["review"]["current_spec_sha256"],
                        }
                        if interrupted and workspace == "agent/first":
                            failed = await client.call_tool("approve_dataset_plan", approval_args)
                            responses.append(failed.model_dump_json())
                            assert failed.model_dump(by_alias=True)["isError"]
                            before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                                      for path in generated.iterdir() if path.is_file()}
                            state = await call("inspect_dataset_plan", {"workspace_path": workspace})
                            assert state["phase"] == "recovery_required"
                            assert state["next_action"] == "recover"
                            approved = await call("recover_dataset_plan", approval_args)
                            after = {path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                                     for path in generated.iterdir() if path.is_file()}
                            assert before == after
                        else:
                            approved = await call("approve_dataset_plan", {
                                "workspace_path": workspace,
                                "reviewed_spec_sha256": state["review"]["current_spec_sha256"],
                            })
                        assert approved["row_counts"] == {"customers": 4}
                        assert approved["validation_valid"] is True
                        assert approved["synthetic"] is True
                        assert approved["source_rows_copied"] is False
                        manifest = json.loads((tmp_path / approved["manifest_path"]).read_text())
                        assert manifest["synthetic"] is True
                        assert manifest["source_rows_copied"] is False
                        assert (await call("inspect_dataset_plan", {
                            "workspace_path": workspace,
                        }))["phase"] == "completed"
            errors.seek(0)
            logs = errors.read()
            for sentinel in ["alice@example.com", "bob@example.com",
                             "synthetic-private-interruption-marker"]:
                assert sentinel not in logs
                assert sentinel not in "\n".join(responses)

    asyncio.run(asyncio.wait_for(run(), timeout=60))
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_path.read_text()), 0)
    first = tmp_path / "agent/first/generated/customers.csv"
    replay = tmp_path / "agent/replay/generated/customers.csv"
    assert first.read_bytes() == replay.read_bytes()
    with source.open(newline="") as handle:
        source_rows = {tuple(row.items()) for row in csv.DictReader(handle)}
    with first.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert source_rows.isdisjoint(tuple(row.items()) for row in rows)


@pytest.mark.parametrize("failure", ["error", "timeout"])
def test_client_failure_closes_server_process(tmp_path: Path, failure: str) -> None:
    pid_path = tmp_path / "server.pid"
    program = """
import os
from pathlib import Path
from test_data_agent.mcp_generator_server import main
Path(os.environ['TEST_PID_PATH']).write_text(str(os.getpid()))
raise SystemExit(main())
"""
    server = StdioServerParameters(command=sys.executable, args=["-c", program], env={
        **os.environ, "TEST_PID_PATH": str(pid_path),
        "TEST_DATA_AGENT_WORKSPACE_ROOT": str(tmp_path),
        "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
    })

    async def run() -> None:
        with (tmp_path / "stderr.txt").open("w") as errors:
            async with stdio_client(server, errlog=errors) as (read, write):
                async with ClientSession(
                    read, write, read_timeout_seconds=(timedelta(seconds=15)
                        if int(version("mcp").split(".")[0]) == 1 else 15),
                ) as client:
                    await client.initialize()
                    if failure == "error":
                        raise ValueError("synthetic-client-stop")
                    await asyncio.wait_for(asyncio.Event().wait(), timeout=0.01)

    with pytest.raises(BaseExceptionGroup) as caught:
        asyncio.run(asyncio.wait_for(run(), timeout=30))
    assert caught.value.subgroup(ValueError if failure == "error" else TimeoutError)
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_path.read_text()), 0)


@pytest.mark.parametrize('interrupted', [False, True])
def test_client_relational_plan_exact_engine_review_and_recovery(tmp_path: Path, interrupted: bool) -> None:
    """Synthetic SDK evidence only; this is not manual human acceptance."""
    source = tmp_path/'source'
    source.mkdir()
    (source/'customers.csv').write_text('customer_id,label\nC1,fictional alpha\nC2,fictional beta\n')
    (source/'orders.csv').write_text('order_id,customer_id,label\nO1,C1,fictional one\nO2,C2,fictional two\nO3,C1,fictional three\n')
    env = {**os.environ, 'TEST_DATA_AGENT_WORKSPACE_ROOT': str(tmp_path),
           'PYTHONPATH': str(Path(__file__).resolve().parents[1]/'src')}
    program = '''
import test_data_agent.agent_approval as approval
from test_data_agent.mcp_generator_server import main
original = approval.publish_agent_completion

def interrupt_once(*args, **kwargs):
    approval.publish_agent_completion = original
    raise RuntimeError('fictional-private-interruption')
'''
    if interrupted:
        program += '\napproval.publish_agent_completion = interrupt_once\n'
    program += '\nraise SystemExit(main())\n'
    async def run() -> None:
        with (tmp_path/'stderr.txt').open('w+') as errors:
            async with stdio_client(StdioServerParameters(command=sys.executable, args=['-c', program], env=env), errlog=errors) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    responses = []
                    async def call(name, args):
                        result = await client.call_tool(name, args)
                        responses.append(result.model_dump_json())
                        assert not result.model_dump(by_alias=True)["isError"], responses[-1]
                        return json.loads(next(item.text for item in result.content if item.type == 'text'))
                    plan = await call('plan_dataset', dict(source_path='source', workspace_path='plan', count=7,
                        seed=42, output_format='csv', execution_policy=dict(engine='scalable-relational-v1', workers=2, batch_size=3)))
                    path = tmp_path/plan['spec_path']
                    data = yaml.safe_load(path.read_text())
                    assert data['relationships']
                    state = await call('inspect_dataset_plan', dict(workspace_path='plan'))
                    reviewed = state['review']['current_spec_sha256']
                    original = path.read_bytes()
                    data['generation_settings']['execution_policy']['engine'] = 'scalable-v1'
                    path.write_text(yaml.safe_dump(data))
                    rejection = await client.call_tool('approve_dataset_plan', dict(workspace_path='plan', reviewed_spec_sha256=reviewed))
                    assert rejection.model_dump(by_alias=True)["isError"]
                    assert not (tmp_path/'plan/generated').exists()
                    path.write_bytes(original)
                    state = await call('inspect_dataset_plan', dict(workspace_path='plan'))
                    args = dict(workspace_path='plan', reviewed_spec_sha256=state['review']['current_spec_sha256'])
                    if interrupted:
                        failure = await client.call_tool('approve_dataset_plan', args)
                        assert failure.model_dump(by_alias=True)["isError"]
                        assert (await call('inspect_dataset_plan', dict(workspace_path='plan')))['phase'] == 'recovery_required'
                        result = await call('recover_dataset_plan', args)
                    else:
                        result = await call('approve_dataset_plan', args)
                    assert result['row_counts'] == {'customers': 7, 'orders': 7}
                    assert result['validation_valid'] and result['source_rows_copied'] is False
                    report = json.loads((tmp_path/'plan/generated/validation_report.json').read_text())
                    assert report['utility']['relationship_checks'] == 'executed'
                    assert report['utility']['active_relationships'] == 1
                    assert 'fictional-private-interruption' not in '\n'.join(responses)
                    assert 'fictional alpha' not in '\n'.join(responses)
            errors.seek(0)
            assert 'fictional-private-interruption' not in errors.read()
    asyncio.run(asyncio.wait_for(run(), timeout=60))
