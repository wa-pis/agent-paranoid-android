"""Reviewed synthetic DECIMAL replacements never declassify source CSV values."""
import pytest

from test_data_agent.csv_profiler import CSVColumnAccumulator, profile_column
from test_data_agent.profiling.schema_profiler import FieldAccumulator
from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.entity import EntityProfile
from test_data_agent.core.field import FieldSpec
from test_data_agent.csv_profiler import CSVProfile
from test_data_agent.generation import generate_dataset, infer_dataset_spec


def reviewed():
    return FieldSpec(name="quantity", data_type="decimal", semantic_type="numeric_measure",
        distribution={"kind": "decimal_range", "precision": 8, "scale": 3, "min": "1.001", "max": "2.002"})


@pytest.mark.parametrize("route", ["column", "single", "folder", "schema_column"])
def test_reviewed_numeric_replacement_retains_source_sensitivity(route):
    values = ["2468.125", "3579.625"]
    if route == "schema_column":
        from test_data_agent.profiling.schema_profiler import profile_field
        field = profile_field("quantity", values, 2)
    elif route == "column":
        field = profile_column("quantity", values, 2)
    else:
        accumulator = CSVColumnAccumulator("quantity") if route == "single" else FieldAccumulator("quantity")
        for value in values:
            accumulator.add(value)
        field = accumulator.to_profile(2)
    assert field.sensitive and field.semantic_type == "phone"
    assert field.numeric_storage_type == "float"
    if route in {"folder", "schema_column"}:
        profile = DatasetProfile(entities=[EntityProfile(name="events", row_count=2, fields=[field])])
    else:
        profile = csv_profile_to_dataset_profile(CSVProfile(table="events", row_count=2, columns=[field]))
    before = profile.model_dump_json()
    spec = infer_dataset_spec(profile, count=10, decimal_fields={"events.quantity": reviewed()})
    assert profile.model_dump_json() == before
    assert all(value not in before for value in values)
    assert spec.entities[0].fields[0] == reviewed()
    rows = generate_dataset(spec, seed=7)
    assert rows == generate_dataset(spec, seed=7)
    assert all(row["quantity"] not in values for row in rows["events"])


@pytest.mark.parametrize("values", [
    ["2468.125", "+1 (555) 010-0117"],
    ["2468.125", "api_key=fictional_not_a_real_credential"],
    ["2468.125", "4111111111111111"],
    ["2468.125", "NaN"], ["2468.125", "Infinity"],
    ["2468.125", "1e1000000000"], ["2468.125", "not-a-number"],
])
@pytest.mark.parametrize("route", ["single", "folder"])
def test_late_bad_values_cannot_authorize_numeric_replacement(values, route):
    accumulator = CSVColumnAccumulator("quantity") if route == "single" else FieldAccumulator("quantity")
    actual = [values[0]] * 105 + [values[1]]
    for value in actual:
        accumulator.add(value)
    field = accumulator.to_profile(len(actual))
    assert field.numeric_storage_type is None
    if route == "folder":
        profile = DatasetProfile(entities=[EntityProfile(name="events", row_count=len(actual), fields=[field])])
    else:
        profile = csv_profile_to_dataset_profile(CSVProfile(table="events", row_count=len(actual), columns=[field]))
    with pytest.raises(ValueError):
        infer_dataset_spec(profile, decimal_fields={"events.quantity": reviewed()})
    assert values[1] not in profile.model_dump_json()


@pytest.mark.parametrize("name", ["phone", "customer_id", "postal_code", "quantity_id"])
def test_explicit_names_and_identifier_protections_veto_replacement(name):
    field = profile_column(name, ["2468.125", "3579.625"], 2)
    profile = csv_profile_to_dataset_profile(CSVProfile(table="events", row_count=2, columns=[field]))
    override = reviewed().model_copy(update={"name": name})
    with pytest.raises(ValueError):
        infer_dataset_spec(profile, decimal_fields={f"events.{name}": override})


def test_old_profile_without_storage_evidence_requires_reprofiling():
    from test_data_agent.core.field import FieldProfile
    profile = DatasetProfile(entities=[EntityProfile(name="events", row_count=2,
        fields=[FieldProfile(name="quantity", data_type="string", sensitive=True, semantic_type="phone")])])
    with pytest.raises(ValueError, match="reprofile"):
        infer_dataset_spec(profile, decimal_fields={"events.quantity": reviewed()})


def test_plain_decimal_range_without_numeric_measure_is_not_a_csv_replacement():
    field = profile_column("quantity", ["2468.125", "3579.625"], 2)
    profile = csv_profile_to_dataset_profile(CSVProfile(table="events", row_count=2, columns=[field]))
    with pytest.raises(ValueError, match="numeric_measure"):
        infer_dataset_spec(profile, decimal_fields={"events.quantity": reviewed().model_copy(update={"semantic_type": None})})


def test_cli_requires_reviewed_mapping_and_leaves_original_profile_safe(tmp_path):
    import json
    from test_data_agent.cli import main
    from test_data_agent.io.readers import load_dataset_spec

    source = tmp_path / "events.csv"
    source.write_text("quantity\n2468.125\n3579.625\n")
    profile_path = tmp_path / "profile.json"
    output = tmp_path / "spec.yaml"
    mapping = tmp_path / "reviewed.json"
    mapping.write_text(json.dumps({"events.quantity": reviewed().model_dump(mode="json")}))
    assert main(["profile-csv", str(source), "--output", str(profile_path)]) == 0
    before = profile_path.read_bytes()
    assert main(["infer-spec", str(profile_path), "--output", str(output),
                 "--decimal-fields", str(mapping)]) == 0
    assert load_dataset_spec(output).entity("events").field("quantity") == reviewed()
    assert profile_path.read_bytes() == before
    assert b"2468.125" not in before and b"3579.625" not in before
    invalid = reviewed().model_dump(mode="json")
    invalid["semantic_type"] = None
    mapping.write_text(json.dumps({"events.quantity": invalid}))
    previous = output.read_bytes()
    assert main(["infer-spec", str(profile_path), "--output", str(output),
                 "--decimal-fields", str(mapping), "--overwrite"]) != 0
    assert output.read_bytes() == previous


def test_storage_evidence_changes_profile_fingerprint_but_does_not_declassify_advisor():
    from test_data_agent.advisor import build_advisor_request
    from test_data_agent.core.fingerprints import model_fingerprint as dataset_profile_fingerprint

    field = profile_column("quantity", ["2468.125", "3579.625"], 2)
    profile = csv_profile_to_dataset_profile(CSVProfile(table="events", row_count=2, columns=[field]))
    legacy = profile.model_copy(deep=True)
    legacy.entities[0].fields[0].numeric_storage_type = None
    assert "numeric_storage_type" not in legacy.model_dump_json()
    assert dataset_profile_fingerprint(profile) != dataset_profile_fingerprint(legacy)
    assert dataset_profile_fingerprint(profile) == dataset_profile_fingerprint(
        DatasetProfile.model_validate_json(profile.model_dump_json()))
    request = build_advisor_request(profile)
    assert request.baseline_spec.entity("events").field("quantity").sensitive
    assert request.baseline_spec.entity("events").field("quantity").semantic_type == "phone"
    assert all(value not in request.model_dump_json() for value in ["2468.125", "3579.625"])


@pytest.mark.parametrize("protected", ["primary_key", "relationship"])
def test_reviewed_numeric_replacement_cannot_replace_existing_key_bindings(protected):
    from test_data_agent.core.relationship import Relationship
    field = profile_column("quantity", ["2468.125", "3579.625"], 2)
    profile = csv_profile_to_dataset_profile(CSVProfile(table="events", row_count=2, columns=[field]))
    if protected == "primary_key":
        profile.entities[0].primary_key_candidates = ["quantity"]
    else:
        profile.relationships = [Relationship(parent_entity="events", parent_field="quantity",
            child_entity="events", child_field="quantity", confidence=1.0)]
    with pytest.raises(ValueError, match="eligible CSV"):
        infer_dataset_spec(profile, decimal_fields={"events.quantity": reviewed()})


def test_cache_v7_is_reprofiled_for_numeric_storage_evidence(tmp_path):
    import json
    from test_data_agent.profiling import profile_example_folder
    from test_data_agent.profiling.cache import PROFILE_CACHE_FORMAT_VERSION

    source = tmp_path / "source"
    source.mkdir()
    (source / "events.csv").write_text("quantity\n2468.125\n3579.625\n")
    cache = tmp_path / "cache"
    first = profile_example_folder(source, cache_dir=cache)
    assert first.entity("events").field("quantity").numeric_storage_type == "float"
    path = next(cache.glob("*.json"))
    payload = json.loads(path.read_text())
    payload["format_version"] = 7
    payload["profile"]["entities"][0]["fields"][0].pop("numeric_storage_type")
    path.write_text(json.dumps(payload))
    fresh = profile_example_folder(source, cache_dir=cache)
    assert fresh.entity("events").field("quantity").numeric_storage_type == "float"
    assert json.loads(path.read_text())["format_version"] == PROFILE_CACHE_FORMAT_VERSION == 8
    assert "2468.125" not in path.read_text() and "3579.625" not in path.read_text()


def test_reviewed_csv_numeric_agent_flow_requires_changed_spec_approval(tmp_path, capsys):
    import json
    from test_data_agent.cli import main
    from test_data_agent.io.readers import load_dataset_spec
    from test_data_agent.core.fingerprints import model_fingerprint

    source = tmp_path / "events.csv"
    source.write_text("quantity\n2468.125\n3579.625\n")
    workspace = tmp_path / "agent"
    assert main(["agent-plan", str(source), "--workspace", str(workspace), "--count", "4"]) == 0
    profile_before = (workspace / "profile.json").read_bytes()
    spec_path = workspace / "dataset_spec.yaml"
    planned_spec = load_dataset_spec(spec_path)
    old_sha = model_fingerprint(planned_spec)
    mapping = tmp_path / "reviewed.json"
    mapping.write_text(json.dumps({"events.quantity": reviewed().model_dump(mode="json")}))
    assert main(["infer-spec", str(workspace / "profile.json"), "--output", str(tmp_path / "numeric.yaml"),
        "--count", "4", "--decimal-fields", str(mapping)]) == 0
    from test_data_agent.io.artifacts import write_dataset_spec_artifact
    planned_spec.entity("events").fields[0] = load_dataset_spec(
        tmp_path / "numeric.yaml").entity("events").field("quantity")
    write_dataset_spec_artifact(planned_spec, spec_path)
    new_sha = model_fingerprint(load_dataset_spec(spec_path))
    assert old_sha != new_sha
    assert main(["agent-approve", str(workspace), "--reviewed-spec-sha256", old_sha]) != 0
    assert not (workspace / "generated").exists()
    capsys.readouterr()
    assert main(["agent-review", str(workspace), "--json"]) == 0
    assert new_sha in capsys.readouterr().out
    assert main(["agent-approve", str(workspace), "--reviewed-spec-sha256", new_sha]) == 0
    assert (workspace / "profile.json").read_bytes() == profile_before
    manifest = json.loads((workspace / "generated" / "generation_manifest.json").read_text())
    assert manifest["synthetic"] and manifest["source_rows_copied"] is False
    assert (workspace / "approval_receipt.json").is_file()


def test_provider_projection_keeps_phone_and_rejects_unreviewed_declassification():
    import json
    from test_data_agent.advisor import AdvisorContractError, build_advisor_request
    from test_data_agent.providers.category_privacy import _provider_safe_request

    field = profile_column("quantity", ["2468.125", "3579.625"], 2)
    profile = csv_profile_to_dataset_profile(CSVProfile(table="events", row_count=2, columns=[field]))
    payload, _ = _provider_safe_request(build_advisor_request(profile))
    exported_field = payload["profile"]["entities"][0]["fields"][0]
    assert exported_field["sensitive"] and exported_field["semantic_type"] == "phone"
    assert exported_field["numeric_storage_type"] == "float"
    assert "2468.125" not in json.dumps(payload) and "3579.625" not in json.dumps(payload)
    numeric_spec = infer_dataset_spec(profile, decimal_fields={"events.quantity": reviewed()})
    with pytest.raises(AdvisorContractError, match="cannot weaken sensitive"):
        build_advisor_request(profile, baseline_spec=numeric_spec)


@pytest.mark.parametrize("values", [["1", "2"], ["-1.5", "-2.25"], ["2.468125e3", "3.579625e3"]])
def test_numeric_storage_and_authored_range_do_not_depend_on_phone_punctuation(values):
    field = profile_column("quantity", values, 2)
    profile = csv_profile_to_dataset_profile(CSVProfile(table="events", row_count=2, columns=[field]))
    spec = infer_dataset_spec(profile, decimal_fields={"events.quantity": reviewed()})
    assert spec.entity("events").field("quantity") == reviewed()


def test_sql_profile_cannot_use_csv_numeric_replacement_authority():
    field = profile_column("quantity", ["2468.125", "3579.625"], 2)
    profile = csv_profile_to_dataset_profile(CSVProfile(table="events", row_count=2, columns=[field]))
    profile.source_type = "postgres"
    with pytest.raises(ValueError, match="eligible CSV"):
        infer_dataset_spec(profile, decimal_fields={"events.quantity": reviewed()})


@pytest.mark.parametrize("semantic", ["email", "ssn", "identifier", "quasi_identifier", "secret"])
def test_protected_semantics_veto_even_without_sensitivity_boolean(semantic):
    from test_data_agent.core.field import FieldProfile
    profile = DatasetProfile(entities=[EntityProfile(name="events", row_count=2,
        fields=[FieldProfile(name="quantity", data_type="float", semantic_type=semantic)])])
    with pytest.raises(ValueError):
        infer_dataset_spec(profile, decimal_fields={"events.quantity": reviewed()})
