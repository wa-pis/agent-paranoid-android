"""Dataset profile/spec models."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from test_data_agent.core.constraint import Constraint
from test_data_agent.core.entity import EntityProfile, EntitySpec
from test_data_agent.core.privacy import LocalCategoryField, PrivacyRule, PrivacySettings
from test_data_agent.core.relationship import Relationship
from test_data_agent.core.settings import GenerationSettings, ValidationSettings


DATASET_SPEC_SCHEMA_VERSION: Literal["1.0"] = "1.0"
SUPPORTED_DATASET_SPEC_SCHEMA_VERSIONS = frozenset({DATASET_SPEC_SCHEMA_VERSION})
DEPRECATED_DATASET_SPEC_SCHEMA_VERSIONS: frozenset[str] = frozenset()
RESERVED_ENTITY_ARTIFACT_BASENAMES = frozenset(
    {
        "agent_completion",
        "business_validation_report",
        "csv_profile",
        "dataset_spec",
        "generation_manifest",
        "profile",
        "validation_report",
    }
)


class DatasetProfile(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    source_type: str = "csv_folder"
    source_fingerprint: str | None = None
    source_policy_version: str | None = None
    entities: list[EntityProfile] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    local_category_fields: list[LocalCategoryField] = Field(default_factory=list)

    @field_validator("source_fingerprint")
    @classmethod
    def validate_source_fingerprint(cls, value: str | None) -> str | None:
        if value is not None and (
            len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError("source fingerprint must be a lowercase SHA-256 digest")
        return value

    @model_validator(mode="after")
    def validate_contract(self) -> DatasetProfile:
        _validate_entity_names(self.entities, "dataset profile")
        _validate_relationship_references(self.entities, self.relationships)
        _validate_constraint_references(self.entities, self.constraints)
        _validate_local_category_fields(self.entities, self.local_category_fields)
        return self

    def entity(self, name: str) -> EntityProfile:
        for entity in self.entities:
            if entity.name == name:
                return entity
        raise KeyError(name)


class DatasetSpec(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    schema_version: Literal["1.0"] = DATASET_SPEC_SCHEMA_VERSION
    entities: list[EntitySpec] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    privacy_rules: list[PrivacyRule] = Field(default_factory=list)
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)
    local_category_fields: list[LocalCategoryField] = Field(default_factory=list)
    generation_settings: GenerationSettings = Field(default_factory=GenerationSettings)
    validation_settings: ValidationSettings = Field(default_factory=ValidationSettings)

    @model_validator(mode="after")
    def validate_contract(self) -> DatasetSpec:
        _validate_entity_names(self.entities, "dataset spec")
        _validate_reserved_entity_names(self.entities)
        _validate_relationship_references(self.entities, self.relationships)
        _validate_constraint_references(self.entities, self.constraints)
        _validate_local_category_fields(self.entities, self.local_category_fields)
        entity_fields = {entity.name: {field.name for field in entity.fields} for entity in self.entities}
        for rule in self.privacy_rules:
            if rule.entity is not None and rule.entity not in entity_fields:
                raise ValueError(f"privacy rule references unknown entity: {rule.entity!r}")
            if rule.entity is not None and rule.field is not None and rule.field not in entity_fields[rule.entity]:
                raise ValueError(
                    f"privacy rule references unknown field: {rule.entity!r}.{rule.field!r}"
                )
        return self

    def entity(self, name: str) -> EntitySpec:
        for entity in self.entities:
            if entity.name == name:
                return entity
        raise KeyError(name)


def parse_dataset_spec_payload(payload: Any) -> DatasetSpec:
    """Validate a DatasetSpec with an explicit fail-closed version check."""

    if isinstance(payload, Mapping):
        version = payload.get("schema_version", DATASET_SPEC_SCHEMA_VERSION)
        if not isinstance(version, str):
            raise ValueError("DatasetSpec schema_version must be a string")
        if version not in SUPPORTED_DATASET_SPEC_SCHEMA_VERSIONS:
            supported = ", ".join(sorted(SUPPORTED_DATASET_SPEC_SCHEMA_VERSIONS))
            raise ValueError(
                f"unsupported DatasetSpec schema_version {version!r}; "
                f"this package supports: {supported}"
            )
    return DatasetSpec.model_validate(payload)


def _validate_entity_names(entities: list[EntityProfile] | list[EntitySpec], context: str) -> None:
    names = [entity.name for entity in entities]
    if len(names) != len(set(names)):
        raise ValueError(f"{context} has duplicate entity names")


def _validate_reserved_entity_names(entities: list[EntitySpec]) -> None:
    if any(entity.name in RESERVED_ENTITY_ARTIFACT_BASENAMES for entity in entities):
        raise ValueError("dataset spec uses a reserved entity name")


def _entity_fields(entities: list[EntityProfile] | list[EntitySpec]) -> dict[str, set[str]]:
    return {entity.name: {field.name for field in entity.fields} for entity in entities}


def _validate_relationship_references(
    entities: list[EntityProfile] | list[EntitySpec],
    relationships: list[Relationship],
) -> None:
    fields = _entity_fields(entities)
    for relationship in relationships:
        for entity_name, field_name in (
            (relationship.parent_entity, relationship.parent_field),
            (relationship.child_entity, relationship.child_field),
        ):
            if entity_name not in fields:
                raise ValueError(f"relationship references unknown entity: {entity_name!r}")
            if field_name not in fields[entity_name]:
                raise ValueError(f"relationship references unknown field: {entity_name!r}.{field_name!r}")


def _validate_constraint_references(
    entities: list[EntityProfile] | list[EntitySpec],
    constraints: list[Constraint],
) -> None:
    fields = _entity_fields(entities)
    for constraint in constraints:
        if constraint.entity not in fields:
            raise ValueError(f"constraint references unknown entity: {constraint.entity!r}")
        missing = sorted(set(constraint.fields) - fields[constraint.entity])
        if missing:
            raise ValueError(
                f"constraint references unknown fields on {constraint.entity!r}: {missing}"
            )
        condition_field = constraint.condition.get("field") if constraint.condition else None
        if condition_field is not None and condition_field not in fields[constraint.entity]:
            raise ValueError(
                f"constraint references unknown condition field: {constraint.entity!r}.{condition_field!r}"
            )
        if constraint.target_entity is not None:
            if constraint.target_entity not in fields:
                raise ValueError(f"constraint references unknown target entity: {constraint.target_entity!r}")
            if constraint.target_field is not None and constraint.target_field not in fields[constraint.target_entity]:
                raise ValueError(
                    "constraint references unknown target field: "
                    f"{constraint.target_entity!r}.{constraint.target_field!r}"
                )


def _validate_local_category_fields(
    entities: list[EntityProfile] | list[EntitySpec],
    fields: list[LocalCategoryField],
) -> None:
    entity_fields = _entity_fields(entities)
    references = [(item.entity, item.field) for item in fields]
    if len(references) != len(set(references)):
        raise ValueError("local category allowlist has duplicate fields")
    for entity_name, field_name in references:
        if entity_name not in entity_fields or field_name not in entity_fields[entity_name]:
            raise ValueError(
                f"local category allowlist references unknown field: {entity_name!r}.{field_name!r}"
            )
