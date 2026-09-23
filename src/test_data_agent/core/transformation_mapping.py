"""Internal mapping declarations; parsing grants no execution authority.

No file reads or type coercion are performed here. Dumps contain private mapping
values and must never be used as public summaries or provider inputs.
"""

from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr, TypeAdapter, ValidationError

from test_data_agent.core.limits import DEFAULT_MAX_INPUT_COLUMNS, DEFAULT_MAX_INPUT_ROWS


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


class DomainMapping(_PrivateModel):
    kind: Literal["domain"]
    name: StrictStr = Field(min_length=1, repr=False)


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
