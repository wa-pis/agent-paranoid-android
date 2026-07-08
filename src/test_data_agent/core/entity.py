"""Entity profiles and specs."""

from __future__ import annotations

from pydantic import BaseModel, Field

from test_data_agent.core.field import FieldProfile, FieldSpec


class EntityProfile(BaseModel):
    name: str
    row_count: int = Field(ge=0)
    fields: list[FieldProfile] = Field(default_factory=list)
    primary_key_candidates: list[str] = Field(default_factory=list)

    def field(self, name: str) -> FieldProfile:
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)


class EntitySpec(BaseModel):
    name: str
    row_count: int = Field(gt=0)
    fields: list[FieldSpec] = Field(default_factory=list)
    primary_key: str | None = None

    def field(self, name: str) -> FieldSpec:
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)
