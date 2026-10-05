"""Every generator consumer rejects oversized allocation before row creation."""

import argparse
import random

import pytest
import yaml

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.distribution import StringPatternDistribution
from test_data_agent.core.limits import GenerationLimitError
from test_data_agent.generation.entity_generator import generate_dataset, synthetic_string
from test_data_agent.io.commands import export_postgres_sql_command


def spec(length=12, rows=1):
    return DatasetSpec.model_validate({"entities": [{"name": "items", "row_count": rows,
        "fields": [{"name": "payload", "data_type": "string", "distribution": {
            "kind": "string_pattern", "min_length": length, "max_length": length}}]}]})


@pytest.mark.parametrize("length,rows", [(10**12, 1), (1000, 100000)])
def test_direct_generation_rejects_before_row_generation(monkeypatch, length, rows):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_OUTPUT_BYTES", "100000")
    monkeypatch.setattr("test_data_agent.generation.entity_generator.generate_row",
                        lambda *a, **k: pytest.fail("allocated row before preflight"))
    with pytest.raises(GenerationLimitError, match="estimated generated data"):
        generate_dataset(spec(length, rows), seed=1)


def test_sql_export_uses_same_preflight(tmp_path, monkeypatch):
    path = tmp_path / "spec.yaml"
    path.write_text(yaml.safe_dump(spec(10**12).model_dump(mode="json")))
    output = tmp_path / "output.sql"
    monkeypatch.setattr("test_data_agent.generation.entity_generator.generate_row",
                        lambda *a, **k: pytest.fail("allocated export row"))
    with pytest.raises(GenerationLimitError):
        export_postgres_sql_command(argparse.Namespace(spec=path, output=output,
            overwrite=False, seed=1, count=None))
    assert not output.exists()


def test_string_value_guard_precedes_random_allocation(monkeypatch):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS", "10")
    field = FieldSpec(name="payload", data_type="string")
    with pytest.raises(GenerationLimitError, match="cell size"):
        synthetic_string(field, StringPatternDistribution(min_length=11, max_length=11), random.Random(1))


def test_ordinary_seeded_output_unchanged():
    assert generate_dataset(spec(), seed=7) == generate_dataset(spec(), seed=7)
