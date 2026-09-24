"""Private local mapping snapshots; not execution approval or public artifacts."""

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_mapping import MappingDeclarationError
from test_data_agent.io.path_policy import open_regular_file


@dataclass(frozen=True)
class MappingSnapshot:
    payload: bytes = field(repr=False)
    sha256: str = field(repr=False)


def read_mapping_snapshot(
    root: Path, relative_path: str, *, max_bytes: int, budget: GenerationBudget,
) -> MappingSnapshot:
    """Read once below an explicit root; return the exact bytes that were hashed."""
    try:
        budget.check("mapping snapshot")
        if type(max_bytes) is not int or max_bytes < 1 or type(relative_path) is not str:
            raise ValueError
        path = Path(relative_path)
        if not root.is_absolute() or not relative_path or path.is_absolute() or ".." in path.parts:
            raise ValueError
        with open_regular_file(root / path) as handle:
            before = os.fstat(handle.fileno())
            if before.st_size > max_bytes:
                raise ValueError
            chunks: list[bytes] = []
            size = 0
            while True:
                budget.check("mapping snapshot")
                chunk = handle.read(min(65536, max_bytes - size + 1))
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError
                chunks.append(chunk)
            after = os.fstat(handle.fileno())
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns
            ):
                raise ValueError
        payload = b"".join(chunks)
        result = MappingSnapshot(payload, hashlib.sha256(payload).hexdigest())
        budget.check("mapping snapshot")
        return result
    except (OSError, ValueError):
        pass
    try:
        raise MappingDeclarationError("invalid mapping snapshot")
    except MappingDeclarationError as error:
        error.__context__ = None
        raise
