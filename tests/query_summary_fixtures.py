"""Encode fictional per-column aggregates as a batched driver response."""
import re
from collections.abc import Sequence


def batch_aggregate_rows(sql: str, summaries: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    aliases = re.findall(r'AS "(__apa_(\d+)_([a-z_]+))"', sql)
    if not aliases:
        raise AssertionError("expected a batched aggregate query")
    return [{alias: summaries[int(index)][name] for alias, index, name in aliases
             if name in summaries[int(index)]}]
