"""Safe agent orchestration over deterministic dataset workflows."""

from __future__ import annotations

import shutil
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from test_data_agent.adapters import csv_file_to_dataset_profile, load_profile_or_spec
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import enforce_output_folder_size, read_limited_text
from test_data_agent.core.settings import GenerationMode, OutputFormat
from test_data_agent.generation import infer_dataset_spec
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.io.artifacts import (
    write_dataset_profile_artifact,
    write_dataset_review_artifacts,
    write_dataset_spec_artifact,
    write_generation_manifest,
    write_json_artifact,
)
from test_data_agent.io.readers import load_dataset_spec
from test_data_agent.io.workflows import (
    apply_dataset_mode_options,
    commit_temp_output_folder,
    enforce_generation_row_count_limits,
    ensure_empty_output_folder,
    make_temp_output_folder,
    prepare_generation_budget,
)
from test_data_agent.io.writers import write_dataset_rows
from test_data_agent.profiling import profile_example_folder
from test_data_agent.safety import (
    assert_no_csv_folder_source_rows,
    assert_no_csv_source_rows,
    assert_profile_safe,
)
from test_data_agent.validation import validate_dataset


AGENT_REQUEST_FILE = "agent_request.json"
AGENT_PLAN_FILE = "agent_plan.json"
AGENT_RESULT_FILE = "agent_result.json"
PROFILE_FILE = "profile.json"
DATASET_SPEC_FILE = "dataset_spec.yaml"
GENERATED_FOLDER = "generated"


class AgentSourceType(StrEnum):
    CSV = "csv"
    CSV_FOLDER = "csv_folder"
    PROFILE = "profile"


class AgentPhase(StrEnum):
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"


class AgentRequest(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    source_type: AgentSourceType
    source_path: Path
    workspace: Path
    count: int = Field(default=100, ge=1)
    seed: int = Field(default=12345, ge=0)
    output_format: OutputFormat = OutputFormat.CSV
    mode: GenerationMode = GenerationMode.VALID
    invalid_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    table_name: str | None = None
    rule_sample_rows: int = Field(default=50_000, ge=1)
    use_cache: bool = False


class AgentStep(BaseModel):
    name: str
    status: Literal["completed", "pending", "skipped"]
    summary: str


class AgentArtifacts(BaseModel):
    workspace: Path
    request_path: Path
    profile_path: Path
    dataset_spec_path: Path
    plan_path: Path
    generated_folder: Path | None = None
    validation_report_path: Path | None = None
    manifest_path: Path | None = None


class AgentResult(BaseModel):
    phase: AgentPhase
    approval_required: bool
    steps: list[AgentStep]
    artifacts: AgentArtifacts
    summary: dict[str, Any] = Field(default_factory=dict)


def plan_agent_request(request: AgentRequest) -> AgentResult:
    normalized = normalize_agent_request(request)
    ensure_agent_workspace_for_plan(normalized)

    profile = build_agent_profile(normalized)
    spec = build_agent_spec(profile, normalized)
    artifacts = agent_artifacts(normalized.workspace)

    write_json_artifact(normalized, artifacts.request_path)
    write_dataset_profile_artifact(profile, artifacts.profile_path)
    write_dataset_spec_artifact(spec, artifacts.dataset_spec_path)

    result = AgentResult(
        phase=AgentPhase.AWAITING_APPROVAL,
        approval_required=True,
        steps=[
            AgentStep(name="profile", status="completed", summary="Safe profile metadata written."),
            AgentStep(name="infer_spec", status="completed", summary="Reviewable DatasetSpec written."),
            AgentStep(name="approval", status="pending", summary="Review dataset_spec.yaml before generation."),
            AgentStep(name="generate", status="skipped", summary="Generation waits for agent-approve."),
        ],
        artifacts=artifacts,
        summary={
            "source_type": normalized.source_type.value,
            "entities": entity_summary(spec),
            "relationship_count": len(spec.relationships),
            "constraint_count": len(spec.constraints),
            "seed": normalized.seed,
            "output_format": normalized.output_format.value,
        },
    )
    write_json_artifact(result, artifacts.plan_path)
    return result


def approve_agent_workspace(workspace: Path) -> AgentResult:
    resolved_workspace = workspace.expanduser().resolve(strict=True)
    artifacts = agent_artifacts(resolved_workspace)
    if not artifacts.request_path.is_file():
        raise ValueError("agent workspace does not contain agent_request.json")
    if not artifacts.profile_path.is_file():
        raise ValueError("agent workspace does not contain profile.json")
    if not artifacts.dataset_spec_path.is_file():
        raise ValueError("agent workspace does not contain dataset_spec.yaml")

    request = AgentRequest.model_validate_json(read_limited_text(artifacts.request_path))
    request = normalize_agent_request(request.model_copy(update={"workspace": resolved_workspace}))
    profile = DatasetProfile.model_validate_json(read_limited_text(artifacts.profile_path))
    assert_profile_safe(profile)
    spec = load_dataset_spec(artifacts.dataset_spec_path)
    prepare_spec_for_approval(spec, request)

    generated_folder = resolved_workspace / GENERATED_FOLDER
    ensure_empty_output_folder(generated_folder)
    row_counts, validation_valid = generate_agent_dataset(
        request,
        profile,
        spec,
        output_folder=generated_folder,
    )

    completed_artifacts = agent_artifacts(resolved_workspace, generated_folder=generated_folder)
    result = AgentResult(
        phase=AgentPhase.COMPLETED,
        approval_required=False,
        steps=[
            AgentStep(name="profile", status="completed", summary="Safe profile metadata loaded."),
            AgentStep(name="infer_spec", status="completed", summary="Reviewed DatasetSpec loaded."),
            AgentStep(name="approval", status="completed", summary="Approval gate passed."),
            AgentStep(name="generate", status="completed", summary="Synthetic dataset bundle written."),
            AgentStep(name="validate", status="completed", summary="Validation report written."),
        ],
        artifacts=completed_artifacts,
        summary={
            "source_type": request.source_type.value,
            "row_counts": row_counts,
            "seed": request.seed,
            "output_format": request.output_format.value,
            "validation_valid": validation_valid,
            "synthetic": True,
            "source_rows_copied": False,
        },
    )
    write_json_artifact(result, resolved_workspace / AGENT_RESULT_FILE)
    return result


def normalize_agent_request(request: AgentRequest) -> AgentRequest:
    source = request.source_path.expanduser().resolve(strict=True)
    workspace = request.workspace.expanduser().resolve(strict=False)
    if request.source_type == AgentSourceType.CSV and not source.is_file():
        raise ValueError("csv source must be a file")
    if request.source_type == AgentSourceType.CSV and source.suffix.lower() != ".csv":
        raise ValueError("csv source must have .csv suffix")
    if request.source_type == AgentSourceType.CSV_FOLDER and not source.is_dir():
        raise ValueError("csv_folder source must be a directory")
    if request.source_type == AgentSourceType.CSV_FOLDER and workspace.is_relative_to(source):
        raise ValueError("agent workspace must not be inside the source CSV folder")
    if request.source_type == AgentSourceType.PROFILE and not source.is_file():
        raise ValueError("profile source must be a file")
    if request.source_type == AgentSourceType.PROFILE and source.suffix.lower() != ".json":
        raise ValueError("profile source must have .json suffix")
    return request.model_copy(update={"source_path": source, "workspace": workspace})


def ensure_agent_workspace_for_plan(request: AgentRequest) -> None:
    workspace = request.workspace
    if workspace.exists() and not workspace.is_dir():
        raise ValueError("agent workspace must be a folder")
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError("agent workspace must be empty for planning")
    workspace.mkdir(parents=True, exist_ok=True)


def build_agent_profile(request: AgentRequest) -> DatasetProfile:
    if request.source_type == AgentSourceType.CSV:
        profile = csv_file_to_dataset_profile(request.source_path, table_name=request.table_name)
    elif request.source_type == AgentSourceType.CSV_FOLDER:
        profile = profile_example_folder(
            request.source_path,
            cache_dir=request.workspace / "profile_cache" if request.use_cache else None,
            use_cache=request.use_cache,
            rule_sample_rows=request.rule_sample_rows,
        )
    else:
        loaded = load_profile_or_spec(request.source_path)
        if isinstance(loaded, DatasetSpec):
            raise ValueError("agent profile source expects a dataset profile, not a dataset spec")
        profile = loaded
    assert_profile_safe(profile)
    return profile


def build_agent_spec(profile: DatasetProfile, request: AgentRequest) -> DatasetSpec:
    spec = infer_dataset_spec(profile, count=request.count)
    prepare_spec_for_approval(spec, request)
    return spec


def prepare_spec_for_approval(spec: DatasetSpec, request: AgentRequest) -> None:
    spec.generation_settings.seed = request.seed
    spec.generation_settings.output_format = request.output_format
    apply_dataset_mode_options(
        spec,
        mode=request.mode.value,
        invalid_ratio=request.invalid_ratio,
    )
    enforce_generation_row_count_limits(spec)


def generate_agent_dataset(
    request: AgentRequest,
    profile: DatasetProfile,
    spec: DatasetSpec,
    *,
    output_folder: Path,
) -> tuple[dict[str, int], bool]:
    budget = prepare_generation_budget(spec, output_folder)
    temp_folder = make_temp_output_folder(output_folder)
    try:
        rows_by_entity = generate_dataset(spec, seed=request.seed, budget=budget)
        budget.check("dataset generation")
        assert_agent_source_not_copied(request, spec, rows_by_entity)
        write_dataset_rows(rows_by_entity, request.output_format, temp_folder)
        budget.check("dataset export")
        report = validate_dataset(rows_by_entity, spec)
        budget.check("dataset validation")
        write_dataset_review_artifacts(profile, spec, report, temp_folder)
        row_counts = {name: len(rows) for name, rows in rows_by_entity.items()}
        write_generation_manifest(
            spec,
            seed=request.seed,
            output_format=request.output_format,
            row_counts=row_counts,
            validation_valid=report.valid,
            output_folder=temp_folder,
        )
        enforce_output_folder_size(temp_folder)
        budget.check("artifact publication")
        commit_temp_output_folder(temp_folder, output_folder)
    except Exception:
        shutil.rmtree(temp_folder, ignore_errors=True)
        raise
    return row_counts, report.valid


def assert_agent_source_not_copied(
    request: AgentRequest,
    spec: DatasetSpec,
    rows_by_entity: dict[str, list[dict[str, Any]]],
) -> None:
    if request.source_type == AgentSourceType.CSV:
        if len(spec.entities) != 1:
            raise ValueError("csv agent source expects exactly one generated entity")
        entity_name = spec.entities[0].name
        assert_no_csv_source_rows(request.source_path, rows_by_entity[entity_name])
    elif request.source_type == AgentSourceType.CSV_FOLDER:
        assert_no_csv_folder_source_rows(request.source_path, rows_by_entity)


def agent_artifacts(workspace: Path, *, generated_folder: Path | None = None) -> AgentArtifacts:
    return AgentArtifacts(
        workspace=workspace,
        request_path=workspace / AGENT_REQUEST_FILE,
        profile_path=workspace / PROFILE_FILE,
        dataset_spec_path=workspace / DATASET_SPEC_FILE,
        plan_path=workspace / AGENT_PLAN_FILE,
        generated_folder=generated_folder,
        validation_report_path=generated_folder / "validation_report.json" if generated_folder else None,
        manifest_path=generated_folder / "generation_manifest.json" if generated_folder else None,
    )


def entity_summary(spec: DatasetSpec) -> list[dict[str, Any]]:
    return [
        {
            "name": entity.name,
            "row_count": entity.row_count,
            "field_count": len(entity.fields),
        }
        for entity in spec.entities
    ]
