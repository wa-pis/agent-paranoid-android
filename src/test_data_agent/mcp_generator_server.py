"""Safe MCP tools for synthetic dataset profiling, generation, and validation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:  # pragma: no cover - exercised when the MCP dependency is installed.
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore[misc, assignment]

from test_data_agent.adapters import load_profile_or_spec
from test_data_agent.adapters.json_profile import json_payload_to_dataset_profile
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import (
    enforce_business_rules_payload_size,
    read_limited_text,
)
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io import (
    GenerationManifest,
    dataset_spec_fingerprint,
    generate_dataset_bundle,
    infer_dataset_spec_artifact,
    load_dataset_spec,
    validate_dataset_artifacts,
    write_csv_profile_artifact,
)
from test_data_agent.io.artifacts import business_validation_manifest
from test_data_agent.rules.business_config import make_business_rules_applier
from test_data_agent.rules.contract import validate_business_rules_for_spec
from test_data_agent.rules.models import (
    BusinessRules,
    business_rules_from_dict,
    load_business_rules,
)
from test_data_agent.rules.validation import BusinessValidationReport
from test_data_agent.safety import assert_profile_safe


WORKSPACE_ROOT_ENV = "TEST_DATA_AGENT_WORKSPACE_ROOT"


class WorkspacePathError(ValueError):
    """Raised when an MCP path escapes the configured workspace root."""


def profile_csv(input_path: str, output_path: str, table_name: str | None = None) -> dict[str, Any]:
    """Create a safe aggregate profile for one workspace CSV file."""

    source = resolve_workspace_path(input_path, must_exist=True, expect_file=True)
    output = resolve_workspace_path(output_path)
    _require_suffix(source, {".csv"}, "input CSV")
    _require_suffix(output, {".json"}, "profile output")
    _require_distinct(source, output)
    _require_new_output(output)

    profile = write_csv_profile_artifact(source, output_path=output, table_name=table_name)
    return {
        "operation": "profile_csv",
        "profile_path": workspace_path_label(output),
        **profile_summary(profile),
    }


def infer_dataset_spec(
    output_path: str,
    profile_path: str | None = None,
    profile_payload: dict[str, Any] | None = None,
    count: int | None = None,
) -> dict[str, Any]:
    """Infer and persist a versioned DatasetSpec from safe profile metadata."""

    output = resolve_workspace_path(output_path)
    _require_suffix(output, {".json", ".yaml", ".yml"}, "spec output")
    _require_new_output(output)
    if (profile_path is None) == (profile_payload is None):
        raise ValueError("provide exactly one of profile_path or profile_payload")
    if profile_path is not None:
        source = resolve_workspace_path(profile_path, must_exist=True, expect_file=True)
        _require_suffix(source, {".json"}, "profile input")
        _require_distinct(source, output)
        loaded = load_profile_or_spec(source)
        if isinstance(loaded, DatasetSpec):
            raise ValueError("infer_dataset_spec expects a dataset profile, not a dataset spec")
    else:
        loaded = json_payload_to_dataset_profile(profile_payload or {})
    assert_profile_safe(loaded)
    spec = infer_dataset_spec_artifact(loaded, output_path=output, count=count)
    return {
        "operation": "infer_dataset_spec",
        "spec_path": workspace_path_label(output),
        **spec_summary(spec),
    }


def generate_dataset(
    spec_path: str,
    output_folder: str,
    output_format: str | None = None,
    seed: int | None = None,
    count: int | None = None,
    business_rules_path: str | None = None,
    business_rules_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate synthetic files and validation artifacts without returning rows."""

    return _generate_dataset(
        operation="generate_dataset",
        spec_path=spec_path,
        output_folder=output_folder,
        output_format=output_format,
        seed=seed,
        count=count,
        business_rules_path=business_rules_path,
        business_rules_payload=business_rules_payload,
    )


def validate_dataset(
    spec_path: str,
    rows_folder: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Validate generated workspace artifacts against a DatasetSpec."""

    spec = resolve_workspace_path(spec_path, must_exist=True, expect_file=True)
    rows = resolve_workspace_path(rows_folder, must_exist=True, expect_directory=True)
    _require_suffix(spec, {".json", ".yaml", ".yml"}, "spec input")
    manifest_path = rows / "generation_manifest.json"
    if not manifest_path.is_file():
        raise WorkspacePathError("rows folder is not a synthetic generation bundle")
    try:
        manifest = GenerationManifest.model_validate_json(read_limited_text(manifest_path))
    except ValueError as exc:
        raise WorkspacePathError("generation manifest is invalid") from exc
    loaded_spec = load_dataset_spec(spec)
    if manifest.spec_sha256 != dataset_spec_fingerprint(loaded_spec):
        raise WorkspacePathError("generation manifest does not match the dataset spec")
    business_report_path = rows / "business_validation_report.json"
    if manifest.business_validation is not None:
        if not business_report_path.is_file():
            raise WorkspacePathError("business validation report is missing")
        try:
            business_report = BusinessValidationReport.model_validate_json(
                read_limited_text(business_report_path)
            )
        except ValueError as exc:
            raise WorkspacePathError("business validation report is invalid") from exc
        if business_validation_manifest(business_report) != manifest.business_validation:
            raise WorkspacePathError(
                "business validation report does not match the generation manifest"
            )
    report_path = None
    if output_path is not None:
        report_path = resolve_workspace_path(output_path)
        _require_suffix(report_path, {".json"}, "validation output")
        _require_new_output(report_path)
    report = validate_dataset_artifacts(spec, rows, output_path=report_path)
    return {
        "operation": "validate_dataset",
        "rows_folder": workspace_path_label(rows),
        "report_path": workspace_path_label(report_path) if report_path is not None else None,
        "validation": report.model_dump(mode="json"),
        "business_validation": (
            manifest.business_validation.model_dump(mode="json")
            if manifest.business_validation is not None
            else None
        ),
        "business_validation_report_path": (
            workspace_path_label(business_report_path)
            if manifest.business_validation is not None
            else None
        ),
    }


def export_dataset(
    spec_path: str,
    output_folder: str,
    output_format: str,
    seed: int | None = None,
    count: int | None = None,
    business_rules_path: str | None = None,
    business_rules_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate and export fresh synthetic data; source-row conversion is not supported."""

    return _generate_dataset(
        operation="export_dataset",
        spec_path=spec_path,
        output_folder=output_folder,
        output_format=output_format,
        seed=seed,
        count=count,
        business_rules_path=business_rules_path,
        business_rules_payload=business_rules_payload,
    )


def resolve_workspace_path(
    raw_path: str,
    *,
    must_exist: bool = False,
    expect_file: bool = False,
    expect_directory: bool = False,
) -> Path:
    if not raw_path or "\x00" in raw_path:
        raise WorkspacePathError("path must be a non-empty workspace path")
    root = workspace_root()
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise WorkspacePathError(f"path escapes {WORKSPACE_ROOT_ENV}")
    if must_exist and not resolved.exists():
        raise WorkspacePathError("workspace input path does not exist")
    if expect_file and resolved.exists() and not resolved.is_file():
        raise WorkspacePathError("workspace input path must be a file")
    if expect_directory and resolved.exists() and not resolved.is_dir():
        raise WorkspacePathError("workspace input path must be a directory")
    return resolved


def workspace_root() -> Path:
    configured = os.environ.get(WORKSPACE_ROOT_ENV)
    root = Path(configured).expanduser() if configured else Path.cwd()
    try:
        resolved = root.resolve(strict=True)
    except FileNotFoundError as exc:
        raise WorkspacePathError(f"{WORKSPACE_ROOT_ENV} does not exist") from exc
    if not resolved.is_dir():
        raise WorkspacePathError(f"{WORKSPACE_ROOT_ENV} must be a directory")
    return resolved


def workspace_path_label(path: Path) -> str:
    return path.relative_to(workspace_root()).as_posix()


def profile_summary(profile: DatasetProfile) -> dict[str, Any]:
    return {
        "source_type": profile.source_type,
        "entity_count": len(profile.entities),
        "entities": [
            {
                "name": entity.name,
                "row_count": entity.row_count,
                "field_count": len(entity.fields),
                "sensitive_field_count": sum(field.sensitive for field in entity.fields),
            }
            for entity in profile.entities
        ],
    }


def spec_summary(spec: DatasetSpec) -> dict[str, Any]:
    return {
        "schema_version": spec.schema_version,
        "entity_count": len(spec.entities),
        "entities": [
            {"name": entity.name, "row_count": entity.row_count, "field_count": len(entity.fields)}
            for entity in spec.entities
        ],
        "relationship_count": len(spec.relationships),
        "constraint_count": len(spec.constraints),
    }


def _generate_dataset(
    *,
    operation: str,
    spec_path: str,
    output_folder: str,
    output_format: str | None,
    seed: int | None,
    count: int | None,
    business_rules_path: str | None,
    business_rules_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    source = resolve_workspace_path(spec_path, must_exist=True, expect_file=True)
    output = resolve_workspace_path(output_folder)
    _require_suffix(source, {".json", ".yaml", ".yml"}, "spec input")
    if output.exists() and not output.is_dir():
        raise WorkspacePathError("generation output must be a folder")
    if output.exists() and any(output.iterdir()):
        raise WorkspacePathError("generation output folder must be empty")
    spec = load_dataset_spec(source)
    business_rules = load_mcp_business_rules(
        business_rules_path,
        business_rules_payload,
        spec,
    )
    selected_format = None if output_format is None else OutputFormat(output_format)
    result = generate_dataset_bundle(
        spec,
        output_folder=output,
        output_format=selected_format,
        seed=seed,
        count=count,
        business_rules_applier=(
            make_business_rules_applier(business_rules)
            if business_rules is not None
            else None
        ),
    )
    business_summary = business_validation_manifest(result.business_validation)
    return {
        "operation": operation,
        "output_folder": workspace_path_label(output),
        "manifest_path": workspace_path_label(output / "generation_manifest.json"),
        "business_validation_report_path": (
            workspace_path_label(output / "business_validation_report.json")
            if business_summary is not None
            else None
        ),
        **result.model_dump(mode="json", exclude={"business_validation"}),
        "business_validation": (
            business_summary.model_dump(mode="json")
            if business_summary is not None
            else None
        ),
    }


def load_mcp_business_rules(
    rules_path: str | None,
    rules_payload: dict[str, Any] | None,
    spec: DatasetSpec,
) -> BusinessRules | None:
    if rules_path is not None and rules_payload is not None:
        raise ValueError(
            "provide at most one of business_rules_path or business_rules_payload"
        )
    if rules_path is None and rules_payload is None:
        return None
    if rules_path is not None:
        source = resolve_workspace_path(
            rules_path,
            must_exist=True,
            expect_file=True,
        )
        _require_suffix(
            source,
            {".json", ".yaml", ".yml"},
            "business rules input",
        )
        rules = load_business_rules(source)
    else:
        try:
            serialized = json.dumps(
                rules_payload,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError, RecursionError) as exc:
            raise ValueError("business rules payload must be JSON-compatible") from exc
        enforce_business_rules_payload_size(len(serialized))
        rules = business_rules_from_dict(rules_payload or {})
    validate_business_rules_for_spec(rules, spec)
    return rules


def _require_suffix(path: Path, allowed: set[str], label: str) -> None:
    if path.suffix.lower() not in allowed:
        expected = ", ".join(sorted(allowed))
        raise WorkspacePathError(f"{label} must use one of: {expected}")


def _require_distinct(first: Path, second: Path) -> None:
    if first == second:
        raise WorkspacePathError("input and output paths must be different")


def _require_new_output(path: Path) -> None:
    if path.exists():
        raise WorkspacePathError("MCP output path already exists")


mcp: Any
if FastMCP is not None:
    mcp = FastMCP("test-data-agent-generator")
    mcp.tool()(profile_csv)
    mcp.tool()(infer_dataset_spec)
    mcp.tool()(generate_dataset)
    mcp.tool()(validate_dataset)
    mcp.tool()(export_dataset)
else:  # pragma: no cover
    mcp = None


def main() -> None:
    if mcp is None:
        raise RuntimeError("mcp package is not installed")
    mcp.run()


if __name__ == "__main__":
    main()
