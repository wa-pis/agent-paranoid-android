"""Relationship metadata."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class RelationshipType(StrEnum):
    MANY_TO_ONE = "many_to_one"
    ONE_TO_ONE = "one_to_one"


class Relationship(BaseModel):
    parent_entity: str
    parent_field: str
    child_entity: str
    child_field: str
    relationship_type: RelationshipType = RelationshipType.MANY_TO_ONE
    confidence: float = Field(ge=0.0, le=1.0)
    status: str = "inferred"
