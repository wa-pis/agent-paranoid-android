"""External feedback regressions with fictional metadata and generated inputs."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from test_data_agent.cli import main
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.io.workflows import generate_dataset_bundle
from test_data_agent.sql_query_source import (
    QuerySourceColumn, SqlQueryAdapter, SqlQueryProfileRequest, SqlQuerySourceError,
    authorize_query_source, inspect_query_source,
)
from test_data_agent.validation import validate_dataset


def linked_spec() -> DatasetSpec:
    return DatasetSpec.model_validate({
        "entities": [
            {"name": "product", "row_count": 3, "fields": [
                {"name": "key", "data_type": "integer", "is_identifier": True},
                {"name": "other", "data_type": "integer", "is_identifier": True}]},
            {"name": "deal", "row_count": 6, "fields": [
                {"name": "product_key", "data_type": "integer"},
                {"name": "other", "data_type": "integer", "is_identifier": True}]}],
        "relationships": [{"parent_entity": "product", "parent_field": "key",
                           "child_entity": "deal", "child_field": "product_key", "confidence": 1}],
    })


def test_relationship_uses_exact_fields_and_reports_resolution():
    spec = linked_spec()
    rows = generate_dataset(spec, seed=8)
    keys = {row["key"] for row in rows["product"]}
    assert all(row["product_key"] in keys for row in rows["deal"])
    assert all(row["other"] not in keys for row in rows["deal"])
    report = validate_dataset(rows, spec)
    section = next(s for s in report.sections if s.name == "relationships")
    assert (section.checked, section.passed, section.failed) == (1, 1, 0)
    metric = section.relationship_metrics[0]
    assert (metric.checked_references, metric.resolved_references, metric.resolution_ratio) == (6, 6, 1)
    rows["deal"][0]["product_key"] = -1
    report = validate_dataset(rows, spec)
    assert not report.valid
    section = next(s for s in report.sections if s.name == "relationships")
    assert section.relationship_metrics[0].resolved_references == 5
    assert section.passed == 0


def test_no_declared_relationships_are_not_reported_as_success():
    spec = linked_spec()
    spec.relationships = []
    report = validate_dataset(generate_dataset(spec, seed=8), spec)
    section = next(s for s in report.sections if s.name == "relationships")
    assert (section.checked, section.passed, section.failed) == (0, 0, 0)
    assert section.relationship_metrics == []


@pytest.mark.parametrize("invalid", ["type", "duplicate"])
def test_invalid_field_bindings_rejected(invalid):
    payload = linked_spec().model_dump(mode="json")
    if invalid == "type":
        payload["entities"][1]["fields"][0]["data_type"] = "string"
    else:
        payload["relationships"].append(dict(payload["relationships"][0], parent_field="other"))
    with pytest.raises(ValidationError, match="same data type|same child field"):
        DatasetSpec.model_validate(payload)


@pytest.mark.parametrize("mode", ["edge", "load_test"])
def test_unimplemented_dataset_modes_fail_before_publication(tmp_path, mode):
    spec = linked_spec()
    spec.generation_settings.mode = mode
    with pytest.raises(ValueError, match="not supported"):
        generate_dataset_bundle(spec, output_folder=tmp_path / "output", seed=8)
    assert not (tmp_path / "output").exists()


def test_spec_overwrite_is_explicit_and_preserves_existing_files(tmp_path, capsys):
    spec = tmp_path / "spec.json"
    spec.write_text(linked_spec().model_dump_json())
    out = tmp_path / "out"
    out.mkdir()
    (out / "keep.txt").write_text("fictional")
    assert main(["generate", str(spec), "--output", str(out), "--overwrite"]) == 2
    assert "--overwrite is supported only" in capsys.readouterr().err
    assert (out / "keep.txt").read_text() == "fictional"
    assert list(out.iterdir()) == [out / "keep.txt"]


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("limit", ["1", "10", "1000", "0", "1001", "-1", "1.5"])
def test_query_limit_is_bounded_and_preserved(tmp_path, adapter, limit):
    query_file = tmp_path / "query.sql"
    table = "public.item" if adapter == SqlQueryAdapter.POSTGRES else "lake.safe.item"
    query_file.write_text(f"SELECT id FROM {table} WHERE id > 1 AND id < 99 LIMIT {limit}")
    request = SqlQueryProfileRequest(adapter=adapter, source_id="fictional", entity="item", query_file=query_file)
    if limit not in {"1", "10", "1000"}:
        with pytest.raises(SqlQuerySourceError, match="LIMIT"):
            inspect_query_source(request)
        return
    result = authorize_query_source(inspect_query_source(request), (QuerySourceColumn("id", "bigint", False),))
    assert result.sql.endswith(f"LIMIT {limit}")


def test_parquet_cli_profile_to_spec(tmp_path: Path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    source = tmp_path / "fictional.parquet"
    pq.write_table(pa.table({"quantity": [1, None, 3]}), source)
    profile = tmp_path / "profile.json"
    spec = tmp_path / "spec.json"
    assert main(["profile-parquet", str(source), "--output", str(profile)]) == 0
    assert main(["infer-spec", str(profile), "--output", str(spec)]) == 0
    loaded = DatasetSpec.model_validate_json(spec.read_text())
    assert loaded.entities[0].field("quantity").data_type == "integer"
    assert main(["profile-parquet", str(source), "--output", str(source)]) == 2


def test_help_infer_example_uses_profile_json(capsys):
    with pytest.raises(SystemExit) as caught:
        main(["--help"])
    assert caught.value.code == 0
    output = capsys.readouterr().out
    assert "infer-spec out/profile.json" in output
    assert "infer-spec data.csv" not in output


@pytest.mark.parametrize("fields", [("customer_id", "product_id"), ("id", "id")])
def test_overlapping_unrelated_identifiers_are_not_inferred(tmp_path, fields):
    from test_data_agent.profiling import profile_example_folder
    for entity, field in zip(("customer", "product"), fields, strict=True):
        (tmp_path / f"{entity}.csv").write_text(f"{field}\n1\n2\n3\n")
    profile = profile_example_folder(tmp_path, cache_dir=None)
    assert profile.relationships == []


def test_ambiguous_parent_domains_require_explicit_binding(tmp_path):
    from test_data_agent.profiling import profile_example_folder
    for entity in ("product", "archive"):
        (tmp_path / f"{entity}.csv").write_text("product_id\n1\n2\n3\n")
    (tmp_path / "deal.csv").write_text("deal_id,product_id\n10,1\n11,1\n12,2\n13,3\n")
    profile = profile_example_folder(tmp_path, cache_dir=None)
    assert not any(r.child_entity == "deal" for r in profile.relationships)


def test_old_relationship_cache_is_reprofiled(tmp_path):
    import json
    from test_data_agent.profiling import profile_example_folder
    from test_data_agent.profiling.cache import PROFILE_CACHE_FORMAT_VERSION
    source = tmp_path / "input"
    source.mkdir()
    (source / "customer.csv").write_text("customer_id\n1\n2\n3\n")
    (source / "product.csv").write_text("product_id\n1\n2\n3\n")
    cache = tmp_path / "cache"
    profile_example_folder(source, cache_dir=cache)
    path = next(cache.glob("*.json"))
    payload = json.loads(path.read_text())
    payload["format_version"] = PROFILE_CACHE_FORMAT_VERSION - 1
    payload["profile"]["relationships"] = [{"parent_entity": "customer",
        "parent_field": "customer_id", "child_entity": "product", "child_field": "product_id", "confidence": 1}]
    path.write_text(json.dumps(payload))
    assert profile_example_folder(source, cache_dir=cache).relationships == []
    assert json.loads(path.read_text())["format_version"] == PROFILE_CACHE_FORMAT_VERSION
