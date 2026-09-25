from contextlib import nullcontext

import pytest

from test_data_agent.core.field import FieldType
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_mapping import MappingDeclarationError, validate_inline_scalar_mapping
from test_data_agent.core.transformation_policy import parse_behavior_policy
from test_data_agent.io.behavior_policy_files import load_behavior_policy_file, save_behavior_policy_file
from test_data_agent.io.mapping_loader import load_csv_mapping


@pytest.mark.parametrize("nullable", [True, False])
@pytest.mark.parametrize("kind,original,replacement,csv_row", [
    (FieldType.STRING, "001", "002", "001,002"),
    (FieldType.STRING, "", None, ",NULL"),
    (FieldType.INTEGER, 9007199254740993, 9007199254740995,
     "9007199254740993,9007199254740995"),
    (FieldType.DATE, "2024-02-29", "2025-03-01", "2024-02-29,2025-03-01"),
    (FieldType.DATE, "2025-02-29", "2025-03-01", "2025-02-29,2025-03-01"),
    (FieldType.DATETIME, "2025-04-30T12:34:56+03:00", "2026-09-23T09:34:56Z",
     "2025-04-30T12:34:56+03:00,2026-09-23T09:34:56Z"),
    (FieldType.DATETIME, "2025-04-30 12:34:56+03:00", "2026-09-23T09:34:56Z",
     "2025-04-30 12:34:56+03:00,2026-09-23T09:34:56Z"),
])
def test_saved_inline_and_csv_policies_have_equal_typed_mappings(
    tmp_path, kind, original, replacement, csv_row, nullable,
):
    root = tmp_path.resolve()
    (root / "mapping.csv").write_text("old,new\n" + csv_row + "\n", encoding="utf-8")
    mappings = [
        {"kind": "inline", "entries": [{"original": [original], "replacement": [replacement]}]},
        {"kind": "csv", "path": "mapping.csv", "source_columns": ["old"],
         "replacement_columns": ["new"]},
    ]
    results = []
    rejected = (replacement is None and not nullable) or original in {
        "2025-02-29", "2025-04-30 12:34:56+03:00",
    }
    budget = GenerationBudget()
    for index, mapping in enumerate(mappings):
        policy = parse_behavior_policy({
            "schema_version": "0.1", "schema_fingerprint": "a" * 64, "seed": 7,
            "fields": [{"entity": "fictional", "field": "value", "sensitivity": "unknown",
                        "behavior": {"action": "substitute", "mapping": mapping}}],
        })
        name = f"policy-{index}.yaml"
        save_behavior_policy_file(root, name, policy, max_bytes=10000, budget=budget)
        restored = load_behavior_policy_file(root, name, max_bytes=10000, budget=budget)
        assert restored == policy
        declared = restored.fields[0].behavior.mapping
        with pytest.raises(MappingDeclarationError) if rejected else nullcontext():
            if index == 0:
                result = validate_inline_scalar_mapping(declared, data_types=(kind,), nullable=(nullable,))
            else:
                result = load_csv_mapping(
                    root, declared, data_types=(kind,), nullable=(nullable,), encoding="utf-8",
                    delimiter=",", null_token="NULL", max_bytes=1000, max_rows=10,
                    max_cells=20, max_columns=2, max_cell_chars=100, budget=budget,
                ).mapping
            results.append(result)
    if rejected:
        assert not results
        return
    assert results[0] == results[1]
    assert results[0].entries[0].original == (original,)
    assert results[0].entries[0].replacement == (replacement,)
