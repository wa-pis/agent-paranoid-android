"""Closed shared workflow candidate; not CLI/MCP registration or approval."""

from pathlib import Path
from typing import Literal
import json

from pydantic import BaseModel, ConfigDict, Field

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.io.transformation_batch import TransformationBatchError, review_batch, temporary_batch_publication, _publish_retained_test_batch
from test_data_agent.io.transformation_batch_profile import load_batch_profile


class BatchWorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    operation: Literal["review", "validate", "execute"]
    root: Path = Field(repr=False)
    profile: str = Field(repr=False)
    max_total_bytes: int = Field(gt=0)
    max_review_bytes: int = Field(gt=0)
    max_output_bytes: int = Field(gt=0)
    snapshot_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    receipt: str | None = Field(default=None, repr=False)
    destination: str | None = Field(default=None, repr=False)


class BatchWorkflowResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    operation: Literal["review", "validate", "execute"]
    status: Literal["review_only", "closed_validation_completed", "closed_execution_completed", "closed_publication_completed"]
    snapshot_sha256: str
    review_json: bytes | None = Field(default=None, repr=False)
    summary_json: bytes | None = Field(default=None, repr=False)

    def metadata(self) -> dict[str, object]:
        payload = self.model_dump(mode="json", exclude_none=True)
        for field, name in (("review_json", "review"), ("summary_json", "summary")):
            if field in payload:
                payload[name] = json.loads(payload.pop(field))
        return payload


def run_batch_workflow(request: BatchWorkflowRequest, *, budget: GenerationBudget) -> BatchWorkflowResult:
    """Value-free common consumer; validation/execution use owned temporary output."""
    validated: BatchWorkflowRequest | None = None
    try:
        validated = BatchWorkflowRequest.model_validate(request.model_dump(warnings=False))
    except (ValueError, TypeError, AttributeError):
        pass
    if validated is None:
        raise TransformationBatchError("invalid common workflow request") from None
    request = validated
    destination: Path | None = None
    if request.destination is not None:
        relative = Path(request.destination)
        if (request.operation != "execute" or len(relative.parts) != 1
                or relative.is_absolute() or relative.name in {".", ".."}):
            raise TransformationBatchError("invalid common workflow destination") from None
        destination = request.root / relative
        if destination.exists() or destination.is_symlink():
            raise TransformationBatchError("common workflow destination must be new") from None
    receipt: Path | None = None
    if request.receipt is not None:
        relative = Path(request.receipt)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts or request.operation == "review":
            raise TransformationBatchError("invalid common workflow receipt reference") from None
        receipt = request.root / relative
    batch = load_batch_profile(request.root, request.profile,
        max_total_bytes=request.max_total_bytes, max_review_bytes=request.max_review_bytes, budget=budget)
    if request.snapshot_sha256 is not None and request.snapshot_sha256 != batch.snapshot_sha256:
        raise TransformationBatchError("common workflow snapshot changed") from None
    if request.operation == "review":
        return BatchWorkflowResult(operation="review", status="review_only",
            snapshot_sha256=batch.snapshot_sha256,
            review_json=review_batch(batch, max_total_bytes=request.max_total_bytes,
                max_review_bytes=request.max_review_bytes, budget=budget))
    if request.snapshot_sha256 is None:
        raise TransformationBatchError("common workflow requires reviewed snapshot") from None
    if destination is not None:
        summary = _publish_retained_test_batch(batch, destination,
            expected_snapshot_sha256=request.snapshot_sha256,
            max_total_bytes=request.max_total_bytes, max_review_bytes=request.max_review_bytes,
            max_output_bytes=request.max_output_bytes, budget=budget, receipt_path=receipt)
        return BatchWorkflowResult(operation="execute", status="closed_publication_completed",
            snapshot_sha256=batch.snapshot_sha256, summary_json=summary)
    with temporary_batch_publication(batch, expected_snapshot_sha256=request.snapshot_sha256,
            max_total_bytes=request.max_total_bytes, max_review_bytes=request.max_review_bytes,
            max_output_bytes=request.max_output_bytes, budget=budget, receipt_path=receipt) as bundle:
        summary = (bundle / "manifest.json").read_bytes()
    return BatchWorkflowResult(operation=request.operation,
        status="closed_validation_completed" if request.operation == "validate" else "closed_execution_completed",
        snapshot_sha256=batch.snapshot_sha256, summary_json=summary)
