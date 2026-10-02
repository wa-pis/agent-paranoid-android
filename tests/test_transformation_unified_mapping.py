"""Fictional local mappings only; no production inputs or external access."""

import io
import json
from dataclasses import replace

import pytest
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
from test_data_agent.io.transformation_execute import replace_csv_snapshot
from test_data_agent.io.transformation_output import normalized_output_rows
from test_data_agent.io.transformation_source import _profile_transformation_csv, prepare_csv_review_request


@pytest.mark.parametrize("action", ["substitute", "replace_text"])
@pytest.mark.parametrize("output_format", ["csv", "postgresql_sql", "parquet"])
def test_mapped_fictional_email_permutation_across_outputs(action, output_format):
    originals = ("aster@example.invalid", "birch@example.invalid")
    source = SnapshotPart("source", "items", ("email\n" + "\n".join(originals) + "\n").encode())
    profile = _profile_transformation_csv(source, null_token=None,
        budget=GenerationBudget(5), max_bytes=16384)
    declaration = {"kind": "csv", "path": "map.csv",
                   "source_columns": ["old"], "replacement_columns": ["new"]}
    policy = {"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile),
        "fields": [{"entity": "items", "field": "email", "sensitivity": "sensitive",
                    "behavior": {"action": action}}]}
    references = ()
    if action == "substitute":
        policy["fields"][0]["behavior"]["mapping"] = {"kind": "inline", "entries": [
            {"original": [originals[0]], "replacement": [originals[1]]},
            {"original": [originals[1]], "replacement": [originals[0]]}]}
    else:
        policy["file_text_mapping"] = declaration
        references = (SnapshotPart("mapping", "map.csv",
            f"old,new\n{originals[0]},{originals[1]}\n{originals[1]},{originals[0]}\n".encode()),)
    if output_format != "csv":
        policy["output"] = {"format": output_format,
            "fields": [{"name": "email", "type": "string"}]}
        if output_format == "postgresql_sql":
            policy["output"]["table"] = "items"
    policy_bytes = yaml.safe_dump(policy).encode()
    material = prepare_csv_review_request(policy_bytes, source, references,
        max_total_bytes=16384, max_review_bytes=4096, budget=GenerationBudget(5))
    review = json.loads(material.review)["fields"][0]
    assert review["observed_sensitivity"] == "sensitive"
    assert review["system_comment"]
    assert not review["preserves_original"]
    assert all(value.encode() not in material.review for value in originals)
    result = replace_csv_snapshot(material, max_total_bytes=16384, max_review_bytes=4096,
        max_output_bytes=16384, budget=GenerationBudget(5))
    assert result.rows == ((originals[1],), (originals[0],))
    assert result.mapped_cells == (b"\x01", b"\x01")
    assert all(value not in repr(result) for value in originals)
    if output_format == "csv":
        assert result.csv_bytes == f"email\n{originals[1]}\n{originals[0]}\n".encode()
        return
    output = load_behavior_policy_yaml(policy_bytes, max_bytes=16384, budget=GenerationBudget(5)).output
    assert output is not None
    # No mapped execution evidence: the legacy private result stays fail-closed.
    with pytest.raises(ValueError, match="sensitive normalized"):
        list(normalized_output_rows(replace(result, mapped_cells=()), output, budget=GenerationBudget(5)))
    with pytest.raises(ValueError, match="mapped-cell execution evidence"):
        list(normalized_output_rows(replace(result, mapped_cells=(b"\x02", b"\x01")),
            output, budget=GenerationBudget(5)))
    source_rows = iter((value,) for value in originals)
    if output_format == "postgresql_sql":
        from test_data_agent.io.transformation_sql import render_transformation_sql
        payload = render_transformation_sql(result, output, max_bytes=16384,
            budget=GenerationBudget(5), source_rows=source_rows)
        assert f"VALUES ('{originals[1]}');".encode() in payload
        assert f"VALUES ('{originals[0]}');".encode() in payload
    else:
        pq = pytest.importorskip("pyarrow.parquet")
        from test_data_agent.io.transformation_parquet import render_transformation_parquet
        payload = render_transformation_parquet(result, output, max_bytes=16384,
            budget=GenerationBudget(5), source_rows=source_rows)
        assert pq.read_table(io.BytesIO(payload)).column("email").to_pylist() == list(reversed(originals))
