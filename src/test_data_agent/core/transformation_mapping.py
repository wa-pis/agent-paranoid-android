"""Internal mapping declarations; parsing grants no execution authority.

No file reads or type coercion are performed here. Dumps contain private mapping
values and must never be used as public summaries or provider inputs.
"""

from datetime import date, datetime
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr, TypeAdapter, ValidationError

from test_data_agent.core.limits import DEFAULT_MAX_INPUT_COLUMNS, DEFAULT_MAX_INPUT_ROWS
from test_data_agent.core.field import FieldType
from test_data_agent.core.decimal_units import decimal_to_units, decimal_from_units


def _scalar_without_coercion(value: object) -> object:
    if type(value) not in (str, int, float, bool, type(None)):
        raise ValueError("unsupported mapping scalar type")
    return value


Scalar: TypeAlias = Annotated[
    StrictStr | StrictInt | StrictFloat | StrictBool | None,
    BeforeValidator(_scalar_without_coercion),
]
Key: TypeAlias = Annotated[tuple[Scalar, ...], Field(min_length=1, max_length=DEFAULT_MAX_INPUT_COLUMNS)]


class _PrivateModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True,
                              allow_inf_nan=False, revalidate_instances="always")


class MappingEntry(_PrivateModel):
    original: Key = Field(repr=False)
    replacement: Key = Field(repr=False)


class InlineMapping(_PrivateModel):
    kind: Literal["inline"]
    entries: tuple[MappingEntry, ...] = Field(min_length=1, max_length=DEFAULT_MAX_INPUT_ROWS, repr=False)


class CsvMapping(_PrivateModel):
    kind: Literal["csv"]
    path: StrictStr = Field(min_length=1, repr=False)
    source_columns: tuple[StrictStr, ...] = Field(min_length=1, max_length=DEFAULT_MAX_INPUT_COLUMNS, repr=False)
    replacement_columns: tuple[StrictStr, ...] = Field(min_length=1, max_length=DEFAULT_MAX_INPUT_COLUMNS, repr=False)
    encoding: Literal["utf-8", "utf-8-sig"] = Field(default="utf-8", repr=False)
    delimiter: Literal[",", ";", "\t", "|"] = Field(default=",", repr=False)
    null_token: StrictStr | None = Field(default=None, min_length=1, repr=False)


class DomainMapping(_PrivateModel):
    kind: Literal["domain"]
    name: StrictStr = Field(min_length=1, repr=False)
    component: StrictInt | None = Field(default=None, ge=0, lt=DEFAULT_MAX_INPUT_COLUMNS, repr=False)


MappingSource: TypeAlias = Annotated[InlineMapping | CsvMapping | DomainMapping, Field(discriminator="kind")]
_MAPPING: TypeAdapter[MappingSource] = TypeAdapter(MappingSource)


class MappingDeclarationError(ValueError):
    """Value-free structural error; never attach the rejected payload."""


def parse_mapping_declaration(payload: object) -> MappingSource:
    """Parse structure only; paths, types, budgets and approval need preflight."""
    try:
        return _MAPPING.validate_python(payload)
    except ValidationError:
        pass
    # Also detach an ambient caller exception, not just Pydantic's context.
    try:
        raise MappingDeclarationError("invalid mapping declaration")
    except MappingDeclarationError as error:
        error.__context__ = None
        raise


def validate_inline_mapping_shape(payload: object, *, key_width: int) -> InlineMapping:
    """Check tuple widths and exact typed duplicates; no schema normalization."""
    declaration = parse_mapping_declaration(payload)
    valid = type(key_width) is int and 1 <= key_width <= DEFAULT_MAX_INPUT_COLUMNS
    if isinstance(declaration, InlineMapping) and valid:
        seen: set[tuple[tuple[type, object], ...]] = set()
        for entry in declaration.entries:
            if len(entry.original) != key_width or len(entry.replacement) != key_width:
                valid = False
                break
            key = tuple((type(value), value) for value in entry.original)
            if key in seen:
                valid = False
                break
            seen.add(key)
        if valid:
            return declaration
    try:
        raise MappingDeclarationError("invalid inline mapping shape")
    except MappingDeclarationError as error:
        error.__context__ = None
        raise


def validate_inline_scalar_mapping(
    payload: object, *, data_types: tuple[FieldType, ...], nullable: tuple[bool, ...],
    decimal_shapes: tuple[tuple[int, int] | None, ...] | None = None,
) -> InlineMapping:
    """Validate primitives and canonical ISO dates, without coercion."""
    declaration = validate_inline_mapping_shape(payload, key_width=len(data_types))
    if FieldType.DECIMAL in data_types or decimal_shapes is not None:
        try:
            shapes = decimal_shapes or tuple(None for _ in data_types)
            if len(shapes) != len(data_types):
                raise ValueError
            for kind, shape in zip(data_types, shapes, strict=True):
                if (kind == FieldType.DECIMAL) != (shape is not None):
                    raise ValueError
                if shape is not None:
                    precision, scale = shape
                    decimal_from_units(0, precision=precision, scale=scale)
            entries = []
            for entry in declaration.entries:
                converted: dict[str, list[object]] = {}
                for side, values in (("original", entry.original), ("replacement", entry.replacement)):
                    converted[side] = []
                    for value, kind, shape in zip(values, data_types, shapes, strict=True):
                        if shape is not None and value is not None:
                            if not isinstance(value, str):
                                raise ValueError
                            precision, scale = shape
                            units = decimal_to_units(value, precision=precision, scale=scale)
                            value = format(decimal_from_units(units, precision=precision, scale=scale), "f")
                        converted[side].append(value)
                entries.append(converted)
            return validate_inline_scalar_mapping({"kind": "inline", "entries": entries},
                data_types=tuple(FieldType.STRING if kind == FieldType.DECIMAL else kind for kind in data_types),
                nullable=nullable)
        except (ValueError, TypeError):
            pass
        try:
            raise MappingDeclarationError("invalid typed inline mapping")
        except MappingDeclarationError as error:
            error.__context__ = None
            raise
    scalar_types = {FieldType.STRING: str, FieldType.INTEGER: int,
                    FieldType.FLOAT: float, FieldType.BOOLEAN: bool,
                    FieldType.DATE: str, FieldType.DATETIME: str}
    valid = len(nullable) == len(data_types) and all(type(flag) is bool for flag in nullable)
    valid = valid and all(type(kind) is FieldType and kind in scalar_types for kind in data_types)
    if valid:
        for entry in declaration.entries:
            for values in (entry.original, entry.replacement):
                for value, kind, allows_null in zip(values, data_types, nullable, strict=True):
                    if (value is None and not allows_null) or (
                        value is not None and type(value) is not scalar_types[kind]
                    ):
                        valid = False
                    if value is not None and kind == FieldType.DATE:
                        try:
                            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                                valid = False
                        except ValueError:
                            valid = False
                    if value is not None and kind == FieldType.DATETIME:
                        if not isinstance(value, str):
                            valid = False
                        else:
                            try:
                                canonical = datetime.fromisoformat(value).isoformat()
                                if value.endswith("Z") and canonical.endswith("+00:00"):
                                    canonical = canonical[:-6] + "Z"
                                if canonical != value:
                                    valid = False
                            except ValueError:
                                valid = False
    if valid:
        return declaration
    try:
        raise MappingDeclarationError("invalid typed inline mapping")
    except MappingDeclarationError as error:
        error.__context__ = None
        raise
