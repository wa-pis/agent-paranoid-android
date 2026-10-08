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
def test_client_plans_reviews_and_replays_synthetic_artifacts(
    tmp_path: Path, interrupted: bool,
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
                        })
                        assert plan["approval_required"] is True
                        generated = tmp_path / workspace / "generated"
                        assert not generated.exists()
                        state = await call("inspect_dataset_plan", {"workspace_path": workspace})
                        spec_path = tmp_path / plan["spec_path"]
                        spec_bytes = spec_path.read_bytes()
                        changed_spec = yaml.safe_load(spec_bytes)
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
