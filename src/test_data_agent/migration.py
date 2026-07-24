"""Actionable errors for removed public input contracts."""

from __future__ import annotations

from typing import Any


REMOVED_SPEC_MIGRATION_URL = (
    "https://wa-pis.github.io/agent-paranoid-android/operations/migrating-to-0.6/"
)


def reject_removed_spec_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    if isinstance(payload.get("table"), dict) or isinstance(payload.get("tables"), list):
        raise ValueError(
            "GenerationSpec was removed in 0.6.0. Convert this file to DatasetSpec: "
            f"{REMOVED_SPEC_MIGRATION_URL}"
        )
