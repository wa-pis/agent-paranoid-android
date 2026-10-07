"""Closed instance-owned SQL sessions; metadata only, no approval issuer."""
from contextlib import ExitStack
from dataclasses import dataclass
import json
import math
import secrets
import stat
from pathlib import Path
from threading import RLock, Timer
from time import monotonic
from typing import Literal

from test_data_agent.core.transformation_limits import InputDimension, resolve_input_limit
from test_data_agent.core.transformation_yaml import _load_private_yaml
from test_data_agent.io.path_policy import path_identity, _parent_descriptor, _stat_at
from test_data_agent.io.transformation_batch import TransformationBatch, TransformationBatchError, review_batch, temporary_batch_publication, _publish_retained_test_batch
from test_data_agent.io.transformation_batch_profile import BatchProfile, capture_batch_profile
from test_data_agent.core.transformation_errors import TransformationCleanupError, CLEANUP_INCOMPLETE_MESSAGE
from test_data_agent.io.transformation_query_workflow import _load_configured_query_references, _temporary_configured_query_profile


@dataclass(repr=False)
class _Session:
    owner: ExitStack
    root: Path
    batch: TransformationBatch
    deadline: float
    max_total_bytes: int
    max_review_bytes: int
    max_output_bytes: int
    timer: Timer


class _ConfiguredQuerySessions:
    """One server-owned instance. Close on server shutdown; handles never recapture.

    At most max_active bounded expiry timers are alive. Timers only clean owned
    contexts; active operations share their finite remaining session deadline.
    Cumulative allocation admission is never refunded, even after close/expiry.
    """
    def __init__(self, root: Path, *, max_active: int, max_cumulative_bytes: int,
                 max_seconds: float):
        from test_data_agent.mcp_generator_server import resolve_workspace_path
        if (type(max_active) is not int or not 1 <= max_active <= 32
                or type(max_cumulative_bytes) is not int or not 0 < max_cumulative_bytes <= 2**63 - 1
                or type(max_seconds) not in {int, float} or not math.isfinite(max_seconds)
                or not 0.1 <= max_seconds <= 3600):
            raise TransformationBatchError("invalid SQL session bounds") from None
        self._root = resolve_workspace_path(str(root), must_exist=True, expect_directory=True)
        self._identity = path_identity(self._root)
        self._max_active = max_active
        self._max_cumulative_bytes = max_cumulative_bytes
        self._max_seconds = max_seconds
        self._charged_bytes = 0
        self._sessions: dict[str, _Session] = {}
        self._lock = RLock()
        self._closed = False
        self._cleanup_failed = False

    def close(self) -> None:
        with self._lock:
            self._closed = True
            for handle in tuple(self._sessions):
                try:
                    self._discard(handle)
                except TransformationCleanupError:
                    pass
            self._require_cleanup_health()

    def _require_cleanup_health(self) -> None:
        if self._cleanup_failed:
            raise TransformationCleanupError(CLEANUP_INCOMPLETE_MESSAGE) from None

    def _close_owner(self, owner: ExitStack) -> None:
        try:
            owner.close()
        except Exception:
            self._cleanup_failed = True
            raise TransformationCleanupError(CLEANUP_INCOMPLETE_MESSAGE) from None

    def _discard(self, handle: str) -> None:
        session = self._sessions.pop(handle, None)
        if session is not None:
            session.timer.cancel()
            self._close_owner(session.owner)

    def _expire(self, handle: str) -> None:
        with self._lock:
            try:
                self._discard(handle)
            except TransformationCleanupError:
                pass  # Health latch reports incomplete cleanup on the next owner/request call.

    def _get(self, handle: str) -> _Session:
        self._require_cleanup_health()
        if type(handle) is not str or len(handle) > 64 or self._closed:
            raise TransformationBatchError("SQL session unavailable") from None
        session = self._sessions.get(handle)
        if session is None or monotonic() >= session.deadline:
            self._discard(handle)
            raise TransformationBatchError("SQL session unavailable") from None
        return session

    def open(self, profile_path: str, references_path: str, *, max_total_bytes: int,
             max_review_bytes: int, max_output_bytes: int) -> dict[str, object]:
        from test_data_agent.mcp_transformation_candidate import _mcp_transformation_budget
        import os
        with self._lock:
            self._require_cleanup_health()
            for handle, session in tuple(self._sessions.items()):
                if monotonic() >= session.deadline:
                    self._discard(handle)
            if (self._closed or len(self._sessions) >= self._max_active
                    or type(max_total_bytes) is not int or not 0 < max_total_bytes <= self._max_cumulative_bytes - self._charged_bytes
                    or type(max_review_bytes) is not int or not 0 < max_review_bytes <= max_total_bytes
                    or type(max_output_bytes) is not int or max_output_bytes < 1
                    or path_identity(self._root) != self._identity):
                raise TransformationBatchError("SQL session admission refused") from None
            # Reserve before any database work; failures cannot reset admission.
            self._charged_bytes += max_total_bytes
            owner = ExitStack()
            try:
                with _mcp_transformation_budget() as budget:
                    budget.max_seconds = min(budget.max_seconds, self._max_seconds)
                    deadline = monotonic() + self._max_seconds
                    data = capture_batch_profile(self._root, profile_path,
                        max_total_bytes=max_total_bytes, budget=budget)
                    profile = BatchProfile.model_validate(_load_private_yaml(data, max_total_bytes))
                    resolve_input_limit(InputDimension.OUTPUT_BYTES, profile.resource_limits, os.environ).check(
                        max_output_bytes, requested=True)
                    references = _load_configured_query_references(self._root, references_path,
                        max_bytes=min(max_total_bytes, max_review_bytes), budget=budget)
                    root, batch = owner.enter_context(_temporary_configured_query_profile(
                        self._root, profile, references=references, max_total_bytes=max_total_bytes,
                        max_review_bytes=max_review_bytes, budget=budget))
                    review = review_batch(batch, max_total_bytes=max_total_bytes,
                        max_review_bytes=max_review_bytes, budget=budget)
                    budget.check("SQL session opened")
                handle = secrets.token_urlsafe(32)
                timer = Timer(max(0.001, deadline - monotonic()), self._expire, (handle,))
                timer.daemon = True
                self._sessions[handle] = _Session(owner, root, batch, deadline,
                    max_total_bytes, max_review_bytes, max_output_bytes, timer)
                timer.start()
                return {"handle": handle, "snapshot_sha256": batch.snapshot_sha256,
                    "review": json.loads(review), "expires_in_seconds": max(0.0, deadline - monotonic()),
                    "local_approval": {"root": str(root), "profile": "batch.yaml",
                        "receipt": "local-session-receipt.json", "snapshot_sha256": batch.snapshot_sha256,
                        "max_total_input_bytes": max_total_bytes, "max_review_bytes": max_review_bytes,
                        "authority": "local controlling-TTY confirmation only; MCP cannot approve"},
                    "status": "review_only"}
            except BaseException:
                if "handle" in locals():
                    self._discard(handle)
                self._close_owner(owner)
                raise

    def refuse(self, handle: str | None) -> None:
        """Release an admitted handle after adapter argument refusal."""
        with self._lock:
            if type(handle) is str and len(handle) <= 64:
                self._discard(handle)
            self._require_cleanup_health()

    def local_approval_arguments(self, handle: str) -> list[str]:
        """Trusted local server-owner handoff ONLY; never returned by an MCP tool.

        Pass to existing local CLI approve handler in the owning server process.
        It opens controlling /dev/tty itself, never accepts a remote confirmation.
        """
        with self._lock:
            session = self._get(handle)
            return [str(session.root), "batch.yaml", "local-session-receipt.json",
                "--snapshot-sha256", session.batch.snapshot_sha256,
                "--max-total-input-bytes", str(session.max_total_bytes),
                "--max-review-bytes", str(session.max_review_bytes)]

    def consume(self, handle: str, operation: Literal["review", "validate", "execute", "close"],
                *, snapshot_sha256: str | None = None, destination: str | None = None) -> dict[str, object]:
        from test_data_agent.mcp_transformation_candidate import _mcp_transformation_budget
        with self._lock:
            session = self._get(handle)
            try:
                if operation == "close":
                    self._discard(handle)
                    return {"status": "closed"}
                with _mcp_transformation_budget() as budget:
                    budget.max_seconds = min(budget.max_seconds, session.deadline - monotonic())
                    if operation == "review" and destination is None:
                        return {"status": "review_only", "snapshot_sha256": session.batch.snapshot_sha256,
                            "review": json.loads(review_batch(session.batch,
                                max_total_bytes=session.max_total_bytes, max_review_bytes=session.max_review_bytes,
                                budget=budget))}
                    if operation not in {"validate", "execute"} or snapshot_sha256 != session.batch.snapshot_sha256:
                        raise TransformationBatchError("invalid SQL session request") from None
                    receipt = session.root / "local-session-receipt.json"
                    receipt_path = receipt if receipt.exists() or receipt.is_symlink() else None
                    if operation == "validate" and destination is None:
                        with temporary_batch_publication(session.batch, expected_snapshot_sha256=session.batch.snapshot_sha256,
                            max_total_bytes=session.max_total_bytes, max_review_bytes=session.max_review_bytes,
                            max_output_bytes=session.max_output_bytes, budget=budget, receipt_path=receipt_path) as bundle:
                            summary = (bundle / "manifest.json").read_bytes()
                        return {"status": "closed_validation_completed", "summary": json.loads(summary)}
                    if operation != "execute" or type(destination) is not str:
                        raise TransformationBatchError("invalid SQL session destination") from None
                    relative = Path(destination)
                    if (not destination or relative.is_absolute() or len(relative.parts) != 1
                            or relative.name in {".", ".."} or path_identity(self._root) != self._identity
                            or not stat.S_ISDIR(self._identity.mode)):
                        raise TransformationBatchError("invalid SQL session destination") from None
                    with _parent_descriptor(self._root / relative) as (parent, name):
                        if _stat_at(parent, name) is not None:
                            raise TransformationBatchError("SQL session destination must be new") from None
                    summary = _publish_retained_test_batch(session.batch, self._root / relative, expected_snapshot_sha256=session.batch.snapshot_sha256,
                            max_total_bytes=session.max_total_bytes, max_review_bytes=session.max_review_bytes,
                            max_output_bytes=session.max_output_bytes, budget=budget, receipt_path=receipt_path)
                self._discard(handle)
                return {"status": "closed_publication_completed", "summary": json.loads(summary)}
            except BaseException:
                self._discard(handle)
                raise
