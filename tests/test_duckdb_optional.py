"""The base installation stays lightweight and fails closed at crossover."""

import builtins
from pathlib import Path
import traceback

import pytest

from test_data_agent.profiling import profile_example_folder
from test_data_agent.profiling import schema_profiler
from test_data_agent.profiling.duckdb_distinct import DistinctTrackingError


@pytest.mark.parametrize("failure", [ImportError, RuntimeError])
def test_optional_import_failure_is_redacted_and_does_not_publish_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: type[Exception],
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "items.csv").write_text("id\n1\n2\n")
    cache = tmp_path / "cache"
    real_import = builtins.__import__

    def without_duckdb(name, *args, **kwargs):
        if name == "duckdb":
            raise failure("fictional-secret-loader-path")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_duckdb)
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 1)
    with pytest.raises(DistinctTrackingError) as caught:
        profile_example_folder(source, cache_dir=cache)

    assert caught.value.__context__ is None
    assert "fictional-secret-loader-path" not in "".join(traceback.format_exception(caught.value))
    if failure is ImportError:
        assert "agent-paranoid-android[profiling]" in str(caught.value)
    assert not cache.exists()


def test_large_low_cardinality_profile_does_not_load_duckdb(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "items.csv").write_text("id,status\n" + "A,active\n" * 1_001)
    real_import = builtins.__import__

    def without_engines(name, *args, **kwargs):
        if name in {"duckdb", "pyarrow"}:
            raise AssertionError("small distinct state must not import optional engines")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_engines)
    monkeypatch.setattr(schema_profiler, "MAX_IN_MEMORY_DISTINCT", 2)

    profile = profile_example_folder(tmp_path, cache_dir=None)

    assert profile.entities[0].row_count == 1_001
    assert profile.entities[0].fields[0].distribution["pool_size"] == 1
