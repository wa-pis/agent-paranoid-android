"""Types used while normalizing source profile metadata."""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class ProfileDataType(StrEnum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING = "string"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    ADDRESS = "address"
    UUID = "uuid"


def coerce_profile_type(raw_type: str) -> ProfileDataType:
    type_name = raw_type.lower()
    if "email" in type_name:
        return ProfileDataType.EMAIL
    if "phone" in type_name:
        return ProfileDataType.PHONE
    if "address" in type_name:
        return ProfileDataType.ADDRESS
    if any(part in type_name for part in ("int", "bigint", "smallint", "tinyint")):
        return ProfileDataType.INTEGER
    if any(part in type_name for part in ("decimal", "double", "float", "real")):
        return ProfileDataType.FLOAT
    if "bool" in type_name:
        return ProfileDataType.BOOLEAN
    if "timestamp" in type_name or "datetime" in type_name:
        return ProfileDataType.DATETIME
    if "date" in type_name:
        return ProfileDataType.DATE
    if "uuid" in type_name:
        return ProfileDataType.UUID
    return ProfileDataType.STRING


def infer_profile_data_type(column: dict[str, Any]) -> ProfileDataType:
    semantic_type = str(column.get("semantic_type", "")).lower()
    if semantic_type in {"email", "phone", "name", "address"}:
        return ProfileDataType(semantic_type)
    name = str(column.get("name", "")).lower()
    if "email" in name or "mail" in name:
        return ProfileDataType.EMAIL
    if "phone" in name:
        return ProfileDataType.PHONE
    if "address" in name:
        return ProfileDataType.ADDRESS
    if name in {"name", "full_name"} or name.endswith("_name"):
        return ProfileDataType.NAME
    return coerce_profile_type(str(column.get("data_type", "string")))
