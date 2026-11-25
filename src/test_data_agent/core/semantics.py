"""Deterministic column semantics from bounded aggregate evidence."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, replace

from test_data_agent.core.privacy import SensitiveValueSignal, field_name_words


_NUMERIC_ROLES = frozenset({
    "amount", "balance", "cost", "count", "pct", "percent", "percentage",
    "price", "qty", "quantity", "rate", "ratio", "sum", "total",
})


def semantic_name_hint(name: str, *, numeric: bool) -> str | None:
    words = field_name_words(name)
    tokens = set(words)
    if numeric and tokens & _NUMERIC_ROLES:
        return None
    hints: set[str] = set()
    if tokens & {"email", "mail"}:
        hints.add("email")
    if "phone" in tokens:
        hints.add("phone")
    if "ssn" in tokens or ("tax", "id") in zip(words, words[1:]):
        hints.add("ssn")
    if tokens & {"card", "cc", "pan"}:
        hints.add("card")
    if tokens & {"secret", "password", "passwd", "token", "credential"} or any(
        phrase in zip(words, words[1:])
        for phrase in (("api", "key"), ("access", "key"), ("private", "key"))
    ):
        hints.add("secret")
    if "name" in tokens:
        hints.add("name")
    if "address" in tokens:
        hints.add("address")
    return next(iter(hints)) if len(hints) == 1 else None


def supported_signal_type(
    signal: SensitiveValueSignal, *, hint: str | None, numeric: bool,
) -> str | None:
    if signal.required_context is not None and hint != signal.required_context:
        return None
    if signal is SensitiveValueSignal.PHONE and numeric and hint != "phone":
        return None
    return signal.value_type


@dataclass
class ColumnSemanticEvidence:
    non_null_count: int = 0
    matches: Counter[SensitiveValueSignal] = field(default_factory=Counter)
    all_numeric: bool = True

    def add(
        self, signal: SensitiveValueSignal | None, *, numeric: bool, count: int = 1,
    ) -> None:
        self.non_null_count += count
        self.all_numeric = self.all_numeric and numeric
        if signal is not None:
            self.matches[signal] += count

    @property
    def sensitive(self) -> bool:
        return bool(self.matches)

    def resolve_aggregate(self, name: str, *, non_null_count: int | None) -> str | None:
        """Use full-column coverage rather than normalizing a bounded top list."""
        if any(signal.strong_secret for signal in self.matches):
            return "secret"
        if (
            type(non_null_count) is not int
            or non_null_count <= 0
            or self.non_null_count > non_null_count
        ):
            return None
        return replace(self, non_null_count=non_null_count).resolve(name)

    def resolve(self, name: str) -> str | None:
        if not self.non_null_count:
            return None
        if any(signal.strong_secret for signal in self.matches):
            return "secret"
        hint = semantic_name_hint(name, numeric=self.all_numeric)
        supported: Counter[str] = Counter()
        for signal, count in self.matches.items():
            kind = supported_signal_type(signal, hint=hint, numeric=self.all_numeric)
            if kind is not None:
                supported[kind] += count
        semantic_hint = "secret" if hint == "card" else hint
        for kind in ("email", "phone", "ssn", "secret"):
            if supported[kind] * 5 < self.non_null_count * 4:
                continue
            return kind if semantic_hint is None or semantic_hint == kind else None
        if not self.sensitive and not self.all_numeric and hint in {"name", "address"}:
            return hint
        return None
