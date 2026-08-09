"""Bound and escape untrusted text for human CLI output."""

from __future__ import annotations

import json


DEFAULT_CLI_TEXT_LIMIT = 512


def bound_untrusted_text(value: str, *, limit: int = DEFAULT_CLI_TEXT_LIMIT) -> str:
    truncated = value[:limit]
    return f"{truncated}..." if len(value) > limit else truncated


def display_untrusted_text(value: str, *, limit: int = DEFAULT_CLI_TEXT_LIMIT) -> str:
    escaped = json.dumps(bound_untrusted_text(value, limit=limit), ensure_ascii=False)[1:-1]
    return "".join(
        character
        if character.isprintable()
        else (
            f"\\u{ord(character):04x}"
            if ord(character) <= 0xFFFF
            else f"\\U{ord(character):08x}"
        )
        for character in escaped
    )
