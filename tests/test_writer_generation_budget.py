"""Fictional export gates cannot restart cumulative generation allowances."""

from pathlib import Path

import pytest

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.workflows import generate_dataset_bundle, generate_single_entity_profile_artifacts
from test_data_agent.io.writers import write_dataset_rows, write_single_entity_rows
from test_data_agent.postgres_sql_export import render_postgres_sql, write_postgres_sql


def _spec() -> DatasetSpec:
    return DatasetSpec.model_validate({
        "entities": [{"name": "records", "row_count": 1, "fields": [{
            "name": "quantity", "data_type": "integer", "nullable": True, "distribution": {
                "kind": "numeric", "min_value": 2, "max_value": 2,
            },
        }]}],
        "business_rules": {"field_rules": [{
            "table": "records", "field": "quantity", "required": True,
        }]},
    })


def _write(writer, rows, output: Path, *, budget: GenerationBudget | None = None):
    if writer == "dataset":
        write_dataset_rows(rows, OutputFormat.JSON, output, spec=_spec(), budget=budget)
    else:
        write_single_entity_rows(rows, OutputFormat.JSON, output / "records.json",
                                 spec=_spec(), budget=budget)


def test_bundle_writer_cannot_reset_cumulative_work_before_publication(tmp_path, monkeypatch):
    # The whole invocation needs 61 evaluations; splitting the writer's ten
    # evaluations into a fresh allowance previously admitted this request.
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "55")
    output = tmp_path / "output"
    with pytest.raises(GenerationLimitError, match="evaluations"):
        generate_dataset_bundle(_spec(), output_folder=output)
    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("stdout", [False, True])
def test_single_profile_writer_cannot_reset_the_shared_work_allowance(
    tmp_path, monkeypatch, capsys, stdout,
):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "25")
    monkeypatch.chdir(tmp_path)
    profile = DatasetProfile.model_validate({"source_type": "json_profile", "entities": [{
        "name": "records", "row_count": 1,
        "fields": [{"name": "quantity", "data_type": "integer"}],
    }]})
    with pytest.raises(GenerationLimitError, match="evaluations"):
        generate_single_entity_profile_artifacts(
            profile, _spec(), output_path=None if stdout else tmp_path / "records.json",
            rows_by_entity={"records": [{"quantity": 2}]}, budget=GenerationBudget(),
        )
    assert capsys.readouterr().out == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("writer", ["dataset", "single"])
def test_writer_consumes_the_remaining_supplied_rule_allowance(tmp_path, monkeypatch, writer):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "10")
    budget = GenerationBudget()
    budget.consume_rule_work()
    output = tmp_path / "output"
    with pytest.raises(GenerationLimitError, match="evaluations"):
        _write(writer, {"records": [{"quantity": 2}]}, output, budget=budget)
    assert not output.exists()


@pytest.mark.parametrize("writer", ["dataset", "single"])
def test_standalone_writer_creates_a_bounded_allowance(tmp_path, monkeypatch, writer):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "10")
    _write(writer, {"records": [{"quantity": 2}]}, tmp_path / "first")
    _write(writer, {"records": [{"quantity": 2}]}, tmp_path / "second")
    assert (tmp_path / "first" / "records.json").is_file()
    assert (tmp_path / "second" / "records.json").is_file()
    with pytest.raises(ValueError, match="business-rule"):
        _write(writer, {"records": [{"quantity": None}]}, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


@pytest.mark.parametrize("writer", ["dataset", "single"])
def test_writer_retains_the_supplied_deadline_before_publication(tmp_path, writer):
    clock = [0.0]
    budget = GenerationBudget(max_seconds=1, clock=lambda: clock[0])
    clock[0] = 2.0
    output = tmp_path / "output"
    with pytest.raises(GenerationLimitError, match="second budget"):
        _write(writer, {"records": [{"quantity": 2}]}, output, budget=budget)
    assert not output.exists()


def test_postgres_sql_cli_keeps_generation_and_reconciliation_in_one_allowance(
    tmp_path, monkeypatch, capsys,
):
    from test_data_agent.cli import main

    # Generation needs 31 evaluations and SQL reconciliation needs ten more.
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "40")
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(_spec().model_dump_json())
    output = tmp_path / "records.sql"
    assert main(["export-postgres-sql", str(spec_path), "--output", str(output)]) == 2
    assert "evaluations" in capsys.readouterr().err
    assert not output.exists()


def test_postgres_sql_writer_preserves_existing_output_when_shared_work_is_exhausted(
    tmp_path, monkeypatch,
):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "10")
    budget = GenerationBudget()
    budget.consume_rule_work()
    output = tmp_path / "records.sql"
    output.write_text("previous fictional export")
    with pytest.raises(GenerationLimitError, match="evaluations"):
        write_postgres_sql(_spec(), {"records": [{"quantity": 2}]}, output, budget=budget)
    assert output.read_text() == "previous fictional export"


def test_postgres_sql_renderer_retains_the_supplied_deadline():
    clock = [0.0]
    budget = GenerationBudget(max_seconds=1, clock=lambda: clock[0])
    clock[0] = 2.0
    with pytest.raises(GenerationLimitError, match="second budget"):
        render_postgres_sql(_spec(), {"records": [{"quantity": 2}]}, budget=budget)
