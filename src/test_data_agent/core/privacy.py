"""Privacy policy models for safe synthetic dataset specifications."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable
from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


SENSITIVE_NAME_PARTS = {
    "address",
    "birth",
    "card",
    "cc",
    "credential",
    "dob",
    "email",
    "first_name",
    "firstname",
    "full_name",
    "last_name",
    "lastname",
    "mail",
    "name",
    "passport",
    "password",
    "phone",
    "secret",
    "ssn",
    "tax_id",
    "token",
    "user",
    "username",
}

SENSITIVE_SEMANTIC_TYPES = {
    "address",
    "email",
    "name",
    "phone",
    "secret",
    "ssn",
    "token",
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[\d\s().-]{7,}$")
SSN_RE = re.compile(r"^\d{3}-?\d{2}-?\d{4}$")
PAYMENT_CARD_RE = re.compile(r"^(?:\d[ -]*?){13,19}$")
JWT_RE = re.compile(r"^[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}$")
KNOWN_SECRET_RE = re.compile(
    r"^(?:"
    r"(?:sk|pk)_(?:live|test)_[A-Za-z0-9_-]{8,}"
    r"|(?:gh[opurs]|github_pat)_[A-Za-z0-9_]{20,}"
    r"|(?:AKIA|ASIA)[A-Z0-9]{16}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}"
    r")$"
)
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd|secret)"
    r"\s*[:=]\s*\S+",
    re.IGNORECASE,
)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")
BEARER_TOKEN_RE = re.compile(r"^Bearer\s+\S+$", re.IGNORECASE)
TOKEN_ALPHABET_RE = re.compile(r"^[A-Za-z0-9_+/=-]+$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class PrivacyClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    SECRET = "secret"


class PrivacyAction(StrEnum):
    SYNTHETIC = "synthetic"
    MASK = "mask"
    SUPPRESS = "suppress"


class PrivacyRule(BaseModel):
    entity: str | None = None
    field: str | None = None
    classification: PrivacyClassification = PrivacyClassification.SENSITIVE
    action: PrivacyAction = PrivacyAction.SYNTHETIC
    semantic_type: str | None = None
    reason: str | None = None


class PrivacySettings(BaseModel):
    default_classification: PrivacyClassification = PrivacyClassification.INTERNAL
    pii_classification: PrivacyClassification = PrivacyClassification.SENSITIVE
    secret_classification: PrivacyClassification = PrivacyClassification.SECRET
    treat_unknown_as_sensitive: bool = True
    allow_raw_sensitive_values: bool = False
    max_safe_categories: int = Field(default=20, ge=0)


def normalize_field_name(name: str) -> str:
    return name.lower().replace("-", "_").replace(" ", "_")


def infer_sensitive_from_name(name: str) -> bool:
    """Conservatively mark likely PII/secrets as sensitive by default."""
    normalized = normalize_field_name(name)
    return any(part in normalized for part in SENSITIVE_NAME_PARTS)


def semantic_type_is_sensitive(semantic_type: str | None) -> bool:
    if semantic_type is None:
        return False
    return semantic_type.lower() in SENSITIVE_SEMANTIC_TYPES


def is_sensitive_field(name: str, semantic_type: str | None = None) -> bool:
    return infer_sensitive_from_name(name) or semantic_type_is_sensitive(semantic_type)


def infer_sensitive_value_type(value: Any) -> str | None:
    """Classify recognizable PII and credentials without retaining the value."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if is_iso_date(text):
        return None
    if PRIVATE_KEY_RE.search(text) or BEARER_TOKEN_RE.fullmatch(text):
        return "secret"
    if KNOWN_SECRET_RE.fullmatch(text) or SECRET_ASSIGNMENT_RE.search(text):
        return "secret"
    if JWT_RE.fullmatch(text) or looks_high_entropy_token(text):
        return "secret"
    if EMAIL_RE.fullmatch(text):
        return "email"
    if SSN_RE.fullmatch(text):
        return "ssn"
    if PAYMENT_CARD_RE.fullmatch(text) and passes_luhn_check(text):
        return "secret"
    if PHONE_RE.fullmatch(text) and 7 <= sum(char.isdigit() for char in text) <= 15:
        return "phone"
    return None


def infer_sensitive_type_from_values(values: Iterable[Any]) -> str | None:
    detected: str | None = None
    for value in values:
        value_type = infer_sensitive_value_type(value)
        if value_type == "secret":
            return value_type
        if detected is None and value_type is not None:
            detected = value_type
    return detected


def looks_sensitive_value(value: Any) -> bool:
    return infer_sensitive_value_type(value) is not None


def looks_high_entropy_token(text: str) -> bool:
    if not 24 <= len(text) <= 4096 or not TOKEN_ALPHABET_RE.fullmatch(text):
        return False
    character_classes = sum(
        (
            any(char.islower() for char in text),
            any(char.isupper() for char in text),
            any(char.isdigit() for char in text),
            any(char in "_+/=-" for char in text),
        )
    )
    if character_classes < 2:
        return False
    counts = Counter(text)
    entropy = -sum((count / len(text)) * math.log2(count / len(text)) for count in counts.values())
    return entropy >= 3.5


def passes_luhn_check(text: str) -> bool:
    digits = [int(char) for char in text if char.isdigit()]
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return bool(digits) and checksum % 10 == 0


def is_iso_date(text: str) -> bool:
    if ISO_DATE_RE.fullmatch(text) is None:
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def mask_pattern(value: str, semantic_type: str | None) -> str:
    if semantic_type_is_sensitive(semantic_type):
        return str(semantic_type).lower()
    return f"text_len_{len(value)}"


def mask_value(value: Any) -> Any:
    if value is None:
        return None
    text = str(value)
    if len(text) <= 2:
        return "*" * len(text)
    return f"{text[0]}***{text[-1]}"
