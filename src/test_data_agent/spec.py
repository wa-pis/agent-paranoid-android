"""Pydantic models for synthetic data generation specifications."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class DataType(StrEnum):
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


class GenerationStrategy(StrEnum):
    SEQUENCE = "sequence"
    RANDOM_INT = "random_int"
    RANDOM_FLOAT = "random_float"
    RANDOM_BOOLEAN = "random_boolean"
    FAKER = "faker"
    CHOICE = "choice"
    CONSTANT = "constant"
    DATE_RANGE = "date_range"
    DATETIME_RANGE = "datetime_range"
    UUID = "uuid"


class OutputFormat(StrEnum):
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"


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


def infer_sensitive_from_name(name: str) -> bool:
    """Conservatively mark likely PII/secrets as sensitive by default."""
    normalized = name.lower().replace("-", "_").replace(" ", "_")
    return any(part in normalized for part in SENSITIVE_NAME_PARTS)


def infer_sensitive_from_profile(column: dict[str, Any]) -> bool:
    if bool(column.get("sensitive")):
        return True
    if infer_sensitive_from_name(str(column.get("name", ""))):
        return True
    semantic_type = str(column.get("semantic_type", "")).lower()
    if semantic_type in {"email", "phone", "name", "address", "ssn", "token", "secret"}:
        return True
    data_type = coerce_profile_type(str(column.get("data_type", "string")))
    return data_type in {DataType.EMAIL, DataType.PHONE, DataType.NAME, DataType.ADDRESS}


class ColumnSpec(BaseModel):
    name: str = Field(min_length=1)
    data_type: DataType
    nullable: bool = False
    sensitive: bool | None = None
    strategy: GenerationStrategy | None = None
    faker_provider: str | None = None
    choices: list[Any] | None = None
    constant: Any | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None
    min_date: date | None = None
    max_date: date | None = None
    min_datetime: datetime | None = None
    max_datetime: datetime | None = None
    null_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    invalid_ratio: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def normalize_defaults(self) -> ColumnSpec:
        if self.sensitive is None:
            self.sensitive = infer_sensitive_from_name(self.name)

        if self.strategy is None:
            self.strategy = default_strategy_for_type(self.data_type)

        if self.strategy == GenerationStrategy.CHOICE and not self.choices:
            raise ValueError("choice strategy requires non-empty choices")
        if self.strategy == GenerationStrategy.CONSTANT and self.constant is None:
            raise ValueError("constant strategy requires constant")
        if self.strategy == GenerationStrategy.FAKER and self.faker_provider is None:
            self.faker_provider = default_faker_provider_for_type(self.data_type)
        if not self.nullable and self.null_probability:
            raise ValueError("null_probability requires nullable=true")
        return self


class TableSpec(BaseModel):
    name: str = Field(min_length=1)
    columns: list[ColumnSpec] = Field(min_length=1)
    row_count: int = Field(gt=0)

    @field_validator("columns")
    @classmethod
    def column_names_must_be_unique(cls, columns: list[ColumnSpec]) -> list[ColumnSpec]:
        names = [column.name for column in columns]
        if len(names) != len(set(names)):
            raise ValueError("column names must be unique")
        return columns


class GenerationSpec(BaseModel):
    seed: int = Field(ge=0)
    table: TableSpec
    output_format: OutputFormat = OutputFormat.JSON

    @classmethod
    def from_mock_profile(cls, profile: dict[str, Any], seed: int, row_count: int) -> GenerationSpec:
        """Build a generation spec from safe profile metadata, not source rows."""
        columns = [column_spec_from_profile(column) for column in profile.get("columns", [])]
        return cls(
            seed=seed,
            table=TableSpec(
                name=profile.get("table", "synthetic_table"),
                columns=columns,
                row_count=row_count,
            ),
        )

    @classmethod
    def from_trino_profile(cls, profile: dict[str, Any], seed: int, row_count: int) -> GenerationSpec:
        """Infer a generation spec from safe Trino-derived table profile metadata."""
        return cls.from_mock_profile(profile, seed=seed, row_count=row_count)

    @classmethod
    def from_csv_profile(cls, profile: dict[str, Any], seed: int, row_count: int) -> GenerationSpec:
        """Infer a generation spec from a safe CSV profile without source rows."""
        return cls.from_mock_profile(profile, seed=seed, row_count=row_count)


def default_strategy_for_type(data_type: DataType) -> GenerationStrategy:
    if data_type == DataType.INTEGER:
        return GenerationStrategy.RANDOM_INT
    if data_type == DataType.FLOAT:
        return GenerationStrategy.RANDOM_FLOAT
    if data_type == DataType.BOOLEAN:
        return GenerationStrategy.RANDOM_BOOLEAN
    if data_type == DataType.UUID:
        return GenerationStrategy.UUID
    if data_type == DataType.DATE:
        return GenerationStrategy.DATE_RANGE
    if data_type == DataType.DATETIME:
        return GenerationStrategy.DATETIME_RANGE
    return GenerationStrategy.FAKER


def default_faker_provider_for_type(data_type: DataType) -> str:
    return {
        DataType.ADDRESS: "address",
        DataType.DATE: "date",
        DataType.DATETIME: "date_time",
        DataType.EMAIL: "email",
        DataType.NAME: "name",
        DataType.PHONE: "phone_number",
        DataType.STRING: "word",
    }.get(data_type, "word")


def coerce_profile_type(raw_type: str) -> DataType:
    type_name = raw_type.lower()
    if "email" in type_name:
        return DataType.EMAIL
    if "phone" in type_name:
        return DataType.PHONE
    if "address" in type_name:
        return DataType.ADDRESS
    if any(part in type_name for part in ("int", "bigint", "smallint", "tinyint")):
        return DataType.INTEGER
    if any(part in type_name for part in ("decimal", "double", "float", "real")):
        return DataType.FLOAT
    if "bool" in type_name:
        return DataType.BOOLEAN
    if "timestamp" in type_name or "datetime" in type_name:
        return DataType.DATETIME
    if "date" in type_name:
        return DataType.DATE
    if "uuid" in type_name:
        return DataType.UUID
    return DataType.STRING


def column_spec_from_profile(column: dict[str, Any]) -> ColumnSpec:
    data_type = infer_profile_data_type(column)
    sensitive = infer_sensitive_from_profile(column)
    choices = infer_enum_choices(column, sensitive=sensitive, data_type=data_type)
    null_probability = infer_null_probability(column)
    min_value, max_value = infer_numeric_range(column, data_type)
    min_date, max_date = infer_date_range(column, data_type)
    min_datetime, max_datetime = infer_datetime_range(column, data_type)

    strategy: GenerationStrategy | None = None
    if choices:
        strategy = GenerationStrategy.CHOICE
    elif data_type == DataType.DATE and min_date and max_date:
        strategy = GenerationStrategy.DATE_RANGE
    elif data_type == DataType.DATETIME and min_datetime and max_datetime:
        strategy = GenerationStrategy.DATETIME_RANGE

    return ColumnSpec(
        name=str(column["name"]),
        data_type=data_type,
        nullable=bool(column.get("nullable", null_probability > 0)),
        sensitive=sensitive,
        strategy=strategy,
        choices=choices,
        min_value=min_value,
        max_value=max_value,
        min_date=min_date,
        max_date=max_date,
        min_datetime=min_datetime,
        max_datetime=max_datetime,
        null_probability=null_probability,
        invalid_ratio=float(column.get("invalid_ratio", 0.0) or 0.0),
    )


def infer_profile_data_type(column: dict[str, Any]) -> DataType:
    semantic_type = str(column.get("semantic_type", "")).lower()
    if semantic_type in {"email", "phone", "name", "address"}:
        return DataType(semantic_type)
    name = str(column.get("name", "")).lower()
    if "email" in name or "mail" in name:
        return DataType.EMAIL
    if "phone" in name:
        return DataType.PHONE
    if "address" in name:
        return DataType.ADDRESS
    if name in {"name", "full_name"} or name.endswith("_name"):
        return DataType.NAME
    return coerce_profile_type(str(column.get("data_type", "string")))


def infer_enum_choices(column: dict[str, Any], sensitive: bool, data_type: DataType = DataType.STRING) -> list[Any] | None:
    if sensitive or data_type != DataType.STRING:
        return None
    raw_choices = column.get("choices") or column.get("enum_values") or column.get("top_values")
    if raw_choices is None:
        return None
    values = [
        item.get("value") if isinstance(item, dict) and "value" in item else item
        for item in raw_choices
    ]
    values = [value for value in values if value is not None]
    approx_distinct = int(column.get("approx_distinct_count", len(values)) or len(values))
    if 1 <= len(values) <= 20 and approx_distinct <= 20:
        return values
    return None


def infer_null_probability(column: dict[str, Any]) -> float:
    if "null_probability" in column:
        return float(column["null_probability"] or 0.0)
    if "null_ratio" in column:
        return float(column["null_ratio"] or 0.0)
    row_count = column.get("row_count")
    null_count = column.get("null_count")
    if row_count and null_count is not None:
        return max(0.0, min(1.0, float(null_count) / float(row_count)))
    return 0.0


def infer_numeric_range(column: dict[str, Any], data_type: DataType) -> tuple[int | float | None, int | float | None]:
    if data_type not in {DataType.INTEGER, DataType.FLOAT}:
        return None, None
    low = first_present(column, "p05", "p10", "min_value", "min")
    high = first_present(column, "p95", "p90", "max_value", "max")
    if low is None or high is None:
        return low, high
    if data_type == DataType.INTEGER:
        return int(round(float(low))), int(round(float(high)))
    return float(low), float(high)


def infer_date_range(column: dict[str, Any], data_type: DataType) -> tuple[date | None, date | None]:
    if data_type != DataType.DATE:
        return None, None
    low = first_present(column, "min_date", "min_value", "min")
    high = first_present(column, "max_date", "max_value", "max")
    return parse_date(low), parse_date(high)


def infer_datetime_range(column: dict[str, Any], data_type: DataType) -> tuple[datetime | None, datetime | None]:
    if data_type != DataType.DATETIME:
        return None, None
    low = first_present(column, "min_datetime", "min_timestamp", "min_value", "min")
    high = first_present(column, "max_datetime", "max_timestamp", "max_value", "max")
    return parse_datetime(low), parse_datetime(high)


def first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


def parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
