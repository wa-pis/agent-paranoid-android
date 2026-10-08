"""Closed exact common TTY receipt; no individual receipt issuance or public API."""
import hmac
import hashlib
import json
import os
from pathlib import Path

from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.transformation_limits import TransformationLimitError
from test_data_agent.io.path_policy import atomic_write_bytes, open_regular_file
from test_data_agent.io.transformation_batch import TransformationBatch, review_batch
from test_data_agent.io.transformation_receipt import LocalReceiptError, _confirm_tty_fd, _owner_only


def issue_batch_receipt(batch: TransformationBatch, path: Path, *, max_total_bytes: int,
                        max_review_bytes: int, budget: GenerationBudget) -> None:
    """Reuse controlling-TTY confirmation; no boolean/caller-FD approval surface."""
    try:
        review = review_batch(batch, max_total_bytes=max_total_bytes,
                             max_review_bytes=max_review_bytes, budget=budget)
        fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY | getattr(os, "O_CLOEXEC", 0))
        try:
            _confirm_tty_fd(fd, review, batch.snapshot_sha256)
        finally:
            os.close(fd)
        budget.check("local batch confirmation receipt")
        atomic_write_bytes(path, json.dumps({"version": 2, "kind": "transformation_batch",
            "snapshot_sha256": batch.snapshot_sha256,
            "review_sha256": hashlib.sha256(review).hexdigest()},
            sort_keys=True, separators=(",", ":")).encode())
        return
    except (GenerationLimitError, TransformationLimitError):
        raise
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    raise LocalReceiptError("local batch confirmation failed") from None


def verify_batch_receipt(batch: TransformationBatch, path: Path, *, max_total_bytes: int,
                         max_review_bytes: int, budget: GenerationBudget) -> None:
    """Exact common snapshot, strict scoped envelope, owner-only regular file."""
    try:
        review = review_batch(batch, max_total_bytes=max_total_bytes,
                     max_review_bytes=max_review_bytes, budget=budget)
        with open_regular_file(path) as handle:
            metadata = os.fstat(handle.fileno())
            if not _owner_only(metadata.st_uid, metadata.st_mode):
                raise ValueError
            payload = handle.read(256)
            if len(payload) >= 256:
                raise ValueError
        receipt = json.loads(payload)
        if (type(receipt) is not dict or set(receipt) != {"version", "kind", "snapshot_sha256", "review_sha256"}
                or type(receipt["version"]) is not int or receipt["version"] != 2
                or receipt["kind"] != "transformation_batch"
                or type(receipt["snapshot_sha256"]) is not str
                or not hmac.compare_digest(receipt["snapshot_sha256"], batch.snapshot_sha256)
                or type(receipt["review_sha256"]) is not str
                or not hmac.compare_digest(receipt["review_sha256"], hashlib.sha256(review).hexdigest())):
            raise ValueError
        budget.check("local batch confirmation receipt")
        return
    except (GenerationLimitError, TransformationLimitError):
        raise
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    raise LocalReceiptError("local batch confirmation failed") from None
