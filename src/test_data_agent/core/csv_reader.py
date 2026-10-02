"""Per-reader CSV limits, coordinated around the stdlib's process-wide setting."""

import csv
from collections.abc import Callable, Iterable, Iterator
from threading import RLock
from typing import Any, TYPE_CHECKING, cast

from test_data_agent.core.limits import max_input_cell_chars

_parser_lock = RLock()


class ScopedCSVReader(Iterator[list[str]]):
    def __init__(self, lines: Iterable[str], *, max_chars: int | None = None,
                 check_size: Callable[[int], None] | None = None, **options: Any):
        self.max_chars = max_input_cell_chars() if max_chars is None else max_chars
        if type(self.max_chars) is not int or not 0 < self.max_chars < 2**63:
            raise ValueError("invalid CSV character limit")
        self.check_size = check_size
        self._reader = csv.reader(lines, **options)

    @property
    def line_num(self) -> int:
        return self._reader.line_num

    def __next__(self) -> list[str]:
        overflow = False
        with _parser_lock:
            previous = csv.field_size_limit()
            try:
                csv.field_size_limit(self.max_chars)
                try:
                    return next(self._reader)
                except csv.Error as error:
                    if self.check_size is None or not str(error).startswith("field larger than field limit ("):
                        raise
                    overflow = True
            finally:
                csv.field_size_limit(previous)
        if overflow and self.check_size is not None:
            # First forbidden character, not an estimate of the complete field.
            self.check_size(self.max_chars + 1)
        raise csv.Error("CSV field exceeds character limit")


if TYPE_CHECKING:
    _DictReader = csv.DictReader[str]
else:
    _DictReader = csv.DictReader


class ScopedDictReader(_DictReader):
    def __init__(self, lines: Iterable[str], *, max_chars: int | None = None,
                 check_size: Callable[[int], None] | None = None, **options: Any):
        super().__init__(lines, **options)
        # DictReader consumes __next__ and line_num; stubs require the C reader type.
        self.reader = cast(Any, ScopedCSVReader(lines, max_chars=max_chars, check_size=check_size, **options))
