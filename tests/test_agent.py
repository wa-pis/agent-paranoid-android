import csv
import json
from pathlib import Path
from typing import Any

import pytest
import test_data_agent
import test_data_agent.agent as agent_module
import test_data_agent.agent_approval as agent_approval_module
import test_data_agent.agent_review as agent_review_module
from test_data_agent.agent import (
    AgentApprovalReceipt,
    AgentCompletionCheckpoint,
    AgentFieldReference,
    AgentFieldSummary,
    AgentGenerationSummary,
    AgentNextAction,
    AgentPlanSummary,
    AgentRecoverySummary,
    AgentRequest,
    AgentReviewReport,
    AgentReviewState,
    AgentRelationshipSummary,
    AgentSourceType,
    AgentWorkspaceStatus,
    apply_agent_advisor_proposal,
    advise_agent_workspace,
    approve_agent_workspace,
    build_agent_advisor_exchange,
    build_agent_advisor_request,
    detect_agent_source_type,
    inspect_agent_workspace,
    plan_agent_request,
    recover_agent_workspace,
    review_agent_workspace,
)
from test_data_agent.advisor import (
    AdvisorContractError,
    AdvisorExchange,
    AdvisorExchangeClient,
    AdvisorRequest,
    ExchangeDatasetAdvisor,
)
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.artifacts import write_dataset_spec_artifact
from test_data_agent.io.readers import load_dataset_spec


FIXTURE_CUSTOMERS = Path("tests/fixtures/customers.csv")
FIXTURE_EXAMPLE_DATASET = Path("tests/fixtures/example_dataset")


class RowCountAdvisor:
    def __init__(self, row_count: int) -> None:
        self.row_count = row_count
        self.calls = 0

    def propose(self, request: AdvisorRequest) -> dict[str, Any]:
        self.calls += 1
        candidate = request.baseline_spec.model_copy(deep=True)
        candidate.entities[0].row_count = self.row_count
        return {
            "schema_version": "1.0",
            "profile_sha256": request.profile_sha256,
            "baseline_spec_sha256": request.baseline_spec_sha256,
            "approval_required": True,
            "generation_performed": False,
            "dataset_spec": candidate.model_dump(mode="json"),
        }


class RecordingRowCountClient:
    def __init__(self, row_count: int) -> None:
        self.row_count = row_count
        self.exchanges: list[AdvisorExchange] = []

    def complete(self, exchange: AdvisorExchange) -> dict[str, Any]:
        self.exchanges.append(exchange)
        request = exchange.request
        candidate = request.baseline_spec.model_copy(deep=True)
        candidate.entities[0].row_count = self.row_count
        return {
            "schema_version": "1.0",
            "profile_sha256": request.profile_sha256,
            "baseline_spec_sha256": request.baseline_spec_sha256,
            "approval_required": True,
            "generation_performed": False,
            "dataset_spec": candidate.model_dump(mode="json"),
        }


def test_package_root_exposes_agent_api() -> None:
    assert test_data_agent.AgentApprovalReceipt is AgentApprovalReceipt
    assert test_data_agent.AgentCompletionCheckpoint is AgentCompletionCheckpoint
    assert test_data_agent.AgentFieldReference is AgentFieldReference
    assert test_data_agent.AgentFieldSummary is AgentFieldSummary
    assert test_data_agent.AgentRequest is AgentRequest
    assert test_data_agent.AgentReviewReport is AgentReviewReport
    assert test_data_agent.AgentReviewState is AgentReviewState
    assert test_data_agent.AgentRelationshipSummary is AgentRelationshipSummary
    assert test_data_agent.AgentPlanSummary is AgentPlanSummary
    assert test_data_agent.AgentRecoverySummary is AgentRecoverySummary
    assert test_data_agent.AgentGenerationSummary is AgentGenerationSummary
    assert test_data_agent.AgentNextAction is AgentNextAction
    assert test_data_agent.AgentSourceType is AgentSourceType
    assert test_data_agent.AgentWorkspaceStatus is AgentWorkspaceStatus
    assert test_data_agent.apply_agent_advisor_proposal is apply_agent_advisor_proposal
    assert test_data_agent.advise_agent_workspace is advise_agent_workspace
    assert test_data_agent.AdvisorExchange is AdvisorExchange
    assert test_data_agent.AdvisorExchangeClient is AdvisorExchangeClient
    assert test_data_agent.ExchangeDatasetAdvisor is ExchangeDatasetAdvisor
    assert test_data_agent.build_agent_advisor_exchange is build_agent_advisor_exchange
    assert test_data_agent.build_agent_advisor_request is build_agent_advisor_request
    assert test_data_agent.plan_agent_request is plan_agent_request
    assert test_data_agent.approve_agent_workspace is approve_agent_workspace
    assert test_data_agent.detect_agent_source_type is detect_agent_source_type
    assert test_data_agent.inspect_agent_workspace is inspect_agent_workspace
    assert test_data_agent.recover_agent_workspace is recover_agent_workspace
    assert test_data_agent.review_agent_workspace is review_agent_workspace


def test_agent_plan_stops_before_generation_for_csv_folder(tmp_path) -> None:
    workspace = tmp_path / "agent"

    result = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=6,
            seed=12345,
            output_format=OutputFormat.CSV,
        )
    )

    profile_text = (workspace / "profile.json").read_text()
    plan = json.loads((workspace / "agent_plan.json").read_text())
    request = json.loads((workspace / "agent_request.json").read_text())

    assert result.phase == "awaiting_approval"
    assert isinstance(result.summary, AgentPlanSummary)
    assert result.summary.seed == 12345
    assert result.summary.entities[0].field_count > 0
    assert result.summary.entities[0].fields[0].name == "customer_id"
    assert result.summary.metadata_trust == "untrusted"
    assert [(field.entity, field.field) for field in result.summary.sensitive_fields] == [
        ("customers", "email")
    ]
    assert result.summary.relationships[0].confidence == 1.0
    assert result.summary.minimum_inference_confidence is not None
    assert result.summary.assumptions
    assert "untrusted metadata" in result.summary.warnings[0]
    assert result.review is not None
    assert len(result.review.plan_id) == 32
    assert len(result.review.profile_sha256) == 64
    assert result.review.planned_spec_sha256 == result.review.current_spec_sha256
    assert result.review.spec_changed_since_plan is False
    assert (workspace / "dataset_spec.yaml").is_file()
    assert not (workspace / "generated").exists()
    assert "alice@example.com" not in profile_text
    assert plan["approval_required"] is True
    assert plan["steps"][2]["name"] == "approval"
    assert plan["steps"][2]["status"] == "pending"
    assert plan["summary"]["seed"] == 12345
    assert plan["summary"]["output_format"] == "csv"
    assert request["source_type"] == "csv_folder"
    assert request["seed"] == 12345
    assert plan["review"]["plan_id"] == result.review.plan_id


def test_agent_approve_generates_safe_csv_folder_bundle(tmp_path) -> None:
    workspace = tmp_path / "agent"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=5,
            seed=77,
            output_format=OutputFormat.CSV,
        )
    )

    assert planned.review is not None
    result = approve_agent_workspace(
        workspace,
        reviewed_spec_sha256=planned.review.current_spec_sha256,
    )

    manifest = json.loads((workspace / "generated" / "generation_manifest.json").read_text())
    report = json.loads((workspace / "generated" / "validation_report.json").read_text())
    persisted_result = json.loads((workspace / "agent_result.json").read_text())
    receipt = json.loads((workspace / "approval_receipt.json").read_text())
    generated_rows = load_csv_folder(workspace / "generated")
    source_rows = load_csv_folder(FIXTURE_EXAMPLE_DATASET)

    assert result.phase == "completed"
    assert isinstance(result.summary, AgentGenerationSummary)
    assert result.summary.row_counts == {"customers": 5, "orders": 5}
    assert result.summary.validation_valid is True
    assert result.summary["row_counts"] == {"customers": 5, "orders": 5}
    assert persisted_result["summary"]["row_counts"] == {"customers": 5, "orders": 5}
    assert persisted_result["summary"]["output_format"] == "csv"
    assert persisted_result["summary"]["source_rows_copied"] is False
    assert result.approval_receipt is not None
    assert receipt == result.approval_receipt.model_dump(mode="json")
    assert receipt["plan_id"] == planned.review.plan_id
    assert receipt["profile_sha256"] == planned.review.profile_sha256
    assert receipt["reviewed_spec_sha256"] == manifest["spec_sha256"]
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["seed"] == 77
    assert manifest["row_counts"] == {"customers": 5, "orders": 5}
    assert report["valid"] is True
    assert not copied_rows(generated_rows, source_rows)


def test_agent_approve_generates_safe_single_csv_bundle(tmp_path) -> None:
    workspace = tmp_path / "agent_csv"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV,
            source_path=FIXTURE_CUSTOMERS,
            workspace=workspace,
            count=4,
            seed=19,
            output_format=OutputFormat.CSV,
            table_name="customers_agent",
        )
    )

    assert planned.review is not None
    result = approve_agent_workspace(
        workspace,
        reviewed_spec_sha256=planned.review.current_spec_sha256,
    )

    rows = list(csv.DictReader((workspace / "generated" / "customers_agent.csv").open()))
    source_rows = list(csv.DictReader(FIXTURE_CUSTOMERS.open()))
    profile_text = (workspace / "profile.json").read_text()

    assert result.summary["row_counts"] == {"customers_agent": 4}
    assert len(rows) == 4
    assert "alice@example.com" not in profile_text
    assert {tuple(row.items()) for row in rows}.isdisjoint({tuple(row.items()) for row in source_rows})


def test_agent_workspace_status_tracks_plan_and_completion(tmp_path) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
            seed=21,
            output_format=OutputFormat.CSV,
        )
    )

    planned = inspect_agent_workspace(workspace)

    assert planned.schema_version == "1.0"
    assert planned.phase == "awaiting_approval"
    assert planned.next_action == "review_and_approve"
    assert planned.approval_required is True
    assert isinstance(planned.summary, AgentPlanSummary)
    assert planned.artifacts.generated_folder is None
    assert planned.review is not None

    approve_agent_workspace(
        workspace,
        reviewed_spec_sha256=planned.review.current_spec_sha256,
    )
    completed = inspect_agent_workspace(workspace)

    assert completed.phase == "completed"
    assert completed.next_action == "none"
    assert completed.approval_required is False
    assert isinstance(completed.summary, AgentGenerationSummary)
    assert completed.summary.validation_valid is True
    assert completed.artifacts.generated_folder == workspace.resolve() / "generated"
    assert completed.approval_receipt is not None
    assert completed.artifacts.approval_receipt_path == (
        workspace.resolve() / "approval_receipt.json"
    )
    assert completed.artifacts.completion_checkpoint_path == (
        workspace.resolve() / "generated" / "agent_completion.json"
    )


def test_agent_recovery_finishes_publication_without_regenerating_rows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
            seed=91,
        )
    )
    assert planned.review is not None
    original_publish = agent_approval_module.publish_agent_completion

    def interrupt_publication(*args, **kwargs) -> None:
        raise RuntimeError("simulated publication interruption")

    monkeypatch.setattr(
        agent_approval_module,
        "publish_agent_completion",
        interrupt_publication,
    )
    with pytest.raises(RuntimeError, match="simulated publication interruption"):
        approve_agent_workspace(
            workspace,
            reviewed_spec_sha256=planned.review.current_spec_sha256,
        )

    generated_before = generated_bundle_bytes(workspace / "generated")
    status = inspect_agent_workspace(workspace)
    assert status.phase == "recovery_required"
    assert status.next_action == "recover"
    assert isinstance(status.summary, AgentRecoverySummary)
    assert status.summary.reason == "completion_metadata_missing"
    assert status.summary.reviewed_spec_sha256 == planned.review.current_spec_sha256

    monkeypatch.setattr(
        agent_approval_module,
        "publish_agent_completion",
        original_publish,
    )
    recovered = recover_agent_workspace(
        workspace,
        reviewed_spec_sha256=planned.review.current_spec_sha256,
    )

    assert recovered.phase == "completed"
    assert generated_bundle_bytes(workspace / "generated") == generated_before
    assert inspect_agent_workspace(workspace).phase == "completed"


def test_agent_recovery_rejects_tampered_rows_before_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert planned.review is not None
    original_publish = agent_approval_module.publish_agent_completion
    monkeypatch.setattr(
        agent_approval_module,
        "publish_agent_completion",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("interrupted")),
    )
    with pytest.raises(RuntimeError, match="interrupted"):
        approve_agent_workspace(
            workspace,
            reviewed_spec_sha256=planned.review.current_spec_sha256,
        )
    monkeypatch.setattr(
        agent_approval_module,
        "publish_agent_completion",
        original_publish,
    )

    customers_path = workspace / "generated" / "customers.csv"
    customers_path.write_text(customers_path.read_text() + "tampered,row\n")
    with pytest.raises(ValueError, match="inconsistent|validation report"):
        recover_agent_workspace(
            workspace,
            reviewed_spec_sha256=planned.review.current_spec_sha256,
        )

    assert not (workspace / "agent_result.json").exists()
    assert not (workspace / "approval_receipt.json").exists()


def test_agent_approve_is_idempotent_for_matching_completed_plan(tmp_path) -> None:
    workspace = tmp_path / "agent"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert planned.review is not None
    first = approve_agent_workspace(
        workspace,
        reviewed_spec_sha256=planned.review.current_spec_sha256,
    )
    before = generated_bundle_bytes(workspace / "generated")

    repeated = approve_agent_workspace(
        workspace,
        reviewed_spec_sha256=planned.review.current_spec_sha256,
    )

    assert repeated == first
    assert generated_bundle_bytes(workspace / "generated") == before
    with pytest.raises(ValueError, match="does not match"):
        approve_agent_workspace(workspace, reviewed_spec_sha256="0" * 64)


def test_agent_recovery_restores_missing_approval_receipt(tmp_path) -> None:
    workspace = tmp_path / "agent"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert planned.review is not None
    approve_agent_workspace(
        workspace,
        reviewed_spec_sha256=planned.review.current_spec_sha256,
    )
    (workspace / "approval_receipt.json").unlink()

    status = inspect_agent_workspace(workspace)
    assert status.phase == "recovery_required"
    assert isinstance(status.summary, AgentRecoverySummary)
    assert status.summary.reason == "approval_receipt_missing"

    recover_agent_workspace(
        workspace,
        reviewed_spec_sha256=planned.review.current_spec_sha256,
    )
    assert (workspace / "approval_receipt.json").is_file()
    assert inspect_agent_workspace(workspace).phase == "completed"


def test_agent_recovery_preflights_existing_result_before_writing_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert planned.review is not None
    original_publish = agent_approval_module.publish_agent_completion
    monkeypatch.setattr(
        agent_approval_module,
        "publish_agent_completion",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("interrupted")),
    )
    with pytest.raises(RuntimeError, match="interrupted"):
        approve_agent_workspace(
            workspace,
            reviewed_spec_sha256=planned.review.current_spec_sha256,
        )
    monkeypatch.setattr(
        agent_approval_module,
        "publish_agent_completion",
        original_publish,
    )
    (workspace / "agent_result.json").write_text(
        (workspace / "agent_plan.json").read_text()
    )

    with pytest.raises(ValueError, match="agent_result.json"):
        recover_agent_workspace(
            workspace,
            reviewed_spec_sha256=planned.review.current_spec_sha256,
        )

    assert not (workspace / "approval_receipt.json").exists()


def test_agent_status_tracks_reviewed_spec_edits(tmp_path) -> None:
    workspace = tmp_path / "agent"
    result = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert result.review is not None
    initial_sha256 = result.review.current_spec_sha256
    spec_path = workspace / "dataset_spec.yaml"
    spec = load_dataset_spec(spec_path)
    spec.entities[0].row_count = 4
    write_dataset_spec_artifact(spec, spec_path)

    status = inspect_agent_workspace(workspace)

    assert status.review is not None
    assert status.review.current_spec_sha256 != initial_sha256
    assert status.review.spec_changed_since_plan is True
    assert isinstance(status.summary, AgentPlanSummary)
    assert status.summary.entities[0].row_count == 4
    approved = approve_agent_workspace(
        workspace,
        reviewed_spec_sha256=status.review.current_spec_sha256,
    )
    assert approved.approval_receipt is not None
    assert (
        approved.approval_receipt.reviewed_spec_sha256
        == status.review.current_spec_sha256
    )


def test_agent_review_report_is_detailed_metadata_only_and_read_only(
    tmp_path,
) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
            seed=42,
        )
    )
    before = {
        path.name: path.read_bytes()
        for path in workspace.iterdir()
        if path.is_file()
    }

    report = review_agent_workspace(workspace)

    after = {
        path.name: path.read_bytes()
        for path in workspace.iterdir()
        if path.is_file()
    }
    customer_fields = {
        field.name: field
        for field in report.entities[0].fields
    }
    serialized = report.model_dump_json()

    assert isinstance(report, AgentReviewReport)
    assert report.phase == "awaiting_approval"
    assert report.approval_required is True
    assert report.generation_performed is False
    assert report.seed == 42
    assert report.safety.raw_sensitive_values_blocked is True
    assert report.safety.unknown_fields_treated_as_sensitive is True
    assert customer_fields["customer_id"].is_identifier is True
    assert customer_fields["email"].sensitive is True
    assert customer_fields["email"].semantic_type == "email"
    assert customer_fields["email"].distribution_kind == "masked_patterns"
    assert "alice@example.com" not in serialized
    assert "categories" not in serialized
    assert before == after
    assert not (workspace / "generated").exists()


def test_agent_review_rejects_spec_changed_during_report(
    tmp_path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    original_load = agent_review_module.load_dataset_spec
    load_count = 0

    def load_and_edit(path: Path):
        nonlocal load_count
        spec = original_load(path)
        load_count += 1
        if load_count == 1:
            changed = spec.model_copy(deep=True)
            changed.entities[0].row_count = 4
            write_dataset_spec_artifact(changed, path)
        return spec

    monkeypatch.setattr(agent_review_module, "load_dataset_spec", load_and_edit)

    with pytest.raises(ValueError, match="changed during review"):
        review_agent_workspace(workspace)

    assert not (workspace / "generated").exists()


def test_fake_provider_flow_excludes_source_values_and_requires_approval(
    tmp_path,
) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    client = RecordingRowCountClient(4)
    advisor = ExchangeDatasetAdvisor(client)

    status = advise_agent_workspace(workspace, advisor)

    assert len(client.exchanges) == 1
    provider_request = client.exchanges[0].model_dump_json()
    for source_value in (
        "alice@example.com",
        "bob@example.com",
        "carol@example.com",
        "customer request",
        "fraud",
        '"C1"',
        '"O1"',
    ):
        assert source_value not in provider_request
    assert status.phase == "awaiting_approval"
    assert status.review is not None
    assert status.review.spec_changed_since_plan is True
    assert isinstance(status.summary, AgentPlanSummary)
    assert status.summary.entities[0].row_count == 4
    assert (workspace / "advisor_review.json").is_file()
    assert "alice@example.com" not in (workspace / "advisor_review.json").read_text()
    assert not (workspace / "generated").exists()

    completed = approve_agent_workspace(
        workspace,
        reviewed_spec_sha256=status.review.current_spec_sha256,
    )
    assert completed.phase == "completed"
    assert completed.approval_receipt is not None
    assert (
        completed.approval_receipt.reviewed_spec_sha256
        == status.review.current_spec_sha256
    )


def test_external_advisor_request_is_safe_and_read_only(tmp_path) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    spec_before = (workspace / "dataset_spec.yaml").read_bytes()

    request = build_agent_advisor_request(workspace)

    assert request.approval_required is True
    assert request.metadata_trust == "untrusted"
    assert "alice@example.com" not in request.model_dump_json()
    assert (workspace / "dataset_spec.yaml").read_bytes() == spec_before
    assert not (workspace / "advisor_review.json").exists()
    assert not (workspace / "generated").exists()


def test_external_advisor_proposal_is_applied_once_and_stops_for_review(
    tmp_path,
) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    request = build_agent_advisor_request(workspace)
    proposal = RowCountAdvisor(4).propose(request)

    status = apply_agent_advisor_proposal(workspace, proposal)
    repeated = apply_agent_advisor_proposal(workspace, proposal)

    assert status.phase == "awaiting_approval"
    assert repeated == status
    assert status.review is not None
    assert load_dataset_spec(workspace / "dataset_spec.yaml").entities[0].row_count == 4
    assert (workspace / "advisor_review.json").is_file()
    assert not (workspace / "generated").exists()

    different_proposal = RowCountAdvisor(5).propose(request)
    with pytest.raises(ValueError, match="different advisor proposal"):
        apply_agent_advisor_proposal(workspace, different_proposal)
    assert load_dataset_spec(workspace / "dataset_spec.yaml").entities[0].row_count == 4


def test_external_advisor_proposal_rejects_stale_request(tmp_path) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    request = build_agent_advisor_request(workspace)
    proposal = RowCountAdvisor(4).propose(request)
    spec_path = workspace / "dataset_spec.yaml"
    edited = load_dataset_spec(spec_path)
    edited.entities[0].row_count = 5
    write_dataset_spec_artifact(edited, spec_path)

    with pytest.raises(AdvisorContractError, match="baseline spec fingerprint"):
        apply_agent_advisor_proposal(workspace, proposal)

    assert not (workspace / "advisor_review.json").exists()
    assert load_dataset_spec(spec_path).entities[0].row_count == 5


def test_external_advisor_proposal_resumes_after_interrupted_spec_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    request = build_agent_advisor_request(workspace)
    proposal = RowCountAdvisor(4).propose(request)
    original_write = agent_module.write_dataset_spec_artifact_atomic
    monkeypatch.setattr(
        agent_module,
        "write_dataset_spec_artifact_atomic",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("interrupted")
        ),
    )

    with pytest.raises(RuntimeError, match="interrupted"):
        apply_agent_advisor_proposal(workspace, proposal)

    assert (workspace / "advisor_review.json").is_file()
    assert load_dataset_spec(workspace / "dataset_spec.yaml").entities[0].row_count == 3

    monkeypatch.setattr(
        agent_module,
        "write_dataset_spec_artifact_atomic",
        original_write,
    )
    status = apply_agent_advisor_proposal(workspace, proposal)

    assert status.review is not None
    assert load_dataset_spec(workspace / "dataset_spec.yaml").entities[0].row_count == 4
    assert not (workspace / "generated").exists()


def test_advisor_workspace_handoff_recovers_without_recalling_provider(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    advisor = RowCountAdvisor(4)
    original_write = agent_module.write_dataset_spec_artifact_atomic
    monkeypatch.setattr(
        agent_module,
        "write_dataset_spec_artifact_atomic",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("interrupted")
        ),
    )

    with pytest.raises(RuntimeError, match="interrupted"):
        advise_agent_workspace(workspace, advisor)

    assert advisor.calls == 1
    assert (workspace / "advisor_review.json").is_file()
    assert load_dataset_spec(workspace / "dataset_spec.yaml").entities[0].row_count == 3

    class UnexpectedAdvisor:
        def propose(self, request: AdvisorRequest) -> dict[str, Any]:
            raise AssertionError("persisted advisor review must be reused")

    monkeypatch.setattr(
        agent_module,
        "write_dataset_spec_artifact_atomic",
        original_write,
    )
    status = advise_agent_workspace(workspace, UnexpectedAdvisor())

    assert status.review is not None
    assert status.review.spec_changed_since_plan is True
    assert load_dataset_spec(workspace / "dataset_spec.yaml").entities[0].row_count == 4


def test_advisor_workspace_rejects_unsafe_proposal_without_changes(tmp_path) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    spec_before = (workspace / "dataset_spec.yaml").read_bytes()

    class UnsafeAdvisor:
        def propose(self, request: AdvisorRequest) -> dict[str, Any]:
            candidate = request.baseline_spec.model_copy(deep=True)
            candidate.entity("customers").field("email").sensitive = False
            return {
                "schema_version": "1.0",
                "profile_sha256": request.profile_sha256,
                "baseline_spec_sha256": request.baseline_spec_sha256,
                "approval_required": True,
                "generation_performed": False,
                "dataset_spec": candidate.model_dump(mode="json"),
            }

    with pytest.raises(AdvisorContractError, match="sensitive field"):
        advise_agent_workspace(workspace, UnsafeAdvisor())

    assert not (workspace / "advisor_review.json").exists()
    assert (workspace / "dataset_spec.yaml").read_bytes() == spec_before


def test_advisor_workspace_rejects_spec_changed_after_proposal(tmp_path) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    advise_agent_workspace(workspace, RowCountAdvisor(4))
    spec_path = workspace / "dataset_spec.yaml"
    spec = load_dataset_spec(spec_path)
    spec.entities[0].row_count = 5
    write_dataset_spec_artifact(spec, spec_path)

    with pytest.raises(ValueError, match="changed after advisor review"):
        advise_agent_workspace(workspace, RowCountAdvisor(6))

    assert load_dataset_spec(spec_path).entities[0].row_count == 5


def test_advisor_workspace_does_not_overwrite_edit_during_provider_call(
    tmp_path,
) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    spec_path = workspace / "dataset_spec.yaml"

    class EditingAdvisor(RowCountAdvisor):
        def propose(self, request: AdvisorRequest) -> dict[str, Any]:
            payload = super().propose(request)
            edited = load_dataset_spec(spec_path)
            edited.entities[0].row_count = 5
            write_dataset_spec_artifact(edited, spec_path)
            return payload

    with pytest.raises(ValueError, match="changed after advisor review"):
        advise_agent_workspace(workspace, EditingAdvisor(4))

    assert load_dataset_spec(spec_path).entities[0].row_count == 5


def test_advisor_workspace_rejects_completed_run(tmp_path) -> None:
    workspace = tmp_path / "agent"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert planned.review is not None
    approve_agent_workspace(
        workspace,
        reviewed_spec_sha256=planned.review.current_spec_sha256,
    )

    with pytest.raises(ValueError, match="awaiting-approval"):
        advise_agent_workspace(workspace, RowCountAdvisor(4))


def test_agent_approval_rejects_spec_changed_after_review(tmp_path) -> None:
    workspace = tmp_path / "agent"
    result = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert result.review is not None
    reviewed_sha256 = result.review.current_spec_sha256
    spec_path = workspace / "dataset_spec.yaml"
    spec = load_dataset_spec(spec_path)
    spec.entities[0].row_count = 4
    write_dataset_spec_artifact(spec, spec_path)

    with pytest.raises(ValueError, match="reviewed DatasetSpec fingerprint mismatch"):
        approve_agent_workspace(
            workspace,
            reviewed_spec_sha256=reviewed_sha256,
        )

    assert not (workspace / "generated").exists()
    assert not (workspace / "approval_receipt.json").exists()


def test_agent_approval_rejects_profile_tampering(tmp_path) -> None:
    workspace = tmp_path / "agent"
    result = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert result.review is not None
    profile_path = workspace / "profile.json"
    profile = json.loads(profile_path.read_text())
    profile["entities"][0]["row_count"] += 1
    profile_path.write_text(json.dumps(profile))

    with pytest.raises(ValueError, match="profile.json fingerprint"):
        approve_agent_workspace(
            workspace,
            reviewed_spec_sha256=result.review.current_spec_sha256,
        )

    assert not (workspace / "generated").exists()


def test_agent_approval_rejects_legacy_plan_without_review_state(tmp_path) -> None:
    workspace = tmp_path / "agent"
    result = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert result.review is not None
    plan_path = workspace / "agent_plan.json"
    plan = json.loads(plan_path.read_text())
    plan.pop("review")
    plan_path.write_text(json.dumps(plan))

    with pytest.raises(ValueError, match="create a new plan"):
        approve_agent_workspace(
            workspace,
            reviewed_spec_sha256=result.review.current_spec_sha256,
        )


def test_agent_approval_rejects_receipt_symlink(tmp_path) -> None:
    workspace = tmp_path / "agent"
    result = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_EXAMPLE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert result.review is not None
    target = tmp_path / "outside.json"
    target.write_text("unchanged")
    (workspace / "approval_receipt.json").symlink_to(target)

    with pytest.raises(ValueError, match="approval output already exists"):
        approve_agent_workspace(
            workspace,
            reviewed_spec_sha256=result.review.current_spec_sha256,
        )

    assert target.read_text() == "unchanged"
    assert not (workspace / "generated").exists()


def test_agent_workspace_status_rejects_incomplete_workspace(tmp_path) -> None:
    workspace = tmp_path / "agent"
    workspace.mkdir()
    (workspace / "agent_request.json").write_text("{}")

    try:
        inspect_agent_workspace(workspace)
    except ValueError as exc:
        assert "agent workspace is incomplete" in str(exc)
        assert "profile.json" in str(exc)
    else:
        raise AssertionError("incomplete workspace must be rejected")


def test_detect_agent_source_type_for_supported_inputs(tmp_path) -> None:
    assert detect_agent_source_type(FIXTURE_CUSTOMERS) == AgentSourceType.CSV
    assert detect_agent_source_type(FIXTURE_EXAMPLE_DATASET) == AgentSourceType.CSV_FOLDER
    assert detect_agent_source_type(Path("examples/orders_profile.json")) == AgentSourceType.PROFILE

    empty_folder = tmp_path / "empty"
    empty_folder.mkdir()
    try:
        detect_agent_source_type(empty_folder)
    except ValueError as exc:
        assert "folder contains no CSV files" in str(exc)
    else:
        raise AssertionError("an empty folder must not be detected as a CSV source")


def test_detect_agent_source_type_routes_dataset_spec_to_generate(tmp_path) -> None:
    spec_path = tmp_path / "dataset_spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "entities": [],
            }
        )
    )

    try:
        detect_agent_source_type(spec_path)
    except ValueError as exc:
        assert "detected a DatasetSpec" in str(exc)
        assert "test-data-agent generate" in str(exc)
    else:
        raise AssertionError("DatasetSpec must not be treated as a safe profile")


def test_agent_plan_summary_keeps_older_persisted_shape_readable() -> None:
    summary = AgentPlanSummary.model_validate(
        {
            "source_type": "csv",
            "entities": [
                {
                    "name": "customers",
                    "row_count": 3,
                    "field_count": 2,
                }
            ],
            "relationship_count": 0,
            "constraint_count": 0,
            "seed": 7,
            "output_format": "csv",
        }
    )

    assert summary.entities[0].fields == []
    assert summary.sensitive_fields == []
    assert summary.relationships == []
    assert summary.metadata_trust == "untrusted"


def load_csv_folder(folder: Path) -> dict[str, list[dict[str, str]]]:
    rows = {}
    for path in folder.glob("*.csv"):
        with path.open(newline="") as handle:
            rows[path.stem] = list(csv.DictReader(handle))
    return rows


def copied_rows(generated: dict[str, list[dict[str, str]]], source: dict[str, list[dict[str, str]]]) -> bool:
    for table, rows in generated.items():
        generated_normalized = {tuple(row.items()) for row in rows}
        source_normalized = {tuple(row.items()) for row in source.get(table, [])}
        if generated_normalized & source_normalized:
            return True
    return False


def generated_bundle_bytes(folder: Path) -> dict[str, bytes]:
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }
