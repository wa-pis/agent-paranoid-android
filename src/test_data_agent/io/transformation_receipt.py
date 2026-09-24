"""Private local confirmation receipt; not a transformation execution path."""

import hmac
import json
import os
import select
import stat
import time
from pathlib import Path

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_approval import ApprovalRequest, prepare_approval_request
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.path_policy import atomic_write_bytes, open_regular_file


class LocalReceiptError(ValueError):
    """Value-free local approval failure."""


def _canonical_request(
    request: ApprovalRequest, *, max_total_bytes: int, max_review_bytes: int, budget: GenerationBudget,
) -> ApprovalRequest:
    if not isinstance(request, ApprovalRequest):
        raise ValueError
    policy = next(part.payload for part in request.parts if part.kind == "policy")
    evidence = next(part.payload for part in request.parts if part.kind == "evidence")
    external = tuple(part for part in request.parts if part.kind not in {"review", "policy", "evidence"})
    canonical = prepare_approval_request(policy, evidence, external,
        max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget)
    if canonical != request:
        raise ValueError
    return canonical


def _write_all(fd: int, payload: bytes) -> None:
    while payload:
        written = os.write(fd, payload)
        if written < 1:
            raise OSError("terminal write failed")
        payload = payload[written:]


def _confirm_tty_fd(fd: int, review: bytes, digest: str) -> None:
    if not os.isatty(fd):
        raise ValueError
    _write_all(fd, b"\nTransformation plan (no source values):\n" + review
               + b"\nSnapshot SHA-256: " + digest.encode("ascii")
               + b"\nType APPROVE to create a local receipt: ")
    deadline = time.monotonic() + 60
    answer = bytearray()
    while len(answer) <= 8:
        ready, _, _ = select.select([fd], [], [], max(0.0, deadline - time.monotonic()))
        if not ready:
            raise ValueError
        byte = os.read(fd, 1)
        if not byte:
            raise ValueError
        answer.extend(byte)
        if byte == b"\n":
            break
    if bytes(answer).rstrip(b"\r\n") != b"APPROVE":
        raise ValueError


def _issue_to_tty_fd(canonical: ApprovalRequest, path: Path, fd: int, budget: GenerationBudget) -> None:
    _confirm_tty_fd(fd, canonical.review, canonical.snapshot_sha256)
    budget.check("local approval receipt")
    payload = json.dumps({"version": 1, "snapshot_sha256": canonical.snapshot_sha256},
                         sort_keys=True, separators=(",", ":")).encode("ascii")
    atomic_write_bytes(path, payload)


def issue_local_receipt(
    request: ApprovalRequest, path: Path, *, max_total_bytes: int,
    max_review_bytes: int, budget: GenerationBudget,
) -> None:
    """Prompt on controlling TTY; atomically write owner-only digest receipt."""
    try:
        canonical = _canonical_request(request, max_total_bytes=max_total_bytes,
                                       max_review_bytes=max_review_bytes, budget=budget)
        flags = os.O_RDWR | os.O_NOCTTY
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        fd = os.open("/dev/tty", flags)
        try:
            _issue_to_tty_fd(canonical, path, fd, budget)
        finally:
            os.close(fd)
        return
    except (OSError, ValueError, StopIteration, AttributeError, TypeError):
        pass
    try:
        raise LocalReceiptError("local transformation approval failed")
    except LocalReceiptError as error:
        error.__context__ = None
        raise


def verify_local_receipt(
    request: ApprovalRequest, path: Path, *, max_total_bytes: int,
    max_review_bytes: int, budget: GenerationBudget,
) -> tuple[SnapshotPart, ...]:
    """Return the same approved byte snapshots; never reopen source paths."""
    try:
        canonical = _canonical_request(request, max_total_bytes=max_total_bytes,
                                       max_review_bytes=max_review_bytes, budget=budget)
        with open_regular_file(path) as handle:
            metadata = os.fstat(handle.fileno())
            if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
                raise ValueError
            payload = handle.read(256)
            if len(payload) >= 256:
                raise ValueError
        receipt = json.loads(payload)
        if (type(receipt) is not dict or set(receipt) != {"version", "snapshot_sha256"}
                or type(receipt["version"]) is not int or receipt["version"] != 1
                or type(receipt["snapshot_sha256"]) is not str
                or not hmac.compare_digest(receipt["snapshot_sha256"], canonical.snapshot_sha256)):
            raise ValueError
        budget.check("local approval receipt")
        return canonical.parts
    except (OSError, ValueError, StopIteration, AttributeError, TypeError):
        pass
    try:
        raise LocalReceiptError("local transformation approval failed")
    except LocalReceiptError as error:
        error.__context__ = None
        raise
