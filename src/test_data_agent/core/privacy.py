"""Privacy policy models for safe synthetic dataset specifications."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from test_data_agent.core.limits import InputLimitError, max_input_cell_chars


SYNTHETIC_PREFIX = "synthetic_"

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
_SYNTHETIC_CATEGORY_LABEL_RE = re.compile(
    r"category_(?:[1-9]|[1-4][0-9]|50)(?:_(?:[1-9]|1[0-9]|20))?"
)


class PrivacyClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    SECRET = "secret"


class PrivacyAction(StrEnum):
    SYNTHETIC = "synthetic"
    MASK = "mask"
    SUPPRESS = "suppress"


class SensitiveValueSignal(StrEnum):
    PRIVATE_KEY = "private_key_format"
    BEARER_TOKEN = "bearer_context"
    KNOWN_SECRET = "known_secret_format"
    SECRET_ASSIGNMENT = "secret_assignment_context"
    JWT_SHAPE = "jwt_shape"
    HIGH_ENTROPY = "high_entropy"
    EMAIL = "email_format"
    SSN_FORMAT = "ssn_format"
    SSN_DIGITS = "ssn_digits"
    LUHN = "luhn_checksum"
    PHONE = "phone_shape"

    @property
    def value_type(self) -> str:
        if self is SensitiveValueSignal.EMAIL:
            return "email"
        if self in (SensitiveValueSignal.SSN_FORMAT, SensitiveValueSignal.SSN_DIGITS):
            return "ssn"
        if self is SensitiveValueSignal.PHONE:
            return "phone"
        return "secret"

    @property
    def required_context(self) -> str | None:
        if self is SensitiveValueSignal.SSN_DIGITS:
            return "ssn"
        if self is SensitiveValueSignal.LUHN:
            return "card"
        if self in (SensitiveValueSignal.JWT_SHAPE, SensitiveValueSignal.HIGH_ENTROPY):
            return "secret"
        return None

    @property
    def strong_secret(self) -> bool:
        return self in (
            SensitiveValueSignal.PRIVATE_KEY, SensitiveValueSignal.BEARER_TOKEN,
            SensitiveValueSignal.KNOWN_SECRET, SensitiveValueSignal.SECRET_ASSIGNMENT,
        )


class LocalCategoryField(BaseModel):
    """Explicit field scope for local non-sensitive category preservation."""

    entity: str = Field(max_length=256)
    field: str = Field(max_length=256)

    @field_validator("entity", "field")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("local category entity and field must be non-empty")
        return value


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


def validate_local_category_field(
    *, field_name: str, semantic_type: str | None, sensitive: bool,
) -> None:
    """Validate field eligibility without fetching exact values."""
    if sensitive or infer_sensitive_from_name(field_name):
        raise ValueError("local category field is sensitive")
    normalized_name = normalize_field_name(field_name)
    name_parts = set(normalized_name.split("_"))
    if (
        normalized_name == "id"
        or normalized_name.endswith("_id")
        or normalized_name == "key"
        or normalized_name.endswith("_key")
        or name_parts & {"uuid", "guid"}
    ):
        raise ValueError("local category identifiers cannot be preserved")
    if name_parts & {"age", "ip", "latitude", "longitude", "postal", "postcode", "zip"}:
        raise ValueError("local category quasi-identifiers cannot be preserved")
    normalized_semantic_type = (semantic_type or "").strip().lower()
    if semantic_type_is_sensitive(semantic_type) or normalized_semantic_type in {
        "identifier",
        "quasi_identifier",
        "quasi-identifier",
    }:
        raise ValueError("local category semantic type is sensitive")


def validate_local_category_values(
    *,
    field_name: str,
    semantic_type: str | None,
    sensitive: bool,
    values: Iterable[Any],
    max_categories: int = 20,
    max_value_length: int = 64,
) -> None:
    """Fail closed unless exact local values are bounded non-sensitive scalars."""

    validate_local_category_field(
        field_name=field_name, semantic_type=semantic_type, sensitive=sensitive,
    )
    if (
        type(max_categories) is not int or type(max_value_length) is not int
        or max_categories < 1 or max_value_length < 1
    ):
        raise ValueError("local category limits must be positive integers")

    candidates: list[Any] = []
    for value in values:
        if len(candidates) >= max_categories:
            raise ValueError("local category cardinality exceeds its limit")
        candidates.append(value)
    if not candidates:
        raise ValueError("local category values must not be empty")

    seen: set[tuple[type[object], object]] = set()
    for value in candidates:
        if type(value) not in {str, int, bool}:
            raise ValueError("local category values must be bounded scalars")
        key = (type(value), value)
        if key in seen:
            raise ValueError("local category values must be unique")
        seen.add(key)
        text = str(value)
        if len(text) > max_value_length:
            raise ValueError("local category value length exceeds its limit")
        if isinstance(value, str) and _looks_like_local_free_text(value):
            raise ValueError("local category values contain free text")
    if any(infer_source_value_signal(value) is not None for value in candidates):
        raise ValueError("local category values contain sensitive content")


def normalize_field_name(name: str) -> str:
    return name.lower().replace("-", "_").replace(" ", "_")


def field_name_words(name: str) -> tuple[str, ...]:
    expanded = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", expanded)
    return tuple(word.casefold() for word in re.findall(r"[^\W_]+", expanded))


def infer_sensitive_from_name(name: str) -> bool:
    """Conservatively mark likely PII/secrets as sensitive by default."""
    normalized = normalize_field_name(name)
    if any(
        part in normalized if part != "cc" else part in normalized.split("_")
        for part in SENSITIVE_NAME_PARTS
    ):
        return True
    words = field_name_words(name)
    return bool(set(words) & {"cc", "pan", "passwd"}) or any(
        phrase in zip(words, words[1:])
        for phrase in (("tax", "id"), ("api", "key"), ("access", "key"), ("private", "key"))
    )


def semantic_type_is_sensitive(semantic_type: str | None) -> bool:
    if semantic_type is None:
        return False
    return semantic_type.lower() in SENSITIVE_SEMANTIC_TYPES


def is_sensitive_field(name: str, semantic_type: str | None = None) -> bool:
    return infer_sensitive_from_name(name) or semantic_type_is_sensitive(semantic_type)


def infer_sensitive_value_type(value: Any) -> str | None:
    """Classify recognizable PII and credentials without retaining the value."""
    signal = infer_sensitive_value_signal(value)
    return signal.value_type if signal is not None else None


def infer_sensitive_value_signal(value: Any) -> SensitiveValueSignal | None:
    """Return a fixed reason code while preserving conservative recognition."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if is_iso_date(text):
        return None
    if PRIVATE_KEY_RE.search(text):
        return SensitiveValueSignal.PRIVATE_KEY
    if BEARER_TOKEN_RE.fullmatch(text):
        return SensitiveValueSignal.BEARER_TOKEN
    # Builtin membership preserves regex semantics for custom str subclasses.
    if KNOWN_SECRET_RE.fullmatch(text):
        return SensitiveValueSignal.KNOWN_SECRET
    if (
        (str.__contains__(text, ":") or str.__contains__(text, "="))
        and SECRET_ASSIGNMENT_RE.search(text)
    ):
        return SensitiveValueSignal.SECRET_ASSIGNMENT
    if JWT_RE.fullmatch(text):
        return SensitiveValueSignal.JWT_SHAPE
    if looks_high_entropy_token(text):
        return SensitiveValueSignal.HIGH_ENTROPY
    if str.__contains__(text, "@") and EMAIL_RE.fullmatch(text):
        return SensitiveValueSignal.EMAIL
    if SSN_RE.fullmatch(text):
        return (
            SensitiveValueSignal.SSN_FORMAT if str.count(text, "-") == 2
            else SensitiveValueSignal.SSN_DIGITS
        )
    if PAYMENT_CARD_RE.fullmatch(text) and passes_luhn_check(text):
        return SensitiveValueSignal.LUHN
    if PHONE_RE.fullmatch(text) and 7 <= sum(char.isdigit() for char in text) <= 15:
        return SensitiveValueSignal.PHONE
    return None


def infer_profile_string_signal(
    value: str, *, max_chars: int | None = None,
) -> SensitiveValueSignal | None:
    """Retain the bounded numeric-evidence policy used by CSV profiles."""
    if len(value) > (max_input_cell_chars() if max_chars is None else max_chars):
        raise InputLimitError("source value exceeds character limit")
    detected = infer_sensitive_value_signal(value)
    detected_type = detected.value_type if detected is not None else None
    if detected_type not in {None, "phone"}:
        return detected
    try:
        number = Decimal(value)
    except InvalidOperation:
        return detected
    if not number.is_finite():
        return detected
    # Statistics retain binary floats. Inspect that representation as well as
    # the exact decimal; rounding must not turn an unclassified value into PII.
    # Bound magnitude before conversion or expansion of exponent notation.
    if not -64 <= number.adjusted() <= 18:
        return detected
    retained = Decimal(str(float(number)))
    # Only negative fractional measures are unambiguous here. Positive dotted
    # numbers and integral decimal identifiers remain potentially sensitive.
    if (
        detected_type == "phone" and re.fullmatch(r"-\d+\.\d+", value)
        and number != number.to_integral_value()
        and retained != retained.to_integral_value()
    ):
        return None
    for candidate in (number, retained):
        exponent = candidate.as_tuple().exponent
        if not isinstance(exponent, int) or exponent < -64:
            continue
        canonical = format(candidate.copy_abs(), "f")
        if "." in canonical:
            canonical = canonical.rstrip("0").rstrip(".")
        normalized_signal = infer_sensitive_value_signal(canonical)
        if normalized_signal is not None and normalized_signal.value_type == "secret":
            return normalized_signal
        detected = detected or normalized_signal
    return detected


def infer_source_value_signal(
    value: Any, *, max_chars: int | None = None,
) -> SensitiveValueSignal | None:
    """Normalize source scalars without relaxing strict string protection."""
    if not isinstance(value, str):
        if type(value) not in {int, float, Decimal}:
            return None
        try:
            value = str(value)
        except ValueError:
            raise InputLimitError("source numeric value exceeds character limit") from None
        return infer_profile_string_signal(value, max_chars=max_chars)
    return infer_profile_string_signal(value, max_chars=max_chars) or infer_sensitive_value_signal(value)


def infer_category_value_signal(
    value: Any, *, max_chars: int | None = None,
) -> SensitiveValueSignal | None:
    """Generated rank labels are bounded metadata, rather than source cells."""
    if type(value) is str and _SYNTHETIC_CATEGORY_LABEL_RE.fullmatch(value):
        max_chars = max(len(value), max_input_cell_chars() if max_chars is None else max_chars)
    return infer_source_value_signal(value, max_chars=max_chars)


def has_sensitive_numeric_summary(
    summary: Mapping[str, Any], *, max_chars: int | None = None,
) -> bool:
    return any(
        infer_source_value_signal(summary.get(key), max_chars=max_chars) is not None
        for key in ("min_value", "max_value", "p05", "p95")
    )


def infer_sensitive_type_from_values(values: Iterable[Any]) -> str | None:
    detected: str | None = None
    for value in values:
        value_type = infer_sensitive_value_type(value)
        if value_type == "secret":
            return value_type
        if detected is None and value_type is not None:
            detected = value_type
    return detected


def _looks_like_local_free_text(value: str) -> bool:
    if not value or value.count(" ") > 3 or ":" in value:
        return True
    if any(char.isspace() for char in value) and any(char.isdigit() for char in value):
        return False
    return False


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
    entropy = -sum(
        (count / len(text)) * math.log2(count / len(text)) for count in counts.values()
    )
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


def synthetic_category_distribution(
    counts: Iterable[int],
    *,
    reserved_values: Iterable[str] = (),
) -> list[dict[str, str | int]]:
    """Preserve category frequency ranks without exposing source values."""
    reserved = set(reserved_values)
    categories: list[dict[str, str | int]] = []
    for rank, count in enumerate(counts, start=1):
        value = f"category_{rank}"
        suffix = 1
        while value in reserved:
            value = f"category_{rank}_{suffix}"
            suffix += 1
        reserved.add(value)
        categories.append({"value": value, "count": int(count)})
    return categories


def mask_value(value: Any) -> Any:
    if value is None:
        return None
    return "[MASKED]"
