"""Run configured profile inference and synthetic export through each interface."""

import asyncio
import json
import sys

import pytest
import yaml
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from scripts.accept_cross_interface_matrix import check_bundle
from tests.test_acceptance_mcp_permissions import _environment, _timeout
from tests.test_inference_options import OPTIONS, profile
from tests.test_source_output_matrix import SOURCES, source_profile
from test_data_agent.cli import main
from test_data_agent.core.constraint import Constraint, ConstraintStatus
from test_data_agent.core.inference import parse_inference_options
from test_data_agent.core.relationship import Relationship
from test_data_agent.core.settings import OutputFormat
from test_data_agent.generation.planner import infer_dataset_spec
from test_data_agent.io.readers import load_dataset_spec
from test_data_agent.io.workflows import generate_dataset_bundle, infer_dataset_spec_artifact
from test_data_agent.io.artifacts import write_dataset_spec_artifact
from test_data_agent.rules import business_rules_from_dict

CONFIG = {
    **OPTIONS,
    "field_rules": [{"entity": "parts", "field_suffix": "_code",
                     "action": "keep_builtin", "priority": 10}],
    "min_constraint_confidence": 0.7,
}
INPUTS = tuple(source for source in SOURCES if not source.endswith("_spec"))
SPEC_FORMATS = ("json", "yaml", "yml")


@pytest.mark.parametrize("source", INPUTS)
def test_configured_inference_full_route_matrix(tmp_path, source, capsys):
    acquired = source_profile(source, tmp_path / "source")
    # Acquisition adapters can provide different statistics. The contract
    # promises parity on equivalent metadata, not identical profiler estimates.
    assert "source-marker" not in acquired.model_dump_json()
    common = profile(acquired.source_type)
    label = next(field for field in acquired.entities[0].fields if field.name == "label")
    assert label.data_type.value == "string"
    label = label.model_copy(update={
        "distribution": {}, "nullable": False, "null_ratio": 0.0,
        "is_identifier": False, "sensitive": False, "semantic_type": None,
    })
    common.entities[0].fields.append(label)
    common.entities[1].fields.append(label.model_copy(update={"name": "widget_link"}))
    common.relationships.append(Relationship(
        parent_entity="widgets", parent_field="widget_code",
        child_entity="parts", child_field="widget_link", confidence=0.4,
        status="declared",
    ))
    item = Constraint(
        type="conditional_required", entity="widgets", fields=["label"],
        condition={"field": "widget_code", "equals": "fictional"}, confidence=0.4,
    )
    common.constraints = [item, item.model_copy(update={"status": ConstraintStatus.CONFIRMED})]
    common.has_unmodeled_expressions = acquired.has_unmodeled_expressions
    (tmp_path / "profile.json").write_text(common.model_dump_json())
    (tmp_path / "options.yaml").write_text(yaml.safe_dump(CONFIG))
    options = parse_inference_options(CONFIG)
    baseline = infer_dataset_spec(common, inference_options=options)
    evidence = baseline.inference_evidence
    assert evidence is not None
    assert evidence.options_sha256 == options.fingerprint()
    assert evidence.constraints_filtered == evidence.relationships_filtered == 1
    assert [edge.status for edge in baseline.relationships] == ["declared"]
    assert [rule.status for rule in baseline.constraints] == ["confirmed"]
    assert baseline.entities[0].fields[0].is_identifier
    assert not baseline.entities[1].fields[0].is_identifier
    assert baseline.entities[0].fields[1].sensitive
    assert not baseline.entities[0].fields[1].is_identifier
    parameters = StdioServerParameters(
        command=sys.executable, args=["-I", "-m", "test_data_agent.mcp_generator_server"],
        env=_environment(tmp_path), cwd=str(tmp_path),
    )

    async def run():
        with (tmp_path / "stderr.log").open("w+") as errors:
            async with stdio_client(parameters, errlog=errors) as (reader, writer):
                async with ClientSession(reader, writer, read_timeout_seconds=_timeout()) as client:
                    await client.initialize()

                    async def call(tool, **arguments):
                        result = await client.call_tool(tool, arguments)
                        assert not result.model_dump(by_alias=True)["isError"], (source, tool, result)
                        assert "source-marker" not in result.model_dump_json()

                    if source == "csv":
                        selector = {"entity": "😀" * 128, "field_suffix": "😀" * 128}
                        large = {
                            "version": "1",
                            "identifier_rules": [selector] * 64,
                            "field_rules": [dict(selector, action="keep_builtin")] * 64,
                        }
                        encoded = json.dumps(large)
                        assert len(encoded) > 65_536
                        options_file = tmp_path / "large-options.json"
                        options_file.write_text(encoded)
                        expected = infer_dataset_spec(common, inference_options=parse_inference_options(large))
                        cli_output = tmp_path / "large-cli.json"
                        assert main(["infer-spec", str(tmp_path / "profile.json"), "--inference-options",
                                     str(options_file), "--output", str(cli_output)]) == 0
                        await call("infer_dataset_spec", profile_path="profile.json",
                                   output_path="large-mcp.json", inference_options=large)
                        assert load_dataset_spec(cli_output) == load_dataset_spec(tmp_path / "large-mcp.json") == expected

                    missing = common.model_copy(deep=True)
                    missing.entities[0].fields[-1].null_ratio = None
                    failures = [(missing, "unknown null statistics")]
                    if source.endswith("_query"):
                        failures.extend([
                            (common.model_copy(update={"has_unmodeled_expressions": None}),
                             "requires reprofiling"),
                            (common.model_copy(update={"has_unmodeled_expressions": True}),
                             "SQL expression dependencies are unsupported"),
                        ])
                    for rejected_profile, message in failures:
                        with pytest.raises(ValueError, match=message):
                            infer_dataset_spec(rejected_profile, inference_options=options)
                        missing_path = tmp_path / "missing.json"
                        missing_path.write_text(rejected_profile.model_dump_json())
                        rejected_path = tmp_path / "rejected.json"
                        assert main(["infer-spec", str(missing_path), "--inference-options",
                                     str(tmp_path / "options.yaml"), "--output", str(rejected_path)]) != 0
                        assert message in capsys.readouterr().err
                        assert not rejected_path.exists()
                        rejected = await client.call_tool("infer_dataset_spec", {
                            "profile_path": missing_path.name, "output_path": rejected_path.name,
                            "inference_options": CONFIG,
                        })
                        assert rejected.model_dump(by_alias=True)["isError"]
                        assert message in rejected.model_dump_json()
                        assert not rejected_path.exists()

                    for suffix in SPEC_FORMATS:
                        paths = {name: tmp_path / f"{name}.{suffix}" for name in ("python", "cli", "mcp")}
                        infer_dataset_spec_artifact(common, output_path=paths["python"], inference_options=options)
                        assert main(["infer-spec", str(tmp_path / "profile.json"), "--inference-options",
                                     str(tmp_path / "options.yaml"), "--output", str(paths["cli"])]) == 0
                        profile_argument = ({"profile_payload": common.model_dump(mode="json")}
                                            if suffix == "yml" else {"profile_path": "profile.json"})
                        await call("infer_dataset_spec", output_path=paths["mcp"].name,
                                   inference_options=CONFIG, **profile_argument)
                        for path in paths.values():
                            assert load_dataset_spec(path) == baseline, (source, path.name)
                        for output in OutputFormat:
                            snapshots = []
                            for interface, path in paths.items():
                                spec = load_dataset_spec(path)
                                spec.generation_settings.output_format = output
                                spec.generation_settings.seed = 17
                                spec.business_rules = business_rules_from_dict({
                                    "field_rules": [{"table": "widgets", "field": "label", "required": True}],
                                })
                                reviewed = tmp_path / f"reviewed-{interface}-{output.value}.{suffix}"
                                write_dataset_spec_artifact(spec, reviewed)
                                folder = tmp_path / f"{interface}-{suffix}-{output.value}"
                                if interface == "python":
                                    generate_dataset_bundle(load_dataset_spec(reviewed), output_folder=folder)
                                elif interface == "cli":
                                    assert main(["generate", str(reviewed), "--output", str(folder)]) == 0
                                else:
                                    await call("generate_dataset", spec_path=reviewed.name, output_folder=folder.name)
                                snapshots.append(check_bundle(folder, spec, "source-marker"))
                            assert snapshots[0] == snapshots[1] == snapshots[2], (source, suffix, output)

    asyncio.run(asyncio.wait_for(run(), timeout=120))
