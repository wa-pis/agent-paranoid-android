"""Reject decimal text amplification before formatting or publishing a dataset."""

from decimal import Decimal

import pytest

from test_data_agent.core.decimal_units import value_matches_decimal
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.io.csv_encoding import encode_csv_cell
from test_data_agent.io.parquet_encoding import encode_scalar
from test_data_agent.io.writers import json_decimal, sql_literal, write_parquet
from test_data_agent.postgres_sql_export import postgres_literal


UNBOUNDED = (
    "1E+1000000000", "-1E+1000000000", "1E-1000000000", "-1E-1000000000",
    "0E+1000000000", "NaN", "sNaN", "Infinity", "-Infinity",
)


@pytest.fixture
def forbid_fixed_formatting(monkeypatch):
    def unexpected_format(*args):
        pytest.fail("unbounded decimal reached fixed-point formatting")

    for module in (
        "test_data_agent.core.decimal_units",
        "test_data_agent.io.csv_encoding",
        "test_data_agent.io.parquet_encoding",
        "test_data_agent.io.writers",
        "test_data_agent.postgres_sql_export",
    ):
        monkeypatch.setattr(module + ".format", unexpected_format, raising=False)


@pytest.mark.parametrize("text", UNBOUNDED)
@pytest.mark.parametrize("serialize", [encode_csv_cell, encode_scalar, json_decimal, sql_literal])
def test_scalar_serializers_bound_decimal_expansion(forbid_fixed_formatting, serialize, text):
    with pytest.raises((ValueError, TypeError)) as error:
        serialize(Decimal(text))
    assert text not in str(error.value)


@pytest.mark.parametrize("text", UNBOUNDED)
def test_decimal_validation_rejects_without_expanding(forbid_fixed_formatting, text):
    assert not value_matches_decimal(Decimal(text), precision=38, scale=38)


@pytest.mark.parametrize("text", UNBOUNDED)
def test_postgres_decimal_rejects_without_expanding(forbid_fixed_formatting, text):
    with pytest.raises(ValueError, match="PostgreSQL decimal value is invalid") as error:
        postgres_literal(Decimal(text), FieldType.DECIMAL, precision=38, scale=38)
    assert text not in str(error.value)


@pytest.mark.parametrize("allow_invalid", [False, True])
@pytest.mark.parametrize("text", UNBOUNDED)
def test_parquet_rejects_unbounded_decimal_before_publication(
    tmp_path, forbid_fixed_formatting, allow_invalid, text,
):
    pytest.importorskip("pyarrow")
    field = FieldSpec.model_validate({"name": "amount", "data_type": "decimal",
        "semantic_type": "numeric_measure", "distribution": {
            "kind": "decimal_range", "precision": 2, "scale": 1,
            "min": "0.0", "max": "0.9"}})
    output = tmp_path / "generated.parquet"
    with pytest.raises(ValueError, match="declared field types") as error:
        write_parquet([{"amount": Decimal(text)}], output, fields=[field],
                      allow_invalid=allow_invalid)
    assert text not in str(error.value)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("text", ["1E-38", "-1E-38", "0." + "9" * 38, "-0." + "9" * 38])
def test_supported_decimal_width_is_exact_across_serializers(text):
    import json

    value = Decimal(text)
    expected = format(value, "f")
    assert encode_csv_cell(value) == json_decimal(value) == sql_literal(value) == expected
    assert json.loads(encode_scalar(value)) == expected
    assert postgres_literal(value, FieldType.DECIMAL, precision=38, scale=38) == expected
    assert value_matches_decimal(value, precision=38, scale=38)
