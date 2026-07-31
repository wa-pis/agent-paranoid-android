"""Safe contract for organization-specific synthetic semantic values."""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from test_data_agent.core.field import FieldType
from test_data_agent.core.privacy import infer_sensitive_value_type


MAX_SEMANTIC_VALUE_LENGTH = 1024


class SemanticProviderError(ValueError):
    """Raised when a semantic provider violates the generation contract."""


class SemanticValueRequest(BaseModel):
    """Immutable row-free metadata supplied to a semantic provider."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    entity_name: str = Field(min_length=1)
    field_name: str = Field(min_length=1)
    semantic_type: str = Field(min_length=1)
    data_type: FieldType
    row_index: int = Field(ge=0)
    seed: int


@runtime_checkable
class SemanticValueProvider(Protocol):
    """Generate a deterministic value from safe field metadata."""

    def generate(self, request: SemanticValueRequest) -> Any | None:
        """Return a candidate value, or None to use built-in generation."""


def request_semantic_value(
    provider: SemanticValueProvider,
    request: SemanticValueRequest,
) -> Any | None:
    """Call a provider and reject unsafe or type-invalid output."""

    try:
        value = provider.generate(request.model_copy(deep=True))
    except Exception as exc:
        raise SemanticProviderError("semantic provider failed") from exc
    if value is None:
        return None
    if infer_sensitive_value_type(value) is not None:
        raise SemanticProviderError("semantic provider returned sensitive data")
    if not _matches_field_type(value, request.data_type):
        raise SemanticProviderError(
            "semantic provider returned a value with the wrong field type"
        )
    if isinstance(value, str) and len(value) > MAX_SEMANTIC_VALUE_LENGTH:
        raise SemanticProviderError("semantic provider value exceeds the size limit")
    return value


def _matches_field_type(value: Any, data_type: FieldType) -> bool:
    if data_type == FieldType.STRING:
        return isinstance(value, str)
    if data_type == FieldType.INTEGER:
        return type(value) is int
    if data_type == FieldType.FLOAT:
        return type(value) in {int, float} and math.isfinite(float(value))
    if data_type == FieldType.BOOLEAN:
        return type(value) is bool
    if not isinstance(value, str):
        return False
    try:
        if data_type == FieldType.DATE:
            date.fromisoformat(value)
        else:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True
