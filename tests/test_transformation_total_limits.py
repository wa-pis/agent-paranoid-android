"""Transformation total limits remain separate from source-free defaults."""

import pytest

from test_data_agent.core.transformation_limits import (
    InputDimension, TransformationInputLimits, TransformationLimitError, resolve_input_limit,
)


@pytest.mark.parametrize("run_cap", [None, 8192])
def test_policy_parser_uses_admitted_bootstrap_budget(tmp_path, monkeypatch, run_cap):
    from test_data_agent.core.limits import GenerationBudget
    from test_data_agent.io import transformation_source as source

    monkeypatch.setenv("TEST_DATA_AGENT_TRANSFORM_MAX_TOTAL_INPUT_BYTES", "1073741824")
    (tmp_path / "policy.yaml").write_bytes(b"schema_version: '0.1'\nfields: []\n")
    original = source.load_behavior_policy_yaml
    observed = []

    def observe(payload, *, max_bytes, budget):
        observed.append(max_bytes)
        return original(payload, max_bytes=max_bytes, budget=budget)

    # Unit instrumentation only: real parser still enforces validation.
    monkeypatch.setattr(source, "load_behavior_policy_yaml", observe)
    with pytest.raises(source.TransformationSourceError):
        source.prepare_csv_review_from_paths(tmp_path / "missing.csv", "items", tmp_path,
            "policy.yaml", max_total_bytes=run_cap, max_review_bytes=4096,
            budget=GenerationBudget(5))
    assert observed == [1073741824 if run_cap is None else run_cap]

def test_total_snapshot_limit_configuration_and_diagnostic():
    profile = TransformationInputLimits(max_total_input_bytes=4096)
    effective = resolve_input_limit(InputDimension.TOTAL_BYTES, profile, {})
    assert (effective.value, effective.origin) == (4096, "profile")
    session = {"TEST_DATA_AGENT_TRANSFORM_MAX_TOTAL_INPUT_BYTES": "8192"}
    effective = resolve_input_limit(InputDimension.TOTAL_BYTES, profile, session)
    assert (effective.value, effective.origin) == (8192, "session")
    effective.check(8192)
    with pytest.raises(TransformationLimitError) as error:
        effective.check(8193)
    assert error.value.unit == "bytes"
    assert error.value.code == "limit_exceeded"
    assert "resource_limits.max_total_input_bytes" in str(error.value)
    assert "TEST_DATA_AGENT_TRANSFORM_MAX_TOTAL_INPUT_BYTES" in str(error.value)
    with pytest.raises(TransformationLimitError) as requested:
        effective.check(8193, requested=True)
    assert requested.value.code == "requested_above_limit"


def test_total_snapshot_default_and_legacy_session_are_explicit():
    default = resolve_input_limit(InputDimension.TOTAL_BYTES, None, {})
    assert (default.value, default.origin) == (512 * 1024 * 1024, "default")
    legacy = resolve_input_limit(InputDimension.TOTAL_BYTES, None,
        {"TEST_DATA_AGENT_MAX_TOTAL_INPUT_BYTES": "1024"})
    assert (legacy.value, legacy.origin) == (1024, "legacy_session")


@pytest.mark.parametrize("reader", ["mapping", "source"])
def test_cumulative_reader_total_boundary_preserves_typed_error(tmp_path, reader):
    from test_data_agent.core.limits import GenerationBudget
    from test_data_agent.io.mapping_snapshot import read_mapping_snapshot
    from test_data_agent.io.transformation_source import load_csv_source_snapshot

    (tmp_path / "fixture.csv").write_bytes(b"a\nfiction")
    effective = resolve_input_limit(InputDimension.TOTAL_BYTES,
        TransformationInputLimits(max_total_input_bytes=11), {})

    def read(offset):
        arguments = {"max_bytes": 16, "budget": GenerationBudget(5),
            "total_limit": effective, "consumed_bytes": offset}
        if reader == "mapping":
            return read_mapping_snapshot(tmp_path, "fixture.csv", **arguments)
        return load_csv_source_snapshot(tmp_path / "fixture.csv", "items", **arguments)

    assert read(2).payload == b"a\nfiction"
    with pytest.raises(TransformationLimitError) as error:
        read(3)
    assert (error.value.amount, error.value.limit, error.value.origin) == (12, 11, "profile")
    assert "fiction" not in str(error.value)


@pytest.mark.parametrize("reader", ["mapping", "source"])
def test_no_remaining_bytes_is_typed_exhaustion(tmp_path, reader):
    from test_data_agent.core.limits import GenerationBudget
    from test_data_agent.io.mapping_snapshot import read_mapping_snapshot
    from test_data_agent.io.transformation_source import load_csv_source_snapshot

    (tmp_path / "fixture.csv").write_bytes(b"x")
    effective = resolve_input_limit(InputDimension.TOTAL_BYTES,
        TransformationInputLimits(max_total_input_bytes=11), {})
    arguments = {"max_bytes": 0, "budget": GenerationBudget(5),
        "total_limit": effective, "consumed_bytes": 11}
    with pytest.raises(TransformationLimitError) as error:
        if reader == "mapping":
            read_mapping_snapshot(tmp_path, "fixture.csv", **arguments)
        else:
            load_csv_source_snapshot(tmp_path / "fixture.csv", "items", **arguments)
    assert (error.value.amount, error.value.limit) == (12, 11)
