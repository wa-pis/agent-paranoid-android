"""Entity profiles and specs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from test_data_agent.core.field import FieldProfile, FieldSpec


class EntityProfile(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    name: str = Field(min_length=1)
    row_count: int = Field(ge=0)
    fields: list[FieldProfile] = Field(default_factory=list)
    primary_key_candidates: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_field_references(self) -> EntityProfile:
        field_names = [field.name for field in self.fields]
        if len(field_names) != len(set(field_names)):
            raise ValueError(f"entity profile {self.name!r} has duplicate field names")
        missing = sorted(set(self.primary_key_candidates) - set(field_names))
        if missing:
            raise ValueError(f"entity profile {self.name!r} has unknown primary key candidates: {missing}")
        return self

    def field(self, name: str) -> FieldProfile:
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)


class EntitySpec(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    name: str = Field(min_length=1)
    row_count: int = Field(gt=0)
    fields: list[FieldSpec] = Field(default_factory=list)
    primary_key: str | None = None

    @model_validator(mode="after")
    def validate_field_references(self) -> EntitySpec:
        field_names = [field.name for field in self.fields]
        if len(field_names) != len(set(field_names)):
            raise ValueError(f"entity spec {self.name!r} has duplicate field names")
        if self.primary_key is not None and self.primary_key not in field_names:
            raise ValueError(f"entity spec {self.name!r} has unknown primary key: {self.primary_key!r}")
        return self

    def field(self, name: str) -> FieldSpec:
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)
