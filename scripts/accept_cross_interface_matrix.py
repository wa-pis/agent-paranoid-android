"""Installed Python/CLI/real-stdio MCP acceptance; fictional source handoffs only.

The target environment needs pytest (for the shared fictional fixture), MCP and
the capabilities selected by the matrix, including PyArrow for Parquet. Run the
controller with --python TARGET/bin/python --package-root TARGET/site-packages
--sha EXACT_SHA --output /private/tmp/matrix.json. Subsets are explicitly labelled.
No source rows, SQL, subprocess logs or exception text enter the evidence report.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from datetime import timedelta
from decimal import Decimal
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import runpy
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any


SOURCES = ("csv", "csv_folder", "parquet", "json_profile", "trino", "postgres",
           "postgres_query", "trino_query", "yaml_spec", "json_spec")
OUTPUTS = ("csv", "json", "parquet", "sql")
MODES = ("valid", "edge", "load_test", "mixed", "negative")
INTERFACES = ("python", "cli", "mcp")
LOG_LIMIT = 4 * 1024 * 1024


class AcceptanceFailure(RuntimeError):
    """A fixed, value-free assertion category suitable for persisted evidence."""


def require(condition: bool, category: str) -> None:
    if not condition:
        raise AcceptanceFailure(category)


def digest(value: Any) -> str:
    def scalar(item: Any) -> Any:
        if isinstance(item, Decimal):
            return {"decimal": str(item)}
        raise TypeError("unsupported acceptance scalar")
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    default=scalar, allow_nan=False).encode()).hexdigest()


def clean_environment(workspace: Path | None = None) -> dict[str, str]:
    allowed = ("PATH", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "LANG", "LC_ALL")
    result = {key: os.environ[key] for key in allowed if key in os.environ}
    result["PYTHONDONTWRITEBYTECODE"] = "1"
    if workspace is not None:
        result["TEST_DATA_AGENT_WORKSPACE_ROOT"] = str(workspace)
    return result


def ledger(args: argparse.Namespace) -> list[dict[str, Any]]:
    return [{"id": f"core/{source}/{output}/{mode}/{interface}",
             "source": source, "output": output, "mode": mode, "interface": interface,
             "status": "blocked", "reason": "not_executed"}
            for source in args.source for output in args.output_format
            for mode in args.mode for interface in args.interface]


def save_report(path: Path, report: dict[str, Any]) -> None:
    report["counts"] = dict(Counter(case["status"] for case in report["cases"]))
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def bounded_text(path: Path) -> str:
    require(path.stat().st_size <= LOG_LIMIT, "process_output_limit")
    return path.read_text(errors="replace")


def stop_owned_process(pid: int, requested_signal: int) -> None:
    """Terminate only a PID admitted by this controller or its owned PID file."""
    try:
        if hasattr(os, "getpgid") and os.getpgid(pid) == pid:
            os.killpg(pid, requested_signal)
        else:
            os.kill(pid, requested_signal)
    except ProcessLookupError:
        pass


def supervise(command: list[str], workspace: Path, timeout: float) -> tuple[bool, int]:
    """Bound worker waiting and clean the SDK's separate server kill scope."""
    timed_out = False
    with (workspace / "worker-stdout").open("w") as out, (workspace / "worker-stderr").open("w") as err:
        process = subprocess.Popen(command, cwd=workspace, env=clean_environment(),
                                   stdout=out, stderr=err, start_new_session=True)
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            if process.poll() is None:
                stop_owned_process(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    stop_owned_process(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            pid_path = workspace / "server.pid"
            if pid_path.is_file():
                pid = int(pid_path.read_text())
                stop_owned_process(pid, signal.SIGTERM)
                # The server uses only local generation in this runner. Kill any
                # surviving admitted kill scope before deleting its workspace.
                stop_owned_process(pid, signal.SIGKILL)
    return timed_out, process.returncode


def check_bundle(folder: Path, expected_spec: Any, source_marker: str) -> dict[str, Any]:
    from test_data_agent.core.limits import GenerationBudget
    from test_data_agent.generation import generate_dataset
    from test_data_agent.io.artifacts import dataset_spec_fingerprint
    from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec
    from test_data_agent.rules.typed_values import numeric_row
    from test_data_agent.validation import validate_dataset

    saved = load_dataset_spec(folder / "dataset_spec.yaml")
    require(saved.model_dump(mode="json") == expected_spec.model_dump(mode="json"),
            "effective_spec_mismatch")
    rows = load_dataset_rows(folder)
    expected = generate_dataset(expected_spec, seed=17)
    normalized = {
        entity.name: [numeric_row(row, entity, budget=GenerationBudget())
                      for row in rows[entity.name]] for entity in saved.entities}
    expected_normalized = {
        entity.name: [numeric_row(row, entity, budget=GenerationBudget())
                      for row in expected[entity.name]] for entity in saved.entities}
    require(normalized == expected_normalized, "restored_logical_values_mismatch")
    require(source_marker not in json.dumps(rows, default=str), "source_marker_reused")
    revalidated = validate_dataset(rows, saved).model_dump(mode="json")
    expected_validation = validate_dataset(expected, saved).model_dump(mode="json")
    persisted = json.loads((folder / "validation_report.json").read_text())
    require(revalidated == persisted == expected_validation, "validation_mismatch")
    valid = saved.generation_settings.mode.value not in {"mixed", "negative"}
    require(revalidated["valid"] is valid, "mode_validation_outcome_mismatch")
    manifest = json.loads((folder / "generation_manifest.json").read_text())
    require(manifest["synthetic"] is True and manifest["source_rows_copied"] is False,
            "provenance_mismatch")
    require(manifest["spec_sha256"] == dataset_spec_fingerprint(saved), "spec_hash_mismatch")
    require(manifest["validation_valid"] is valid, "manifest_validation_mismatch")
    require(manifest["seed"] == 17, "seed_mismatch")
    counts = {entity.name: len(rows[entity.name]) for entity in saved.entities}
    require(counts == manifest["row_counts"] == {
        entity.name: entity.row_count for entity in saved.entities}, "row_count_mismatch")
    business = json.loads((folder / "business_validation_report.json").read_text())
    summary = manifest["business_validation"]
    require(summary["expectations_met"] is True
            and summary["unexpected_violation_count"] == 0
            and summary["missing_expected_violation_count"] == 0,
            "business_expectations_mismatch")
    for relative, expected_hash in manifest["reproducibility"]["output_sha256"].items():
        require(hashlib.sha256((folder / relative).read_bytes()).hexdigest() == expected_hash,
                "artifact_hash_mismatch")
    return {"logical_rows_sha256": digest(normalized), "spec_sha256": manifest["spec_sha256"],
            "validation_sha256": digest(persisted), "manifest_sha256": digest(manifest),
            "business_report_sha256": digest(business), "row_counts": counts,
            "validation_valid": valid,
            "artifact_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in sorted(folder.iterdir()) if path.is_file()}}


def run_cli(entrypoint: Path, spec: Path, target: Path, workspace: Path,
            timeout: float, expected_valid: bool) -> None:
    with tempfile.TemporaryDirectory(dir=workspace, prefix="cli-log-") as temporary:
        out, err = Path(temporary) / "stdout", Path(temporary) / "stderr"
        with out.open("w") as stdout, err.open("w") as stderr:
            completed = subprocess.run(
                [sys.executable, "-I", str(entrypoint), "generate", str(spec),
                 "--output", str(target), "--json"], cwd=workspace,
                env=clean_environment(workspace), stdout=stdout, stderr=stderr,
                timeout=timeout, check=False)
        text, errors = bounded_text(out), bounded_text(err)
        require("source-marker" not in text + errors, "cli_source_disclosure")
        require(completed.returncode == (0 if expected_valid else 1), "cli_exit_mismatch")
        payload = json.loads(text)
        require(payload["exit_code"] == completed.returncode, "cli_envelope_exit_mismatch")
        require(payload["status"] == ("succeeded" if expected_valid else "validation_failed"),
                "cli_envelope_status_mismatch")


def load_fixture(path: Path) -> dict[str, Any]:
    """Admit the reviewed fixture's local helpers only while loading it."""
    original_path = sys.path[:]
    sys.path.insert(0, str(path.resolve().parent.parent))
    try:
        return runpy.run_path(str(path))
    finally:
        sys.path[:] = original_path


async def run_campaign(args: argparse.Namespace, report: dict[str, Any]) -> None:
    import test_data_agent
    from test_data_agent.core.field import FieldType
    from test_data_agent.core.settings import GenerationMode, OutputFormat
    from test_data_agent.io.readers import load_dataset_spec
    from test_data_agent.io.workflows import generate_dataset_bundle
    from test_data_agent.io.writers import dataset_spec_to_yaml

    workspace = args.workspace.resolve(strict=True)
    package_root = args.package_root.resolve(strict=True)
    installed = Path(test_data_agent.__file__).resolve(strict=True)
    require(installed.is_relative_to(package_root), "package_provenance_mismatch")
    require(not installed.is_relative_to(args.fixture_file.parent.parent), "source_tree_import")
    fixture = load_fixture(args.fixture_file)
    require(tuple(fixture["SOURCES"]) == SOURCES, "source_inventory_changed")
    require({item.value for item in FieldType} == {
        "integer", "float", "decimal", "boolean", "string", "date", "datetime"},
        "field_inventory_changed")
    require({item.value for item in OutputFormat} == set(OUTPUTS), "output_inventory_changed")
    require({item.value for item in GenerationMode} == set(MODES), "mode_inventory_changed")
    report["environment"] = {
        "python": sys.version.split()[0], "package_version": version("agent-paranoid-android"),
        "module_path": str(installed),
        "dependencies": {name: version(name) for name in
                         ("Faker", "pydantic", "PyYAML", "pytest")}}
    for optional in ("mcp", "pyarrow", "sqlglot"):
        try:
            report["environment"]["dependencies"][optional] = version(optional)
        except Exception:
            pass
    entrypoint = Path(sys.executable).parent / "test-data-agent"
    if "cli" in args.interface:
        require(entrypoint.is_file(), "installed_cli_missing")
    prepared: dict[str, tuple[Path, str | None]] = {}
    for source in args.source:
        source_root = workspace / "sources" / source
        source_root.parent.mkdir(exist_ok=True)
        profile = None if source.endswith("_spec") else fixture["source_profile"](source, source_root)
        if profile is not None:
            require(bool(profile.entities)
                    and len(profile.entities[0].fields) == len(fixture["COLUMNS"]),
                    "source_profile_schema_mismatch")
            profile_payload = profile.model_dump(mode="json")
            require("source-marker" not in json.dumps(profile_payload), "profile_source_disclosure")
            (workspace / f"profile-{source}.json").write_text(json.dumps(profile_payload))
            prepared[source] = (source_root, digest(profile_payload))
        else:
            source_root.mkdir()
            prepared[source] = (source_root, None)

    async def execute(client: Any | None) -> None:
        baselines: dict[tuple[str, str, str], dict[str, Any]] = {}
        for case in report["cases"]:
            started = time.monotonic()
            source, output, mode = case["source"], case["output"], case["mode"]
            interface = case["interface"]
            key = (source, output, mode)
            spec = fixture["reviewed_spec"]()
            spec.generation_settings.mode = GenerationMode(mode)
            spec.generation_settings.invalid_ratio = 1 if mode in {"negative", "mixed"} else 0
            spec.generation_settings.output_format = OutputFormat(output)
            effective = spec.model_copy(deep=True)
            if mode == "load_test":
                for entity in effective.entities:
                    entity.row_count *= effective.generation_settings.load_multiplier
                effective.generation_settings.load_multiplier = 1
            case_root = workspace / "cases" / source / output / mode / interface
            case_root.mkdir(parents=True)
            spec_path = case_root / ("reviewed.yaml" if source == "yaml_spec" else "reviewed.json")
            spec_path.write_text(dataset_spec_to_yaml(spec) if source == "yaml_spec"
                                 else spec.model_dump_json())
            case["acquisition"] = ("reviewed_specification" if source.endswith("_spec")
                                   else "fictional_profile_to_reviewed_specification")
            case["database_evidence"] = ("mocked_aggregate_handoff" if source in {
                "trino", "postgres", "postgres_query", "trino_query"} else "not_applicable")
            case["profile_sha256"] = prepared[source][1]
            try:
                snapshots = []
                for repeat in ("first", "replay"):
                    target = case_root / repeat
                    if interface == "python":
                        generate_dataset_bundle(load_dataset_spec(spec_path), output_folder=target)
                    elif interface == "cli":
                        run_cli(entrypoint, spec_path, target, workspace, args.timeout,
                                mode not in {"mixed", "negative"})
                    else:
                        if client is None:
                            raise AcceptanceFailure("mcp_session_unavailable")
                        result = await asyncio.wait_for(client.call_tool("generate_dataset", {
                            "spec_path": str(spec_path.relative_to(workspace)),
                            "output_folder": str(target.relative_to(workspace)),
                        }), timeout=args.timeout)
                        require(not result.model_dump(by_alias=True).get("isError", False),
                                "mcp_tool_error")
                        texts = [item.text for item in result.content if item.type == "text"]
                        require(len(texts) == 1 and "source-marker" not in texts[0],
                                "mcp_response_disclosure_or_shape")
                        payload = json.loads(texts[0])
                        require("rows" not in payload and payload["source_rows_copied"] is False
                                and payload["synthetic"] is True,
                                "mcp_response_provenance")
                        require(payload["mode"] == mode and payload["output_format"] == output
                                and payload["seed"] == 17
                                and payload["row_counts"] == {entity.name: entity.row_count
                                                               for entity in effective.entities},
                                "mcp_response_effective_settings_mismatch")
                        validated = await asyncio.wait_for(client.call_tool("validate_dataset", {
                            "spec_path": str((target / "dataset_spec.yaml").relative_to(workspace)),
                            "rows_folder": str(target.relative_to(workspace)),
                        }), timeout=args.timeout)
                        require(not validated.model_dump(by_alias=True).get("isError", False),
                                "mcp_revalidation_error")
                        validation_texts = [item.text for item in validated.content if item.type == "text"]
                        require(len(validation_texts) == 1 and "source-marker" not in validation_texts[0],
                                "mcp_validation_disclosure_or_shape")
                        require(json.loads(validation_texts[0])["validation"] == json.loads(
                            (target / "validation_report.json").read_text()),
                            "mcp_revalidation_report_mismatch")
                    snapshots.append(check_bundle(target, effective, "source-marker"))
                require(snapshots[0] == snapshots[1], "same_seed_replay_mismatch")
                if key in baselines:
                    require(snapshots[0] == baselines[key], "cross_interface_mismatch")
                else:
                    baselines[key] = snapshots[0]
                case.update(status="passed", reason=None, evidence=snapshots[0], repeat_count=2)
            except Exception as exc:
                case.update(status="failed", reason=(str(exc) if type(exc) is AcceptanceFailure
                                                       else type(exc).__name__))
            case["duration_seconds"] = round(time.monotonic() - started, 3)
            save_report(args.output, report)

    if "mcp" not in args.interface:
        await execute(None)
        return
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    console = Path(sys.executable).parent / "test-data-agent-mcp-generator"
    require(console.is_file(), "installed_mcp_entrypoint_missing")
    pid_path = workspace / "server.pid"
    # Execute the installed console wrapper, keeping one PID across exec so that
    # SDK context teardown can be checked without importing server helpers.
    bootstrap = ("import os,pathlib,sys;pathlib.Path(sys.argv[1]).write_text(str(os.getpid()));"
                 "os.execv(sys.executable,[sys.executable,'-I',sys.argv[2]])")
    server = StdioServerParameters(command=sys.executable,
        args=["-I", "-c", bootstrap, str(pid_path), str(console)],
        cwd=str(workspace), env=clean_environment(workspace))
    stderr_path = workspace / "server-stderr"
    try:
        with stderr_path.open("w") as errors:
            async with stdio_client(server, errlog=errors) as (read, write):
                sdk_timeout: Any = (timedelta(seconds=args.timeout)
                                   if int(version("mcp").split(".")[0]) == 1 else args.timeout)
                async with ClientSession(read, write, read_timeout_seconds=sdk_timeout) as client:
                    await asyncio.wait_for(client.initialize(), timeout=args.timeout)
                    tools = (await asyncio.wait_for(client.list_tools(), timeout=args.timeout)).tools
                    report["mcp_tools"] = sorted(tool.name for tool in tools)
                    require({"generate_dataset", "validate_dataset"} <= set(report["mcp_tools"]),
                            "mcp_discovery_missing_generation")
                    await execute(client)
    finally:
        if pid_path.is_file():
            try:
                os.kill(int(pid_path.read_text()), 0)
            except ProcessLookupError:
                report["mcp_teardown"] = "process_reaped"
                # A reaped PID must never remain eligible for supervisor cleanup.
                pid_path.unlink()
    require(report.get("mcp_teardown") == "process_reaped", "mcp_process_not_reaped")
    require("source-marker" not in bounded_text(stderr_path), "mcp_stderr_source_disclosure")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--python", type=Path, default=Path(sys.executable))
    result.add_argument("--package-root", type=Path, required=True)
    result.add_argument("--sha", required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--fixture-file", type=Path,
                        default=Path(__file__).resolve().parents[1] / "tests/test_source_output_matrix.py")
    result.add_argument("--timeout", type=float, default=30)
    result.add_argument("--campaign-timeout", type=float, default=1800)
    for name, choices in (("source", SOURCES), ("output-format", OUTPUTS),
                          ("mode", MODES), ("interface", INTERFACES)):
        result.add_argument(f"--{name}", nargs="+", choices=choices, default=list(choices))
    result.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    result.add_argument("--workspace", type=Path, help=argparse.SUPPRESS)
    return result


def main() -> int:
    args = parser().parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.sha):
        raise SystemExit("--sha requires an exact lowercase 40-character commit")
    if not (0 < args.timeout <= 300 and 0 < args.campaign_timeout <= 7200):
        raise SystemExit("timeouts must be positive and bounded")
    args.output = args.output.resolve()
    if args.worker:
        report = json.loads(args.output.read_text())
        try:
            asyncio.run(asyncio.wait_for(run_campaign(args, report),
                                        timeout=max(1.0, args.campaign_timeout - 10)))
            report["worker_complete"] = True
        except BaseException as exc:
            report["campaign_error"] = (str(exc) if type(exc) is AcceptanceFailure
                                        else type(exc).__name__)
        save_report(args.output, report)
        return 0 if (not report.get("campaign_error")
                     and all(case["status"] == "passed" for case in report["cases"])) else 1
    require(not args.output.exists(), "evidence_destination_exists")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": "1.0", "sha": args.sha, "scope": "core_matrix_only",
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "fixture_sha256": hashlib.sha256(args.fixture_file.read_bytes()).hexdigest(),
              "is_full_logical_matrix": all(
                  set(getattr(args, field)) == set(options) for field, options in
                  (("source", SOURCES), ("output_format", OUTPUTS),
                   ("mode", MODES), ("interface", INTERFACES))),
              "cases": ledger(args), "manual_review_evidence": False,
              "live_database_evidence": False}
    save_report(args.output, report)
    with tempfile.TemporaryDirectory(prefix="apa-installed-matrix-") as temporary:
        workspace = Path(temporary).resolve()
        # Resolving a venv's Python symlink selects its base interpreter and
        # silently loses the installed wheel and extras being accepted.
        command = [str(args.python.absolute()), "-I", str(Path(__file__).resolve()),
                   "--worker", "--workspace", str(workspace),
                   "--package-root", str(args.package_root.resolve()), "--sha", args.sha,
                   "--output", str(args.output), "--fixture-file", str(args.fixture_file.resolve()),
                   "--timeout", str(args.timeout), "--campaign-timeout", str(args.campaign_timeout)]
        for field in ("source", "output_format", "mode", "interface"):
            command.extend(["--" + field.replace("_", "-"), *getattr(args, field)])
        timed_out, returncode = supervise(command, workspace, args.campaign_timeout)
        report = json.loads(args.output.read_text())
        if timed_out:
            report["campaign_error"] = "campaign_timeout"
        elif returncode != 0:
            report.setdefault("campaign_error", "worker_exit_failed")
        elif not report.get("worker_complete"):
            report["campaign_error"] = "worker_completion_missing"
        elif "mcp" in args.interface and report.get("mcp_teardown") != "process_reaped":
            report["campaign_error"] = "mcp_teardown_missing"
        save_report(args.output, report)
    report = json.loads(args.output.read_text())
    print(json.dumps({"sha": args.sha, "counts": report["counts"],
                      "scope": report["scope"], "campaign_error": report.get("campaign_error")}))
    return 0 if (not report.get("campaign_error")
                 and all(case["status"] == "passed" for case in report["cases"])) else 1


if __name__ == "__main__":
    raise SystemExit(main())
