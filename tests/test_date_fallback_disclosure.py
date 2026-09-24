import pytest

from test_data_agent.adapters.legacy_profile import legacy_profile_to_dataset_profile
from test_data_agent.agent_planning import plan_warnings
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.generation import infer_dataset_spec
from test_data_agent.generation.entity_generator import generate_dataset


@pytest.mark.parametrize("data_type", ["date", "datetime"])
def test_missing_date_bounds_disclosed_without_source_values(data_type):
    profile = legacy_profile_to_dataset_profile({
        "table": "events", "row_count": 3,
        "columns": [{"name": "event_day", "data_type": data_type}],
    })
    spec = infer_dataset_spec(profile)
    rows = generate_dataset(spec, seed=7)["events"]
    assert len(rows) == 3
    assert all("2020-01-01" <= row["event_day"][:10] <= "2025-01-01" for row in rows)
    warning = next(item for item in plan_warnings(spec) if "date/time" in item)
    assert "2020-01-01" in warning and "2025-01-01" in warning
    assert "source-period fidelity" in warning


def test_complete_date_bounds_need_no_fallback_warning():
    profile = legacy_profile_to_dataset_profile({
        "table": "events", "row_count": 3,
        "columns": [{"name": "event_day", "data_type": "date",
                     "min_date": "2026-01-01", "max_date": "2026-01-03"}],
    })
    assert not any("date/time" in item for item in plan_warnings(infer_dataset_spec(profile)))


@pytest.mark.parametrize("distribution,identifier,expected", [
    ({"kind": "date_range", "min": "2021-01-01"}, False, True),
    ({"kind": "date_range", "max": "2024-01-01"}, False, True),
    ({"kind": "categorical", "categories": [{"value": "2021-01-01", "count": 3}]}, False, False),
    ({}, True, False),
])
def test_warning_matches_range_fallback_path(distribution, identifier, expected):
    spec = DatasetSpec(entities=[EntitySpec(name="events", row_count=3, fields=[
        FieldSpec(name="event_day", data_type=FieldType.DATE,
                  is_identifier=identifier, distribution=distribution),
    ])])
    assert any("date/time" in item for item in plan_warnings(spec)) is expected
