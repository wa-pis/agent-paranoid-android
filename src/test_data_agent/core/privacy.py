"""Privacy policy models for safe synthetic dataset specifications."""

from __future__ import annotations

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
