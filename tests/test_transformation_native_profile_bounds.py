"""Bounded fictional native review profiles, without database access or approval."""

import io

import pytest

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.csv_profiler import CSVColumnAccumulator
from test_data_agent.io.transformation_query_snapshot import _capture_query_result
from test_data_agent.io import transformation_source


@pytest.mark.parametrize("input_format", ["parquet", "postgres_query", "trino_query"])
def test_native_review_profiles_do_not_retain_per_cell_distinct_digests(
    monkeypatch, input_format,
):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    retained_peaks = []

    class ObservedAccumulator(CSVColumnAccumulator):
        def add(self, raw_value, *, literal_empty=False):
            result = super().add(raw_value, literal_empty=literal_empty)
            retained_peaks.append(len(self.distinct_digests))
            return result

    monkeypatch.setattr(transformation_source, "CSVColumnAccumulator", ObservedAccumulator)
    policy = BehaviorPolicy.model_validate({
        "schema_version": "0.1", "seed": 7, "schema_fingerprint": "0" * 64,
        "input_format": input_format,
        "fields": [{"entity": "items", "field": name, "sensitivity": "unknown",
                    "behavior": {"action": "drop"}}
                   for name in ("units", "label", "message")],
    })
    for count in (64, 2048):
        values = {
            "units": list(range(count)),
            "label": [f"fictional case {index}" for index in range(count)],
            "message": [None] * (count - 1) + ["fictional@example.invalid"],
        }
        profiles = []
        for reverse in (False, True):
            buffer = io.BytesIO()
            pq.write_table(pa.table({name: cells[::-1] if reverse else cells
                                    for name, cells in values.items()}), buffer)
            payload = buffer.getvalue()
            source = (SnapshotPart("source", "items", payload) if input_format == "parquet"
                      else _capture_query_result(payload, adapter=input_format,
                          query_sha256="0" * 64, entity="items"))
            profile = transformation_source._profile_transformation_source(
                source, policy, budget=GenerationBudget(10), max_bytes=1024 * 1024,
            )
            # Observe every add, so clearing only at finalization cannot hide growth.
            assert retained_peaks and max(retained_peaks) == 0
            profiles.append(profile.model_dump(mode="json"))
            entity = profile.entities[0]
            assert entity.row_count == count
            assert entity.primary_key_candidates == []
            units, label, message = entity.fields
            assert [field.data_type.value for field in entity.fields] == [
                "integer", "string", "string",
            ]
            assert [field.sensitive for field in entity.fields] == [False, False, True]
            assert [field.semantic_type for field in entity.fields] == [None, None, "email"]
            assert [field.null_ratio for field in entity.fields] == [
                0, 0, round((count - 1) / count, 6),
            ]
            assert not units.nullable and not label.nullable and message.nullable
            assert all(field.unique_ratio is None for field in entity.fields)
            assert all(field.unique_ratio_kind == "unspecified" for field in entity.fields)
            assert all(not field.is_identifier and not field.distribution
                       for field in entity.fields)
            assert "fictional case" not in profile.model_dump_json()
            assert "fictional@example.invalid" not in profile.model_dump_json()
        assert profiles[0] == profiles[1]
