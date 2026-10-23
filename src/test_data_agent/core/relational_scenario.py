"""Reviewed synthetic relationship declarations; not a source-data mapping."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

ScenarioName = Annotated[str, Field(min_length=1, max_length=255)]
ScenarioCount = Annotated[int, Field(strict=True, ge=0)]


class RelationalScenario(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True,
                              str_strip_whitespace=True)

    parent_entity: ScenarioName
    parent_field: ScenarioName
    child_entity: ScenarioName
    child_field: ScenarioName
    orphan_count: ScenarioCount = 0
    fanout_counts: Annotated[tuple[ScenarioCount, ...], Field(max_length=1_000_000)] | None = None

    @property
    def edge(self) -> tuple[str, str, str, str]:
        return self.parent_entity, self.parent_field, self.child_entity, self.child_field


@dataclass(frozen=True)
class RelationalScenarioObservation:
    edge: tuple[str, str, str, str]
    requested_orphan_count: int
    observed_orphan_count: int
    requested_fanout_counts: tuple[int, ...] | None
    observed_fanout_counts: tuple[int, ...] | None
    eligible_child_count: int
    null_child_count: int
    valid: bool
    expectations_met: bool
