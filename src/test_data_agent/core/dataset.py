"""Dataset profile/spec models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from test_data_agent.core.constraint import Constraint
from test_data_agent.core.entity import EntityProfile, EntitySpec
from test_data_agent.core.relationship import Relationship


class DatasetProfile(BaseModel):
    source_type: str = "csv_folder"
    entities: list[EntityProfile] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)

    def entity(self, name: str) -> EntityProfile:
        for entity in self.entities:
            if entity.name == name:
                return entity
        raise KeyError(name)


class DatasetSpec(BaseModel):
    entities: list[EntitySpec] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)

    def entity(self, name: str) -> EntitySpec:
        for entity in self.entities:
            if entity.name == name:
                return entity
        raise KeyError(name)
