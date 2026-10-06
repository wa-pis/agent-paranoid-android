"""Synthetic regressions for the shared CSV structural boundary."""
import pytest

from test_data_agent.core.csv_reader import ScopedDictReader
from test_data_agent.core.limits import InputLimitError


@pytest.mark.parametrize("extra", [1, 99])
def test_surplus_cells_rejected_before_row_return(extra):
    reader = ScopedDictReader(["key\n", ",".join(["fictional_marker"] * (extra + 1)) + "\n"])
    with pytest.raises(InputLimitError) as caught:
        next(reader)
    assert str(caught.value) == "CSV row exceeds header width"
    assert "fictional_marker" not in str(caught.value)


def test_missing_quoted_and_blank_cells_remain_supported():
    reader = ScopedDictReader(["a,b\n", "\n", '"fictional,value",x\n', "one\n"])
    assert list(reader) == [{"a": "fictional,value", "b": "x"}, {"a": "one", "b": None}]


def test_explicit_restkey_header_collision_is_compatible():
    reader = ScopedDictReader(["a,overflow\n", "x,y\n"])
    reader.restkey = "overflow"
    assert list(reader) == [
        {"a": "x", "overflow": "y"}]
    with pytest.raises(InputLimitError):
        reader = ScopedDictReader(["a,overflow\n", "x,y,z\n"])
        reader.restkey = "overflow"
        list(reader)


@pytest.mark.parametrize("route", ["dataset", "single", "folder", "snapshot"])
def test_public_routes_reject_width_under_small_budgets(tmp_path, monkeypatch, route):
    from test_data_agent.csv_profiler import profile_csv, profile_csv_with_row_digests
    from test_data_agent.io.readers import load_dataset_rows
    from test_data_agent.profiling import profile_example_folder

    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_COLUMNS", "2")
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELLS", "2")
    path = tmp_path / "items.csv"
    path.write_text("key\n" + ",".join(["fictional_marker"] * 100) + "\n")
    with pytest.raises(InputLimitError) as caught:
        if route == "dataset":
            load_dataset_rows(tmp_path)
        elif route == "single":
            profile_csv(path)
        elif route == "snapshot":
            profile_csv_with_row_digests(path)
        else:
            profile_example_folder(tmp_path, use_cache=False)
    assert "fictional_marker" not in str(caught.value)
