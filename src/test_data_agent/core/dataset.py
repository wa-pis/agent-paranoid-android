"""Dataset profile/spec models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from test_data_agent.core.constraint import Constraint
from test_data_agent.core.entity import EntityProfile, EntitySpec
from test_data_agent.core.privacy import PrivacyRule, PrivacySettings
from test_data_agent.core.relationship import Relationship
from test_data_agent.core.settings import GenerationSettings, ValidationSettings


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
    privacy_rules: list[PrivacyRule] = Field(default_factory=list)
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)
    generation_settings: GenerationSettings = Field(default_factory=GenerationSettings)
    validation_settings: ValidationSettings = Field(default_factory=ValidationSettings)

    def entity(self, name: str) -> EntitySpec:
        for entity in self.entities:
            if entity.name == name:
                return entity
        raise KeyError(name)
