"""Field profiles and generation specs."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class FieldType(StrEnum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING = "string"
    DATE = "date"
    DATETIME = "datetime"


class FieldProfile(BaseModel):
    name: str
    data_type: FieldType
    nullable: bool = False
    null_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    unique_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    sensitive: bool = False
    semantic_type: str | None = None
    is_identifier: bool = False
    distribution: dict[str, Any] = Field(default_factory=dict)


class FieldSpec(BaseModel):
    name: str
    data_type: FieldType
    nullable: bool = False
    null_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    sensitive: bool = False
    semantic_type: str | None = None
    is_identifier: bool = False
    distribution: dict[str, Any] = Field(default_factory=dict)
