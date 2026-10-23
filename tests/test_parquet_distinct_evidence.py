"""Bounded source-free Parquet distinctness uses the existing inspection scan."""
from types import SimpleNamespace
from decimal import Decimal

import pytest

from test_data_agent.adapters import parquet_dataset as adapter

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")


@pytest.mark.parametrize("values,ratio", [
    ([1, 1, None, 2], 2 / 3),
    ([None, None], 0.0),
    ([], 0.0),
    ([-0.0, 0.0, 1.0], 2 / 3),
    ([Decimal("1.10"), Decimal("1.10"), Decimal("2.20")], 2 / 3),
    (["fictional-alpha", "fictional-alpha", "fictional-beta"], 2 / 3),
])
def test_complete_scalar_scan_has_exact_nonnull_distinctness(tmp_path, values, ratio):
    path = tmp_path / "fictional.parquet"
    pq.write_table(pa.table({"measure": values}), path, row_group_size=2)
    profile = adapter.parquet_file_to_dataset_profile(path)
    field = profile.entities[0].field("measure")
    assert field.unique_ratio == ratio
    assert field.unique_ratio_kind == "exact"
    assert profile.entities[0].primary_key_candidates == []
    assert "fictional-alpha" not in profile.model_dump_json()


def test_cap_reports_lower_bound_and_never_creates_identifier_pool(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "MAX_PARQUET_DISTINCT_DIGESTS", 2)
    path = tmp_path / "fictional.parquet"
    pq.write_table(pa.table({"run_id": [1, 2, 3, None, 4]}), path)
    profile = adapter.parquet_file_to_dataset_profile(path)
    field = profile.entities[0].field("run_id")
    assert field.unique_ratio == 0.5
    assert field.unique_ratio_kind == "lower_bound"
    assert "pool_size" not in field.distribution
    assert profile.entities[0].primary_key_candidates == []


def test_repeated_values_at_cap_remain_exact(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "MAX_PARQUET_DISTINCT_DIGESTS", 2)
    path = tmp_path / "fictional.parquet"
    pq.write_table(pa.table({"measure": [1, 2, 1, 2]}), path)
    field = adapter.parquet_file_to_dataset_profile(path).entities[0].field("measure")
    assert field.unique_ratio == 0.5
    assert field.unique_ratio_kind == "exact"


@pytest.mark.parametrize("values", [[b"fictional"], [[1, 2]], [{"a": 1}], [float("nan")], [float("inf")]])
def test_unsupported_distinctness_stays_unknown(tmp_path, values):
    path = tmp_path / "fictional.parquet"
    pq.write_table(pa.table({"measure": values}), path)
    field = adapter.parquet_file_to_dataset_profile(path).entities[0].field("measure")
    assert field.unique_ratio is None
    assert field.unique_ratio_kind == "unspecified"


@pytest.mark.parametrize("count", [None, -1, 3, True, 1.5])
def test_malformed_null_statistics_remain_unknown(count):
    column = SimpleNamespace(path_in_schema="measure",
        statistics=SimpleNamespace(has_null_count=True, null_count=count))
    group = SimpleNamespace(num_rows=2, column=lambda index: column)
    metadata = SimpleNamespace(num_columns=1, num_row_groups=1, num_rows=2,
        row_group=lambda index: group)
    assert adapter._parquet_null_count(metadata, 0, "measure") is None


def test_inspection_keeps_only_capped_digests(tmp_path):
    value = "fictional.person@example.invalid"
    path = tmp_path / "fictional.parquet"
    pq.write_table(pa.table({"note": [value]}), path)
    evidence = adapter._inspect_parquet_columns(pq.ParquetFile(path))
    assert evidence[0].sensitive
    assert all(type(item) is bytes and len(item) == 32 for item in evidence[0].digests)
    assert value not in repr(evidence)
    assert value not in adapter.parquet_file_to_dataset_profile(path).model_dump_json()


def test_cli_profile_matches_direct_evidence_and_excludes_source_values(tmp_path, capsys):
    from test_data_agent.cli import main
    from test_data_agent.core.dataset import DatasetProfile
    from test_data_agent.core.fingerprints import model_fingerprint
    path = tmp_path / "fictional.parquet"
    output = tmp_path / "profile.json"
    value = "fictional.person@example.invalid"
    pq.write_table(pa.table({"note": [value, value, None]}), path)
    direct = adapter.parquet_file_to_dataset_profile(path)
    assert main(["profile-parquet", str(path), "--output", str(output)]) == 0
    saved = DatasetProfile.model_validate_json(output.read_text())
    assert model_fingerprint(saved) == model_fingerprint(direct)
    assert saved.entities[0].field("note").unique_ratio == 0.5
    assert value not in output.read_text() + capsys.readouterr().out


def test_incomplete_scan_cannot_certify_distinctness(tmp_path, monkeypatch):
    from test_data_agent.core.limits import InputLimitError
    path = tmp_path / "fictional.parquet"
    pq.write_table(pa.table({"measure": list(range(300))}), path)
    original = pq.ParquetFile(path)
    class Incomplete:
        def __getattr__(self, name):
            return getattr(original, name)
        def iter_batches(self, **kwargs):
            yield next(original.iter_batches(**kwargs))
    monkeypatch.setattr(pq, "ParquetFile", lambda *args: Incomplete())
    with pytest.raises(InputLimitError, match="row count"):
        adapter.parquet_file_to_dataset_profile(path)


def test_private_scalar_digest_domains_do_not_alias_string_and_integer():
    evidence = adapter._ParquetColumnEvidence(sensitive=False)
    adapter._observe_distinct(evidence, 1)
    adapter._observe_distinct(evidence, "1")
    assert len(evidence.digests) == 2


def test_private_decimal_zero_sign_does_not_inflate_distinctness():
    evidence = adapter._ParquetColumnEvidence(sensitive=False)
    adapter._observe_distinct(evidence, Decimal("0.00"))
    adapter._observe_distinct(evidence, Decimal("-0.00"))
    assert len(evidence.digests) == 1
