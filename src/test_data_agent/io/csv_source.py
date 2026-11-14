"""Bounded CSV input whose digest covers the bytes consumed by the parser."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
import hashlib
import io
import os
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from test_data_agent.core.limits import max_input_file_bytes, max_total_input_bytes
from test_data_agent.io.path_policy import open_regular_file


if TYPE_CHECKING:
    from typing_extensions import Buffer
    from _hashlib import HASH


class CsvSourceBinding:
    def __init__(self, *, max_bytes: int | None = None) -> None:
        self._remaining = min(max_total_input_bytes(), max_bytes or max_total_input_bytes())
        self._digest = hashlib.sha256(b"agent-source-v1\0")

    @contextmanager
    def read(
        self, path: Path, *, check: Callable[[], None] | None = None,
    ) -> Iterator[io.BufferedReader[_DigestReader]]:
        with open_regular_file(path) as source:
            size = os.fstat(source.fileno()).st_size
            if size > min(self._remaining, max_input_file_bytes()):
                raise ValueError("CSV source exceeds input byte budget")
            self._remaining -= size
            name = path.name.encode("utf-8")
            self._digest.update(len(name).to_bytes(8, "big"))
            self._digest.update(name)
            reader = _DigestReader(source, size, check, self._digest)
            with io.BufferedReader(reader) as buffered:
                yield buffered
                if buffered.read(1):
                    raise ValueError("CSV source was not fully consumed")
                self._digest.update(bytes(8))

    def fingerprint(self) -> str:
        return self._digest.hexdigest()


class _DigestReader(io.RawIOBase):
    def __init__(
        self, source: BinaryIO, size: int, check: Callable[[], None] | None, digest: HASH,
    ) -> None:
        self._source = source
        self._remaining = size
        self._check = check
        self._digest = digest
        self._block_remaining = 0

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Buffer) -> int:
        if self._check is not None:
            self._check()
        if not self._remaining:
            if self._source.read(1):
                raise ValueError("CSV source grew during reading")
            return 0
        view = memoryview(buffer)[:self._remaining]
        chunk = self._source.read(len(view))
        if not chunk:
            raise ValueError("CSV source shrank during reading")
        if self._check is not None:
            self._check()
        size = len(chunk)
        view[:size] = chunk
        offset = 0
        while offset < size:
            if not self._block_remaining:
                self._block_remaining = min(1024 * 1024, self._remaining)
                self._digest.update(self._block_remaining.to_bytes(8, "big"))
            length = min(self._block_remaining, size - offset)
            self._digest.update(chunk[offset:offset + length])
            self._block_remaining -= length
            self._remaining -= length
            offset += length
        return size
