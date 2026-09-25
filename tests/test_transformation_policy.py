import copy
import warnings

import pytest

from test_data_agent.core.transformation_policy import BehaviorPolicyError, parse_behavior_policy
from test_data_agent.core.transformation_policy import validate_policy_field_coverage
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint, validate_policy_profile
from test_data_agent.core.transformation_policy import render_policy_review
from test_data_agent.core.dataset import DatasetProfile


def policy(behavior):
    return {"schema_version": "0.1", "schema_fingerprint": "a" * 64, "seed": 7,
            "fields": [{"entity": "items", "field": "value", "sensitivity": "non_sensitive",
                        "behavior": behavior}]}


@pytest.mark.parametrize("behavior", [
    {"action": "preserve", "authorization_ref": "user-review", "comment": "Reviewed business code"},
    {"action": "synthesize", "generation_policy_ref": "amount-rule"},
    {"action": "substitute", "mapping": {"kind": "inline", "entries": [
        {"original": ["fictional-a"], "replacement": ["fictional-b"]}]}},
    {"action": "derive", "expression": "a + b", "dependencies": ["a", "b"]},
    {"action": "drop"},
])
def test_all_actions_roundtrip_privately(behavior):
    result = parse_behavior_policy(policy(behavior))
    assert parse_behavior_policy(result.model_dump(mode="json")) == result
    assert repr(result) == "BehaviorPolicy(schema_version='0.1')"


@pytest.mark.parametrize("change", ["version", "extra", "duplicate", "sensitivity", "missing_auth",
                                    "missing_comment", "blank_comment"])
def test_invalid_policy_is_value_free(change):
    payload = policy({"action": "preserve", "authorization_ref": "fictional-private-marker",
                      "comment": "Reviewed fictional business code"})
    if change == "version":
        payload["schema_version"] = "fictional-private-marker"
    elif change == "extra":
        payload["fields"][0]["behavior"]["mapping"] = {}
    elif change == "duplicate":
        payload["fields"].append(copy.deepcopy(payload["fields"][0]))
    elif change == "sensitivity":
        payload["fields"][0]["sensitivity"] = "sensitive"
    elif change == "missing_auth":
        del payload["fields"][0]["behavior"]["authorization_ref"]
    elif change == "missing_comment":
        del payload["fields"][0]["behavior"]["comment"]
    else:
        payload["fields"][0]["behavior"]["comment"] = "  \t  "
    try:
        raise ValueError("fictional-private-marker")
    except ValueError:
        with pytest.raises(BehaviorPolicyError) as error:
            parse_behavior_policy(payload)
    assert str(error.value) == "invalid behavior policy"
    assert error.value.__context__ is None


def test_domain_reference_must_resolve_and_cannot_chain():
    payload = policy({"action": "substitute", "mapping": {"kind": "domain", "name": "dates"}})
    with pytest.raises(BehaviorPolicyError):
        parse_behavior_policy(payload)
    payload["domains"] = [{"name": "dates", "mapping": {"kind": "inline", "entries": [
        {"original": ["2025-04-30"], "replacement": ["2026-09-23"]}]}}]
    assert parse_behavior_policy(payload).fields[0].behavior.unmatched.action == "reject"
    payload["domains"][0]["mapping"] = {"kind": "domain", "name": "dates"}
    with pytest.raises(BehaviorPolicyError):
        parse_behavior_policy(payload)


def test_exact_text_policy_accepts_global_and_column_rules_together():
    file_mapping = {"kind": "csv", "path": "all.csv", "source_columns": ["old"],
                    "replacement_columns": ["new"]}
    column_mapping = {"kind": "csv", "path": "status.csv", "source_columns": ["old"],
                      "replacement_columns": ["new"]}
    payload = policy({"action": "replace_text", "mapping": column_mapping})
    payload["file_text_mapping"] = file_mapping
    parsed = parse_behavior_policy(payload)
    assert parsed.file_text_mapping.path == "all.csv"
    assert parsed.fields[0].behavior.mapping.path == "status.csv"
    assert parse_behavior_policy(parsed.model_dump(mode="json")) == parsed
    global_only = policy({"action": "replace_text"})
    global_only["file_text_mapping"] = file_mapping
    assert parse_behavior_policy(global_only).fields[0].behavior.mapping is None


def test_exact_text_preserve_fallback_still_requires_explicit_non_sensitive_decision():
    payload = policy({"action": "replace_text", "unmatched": {
        "action": "preserve", "authorization_ref": "fictional-review",
        "comment": "Reviewed fictional business code",
    }})
    payload["file_text_mapping"] = {"kind": "csv", "path": "all.csv",
                                    "source_columns": ["old"], "replacement_columns": ["new"]}
    assert parse_behavior_policy(payload).fields[0].behavior.unmatched.action == "preserve"
    payload["fields"][0]["sensitivity"] = "sensitive"
    with pytest.raises(BehaviorPolicyError, match="^invalid behavior policy$"):
        parse_behavior_policy(payload)


@pytest.mark.parametrize("mutation", ["no_table", "unused_global", "inline_column",
                                       "domain_column", "global_across_files"])
def test_exact_text_policy_rejects_incomplete_or_wrong_scope_without_values(mutation):
    payload = policy({"action": "replace_text"})
    if mutation == "unused_global":
        payload["fields"][0]["behavior"] = {"action": "drop"}
        payload["file_text_mapping"] = {"kind": "csv", "path": "private-marker.csv",
                                        "source_columns": ["old"], "replacement_columns": ["new"]}
    elif mutation == "inline_column":
        payload["fields"][0]["behavior"]["mapping"] = {
            "kind": "inline", "entries": [{"original": ["private-marker"], "replacement": ["x"]}],
        }
    elif mutation == "domain_column":
        payload["fields"][0]["behavior"]["mapping"] = {"kind": "domain", "name": "private-marker"}
    elif mutation == "global_across_files":
        payload["file_text_mapping"] = {"kind": "csv", "path": "private-marker.csv",
                                        "source_columns": ["old"], "replacement_columns": ["new"]}
        payload["fields"].append({"entity": "another_file", "field": "value",
                                  "sensitivity": "non_sensitive", "behavior": {"action": "drop"}})
    with pytest.raises(BehaviorPolicyError, match="^invalid behavior policy$") as error:
        parse_behavior_policy(payload)
    assert "private-marker" not in str(error.value)


@pytest.mark.parametrize("sensitivity", ["non_sensitive", "sensitive", "unknown"])
def test_unmatched_preserve_requires_non_sensitive_declaration(sensitivity):
    payload = policy({"action": "substitute", "mapping": {"kind": "csv",
        "path": "fictional.csv", "source_columns": ["old"], "replacement_columns": ["new"]},
        "unmatched": {"action": "preserve", "authorization_ref": "review",
                      "comment": "Reviewed unmatched business code"}})
    payload["fields"][0]["sensitivity"] = sensitivity
    if sensitivity == "non_sensitive":
        assert parse_behavior_policy(payload).fields[0].behavior.unmatched.action == "preserve"
    else:
        with pytest.raises(BehaviorPolicyError):
            parse_behavior_policy(payload)


def test_required_version_and_unique_domains():
    payload = policy({"action": "drop"})
    del payload["schema_version"]
    with pytest.raises(BehaviorPolicyError):
        parse_behavior_policy(payload)
    payload["schema_version"] = "0.1"
    domain = {"name": "dates", "mapping": {"kind": "inline", "entries": [
        {"original": ["a"], "replacement": ["b"]}]}}
    payload["domains"] = [domain, copy.deepcopy(domain)]
    with pytest.raises(BehaviorPolicyError):
        parse_behavior_policy(payload)


@pytest.mark.parametrize("field_names", [["value"], ["other"], ["value", "extra"], []])
def test_exact_field_coverage(field_names):
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": name, "data_type": "string"} for name in field_names]}]})
    decision = parse_behavior_policy(policy({"action": "drop"}))
    if field_names == ["value"]:
        assert validate_policy_field_coverage(decision, profile) is None
    else:
        with pytest.raises(BehaviorPolicyError, match="^invalid policy field coverage$"):
            validate_policy_field_coverage(decision, profile)


@pytest.mark.parametrize("mutation", ["duplicate_field", "duplicate_entity", "rename_entity"])
def test_coverage_revalidates_mutated_profiles_without_leaking_errors(mutation):
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "value", "data_type": "string"}]}]})
    if mutation == "duplicate_field":
        profile.entities[0].fields.append(profile.entities[0].fields[0])
    elif mutation == "duplicate_entity":
        profile.entities.append(profile.entities[0])
    else:
        profile.entities[0].name = "fictional-private-marker"
    decision = parse_behavior_policy(policy({"action": "drop"}))
    try:
        raise ValueError("fictional-private-marker")
    except ValueError:
        with pytest.raises(BehaviorPolicyError) as error:
            validate_policy_field_coverage(decision, profile)
    assert str(error.value) == "invalid policy field coverage"
    assert error.value.__context__ is None
    assert error.value.__cause__ is None


def test_coverage_rejects_forged_policy():
    decision = parse_behavior_policy(policy({"action": "drop"}))
    forged = decision.model_copy(update={"fields": ()})
    with pytest.raises(BehaviorPolicyError, match="^invalid behavior policy$"):
        validate_policy_field_coverage(forged, DatasetProfile())


def test_review_shows_every_action_without_mapping_values_or_control_codes():
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "value\nnext", "data_type": "string", "sensitive": False}]}]})
    payload = policy({"action": "substitute", "mapping": {"kind": "inline", "entries": [
        {"original": ["fictional-private-marker"], "replacement": ["fictional-output-marker"]}]},
        "unmatched": {"action": "preserve", "authorization_ref": "fictional-secret-ref",
                      "comment": "fictional-private-comment"}})
    payload["fields"][0]["field"] = "value\nnext"
    payload["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    review = render_policy_review(parse_behavior_policy(payload), profile, max_bytes=4096)
    assert b'"action": "substitute"' in review
    assert b'"unmatched": "preserve"' in review
    assert b'"preserves_original": true' in review
    assert b'"declared_sensitivity": "non_sensitive"' in review
    assert b'"observed_sensitivity": "unknown"' in review
    assert b'"system_comment": "Likely string field; meaning and sensitivity unverified."' in review
    assert b'value\\nnext' in review
    assert b'fictional-private-marker' not in review
    assert b'fictional-output-marker' not in review
    assert b'fictional-secret-ref' not in review
    assert b'fictional-private-comment' not in review
    with pytest.raises(BehaviorPolicyError, match="^invalid policy review$"):
        render_policy_review(parse_behavior_policy(payload), profile, max_bytes=1)


@pytest.mark.parametrize("dependencies", [["input"], ["missing"], ["value"], ["input", "input"]])
def test_derived_dependencies(dependencies):
    payload = policy({"action": "derive", "expression": "input + 1", "dependencies": dependencies})
    payload["fields"].append({"entity": "items", "field": "input", "sensitivity": "unknown",
                              "behavior": {"action": "synthesize", "generation_policy_ref": "rule"}})
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": name, "data_type": "integer"} for name in ["value", "input"]]}]})
    if dependencies == ["input"]:
        validate_policy_field_coverage(parse_behavior_policy(payload), profile)
        payload["fields"][1]["behavior"] = {"action": "drop"}
    with pytest.raises(BehaviorPolicyError):
        validate_policy_field_coverage(parse_behavior_policy(payload), profile)


@pytest.mark.parametrize(("expression", "dependencies"), [
    ("hidden + 1", ["input"]),
    ("input + 1", ["input", "other"]),
    ("sum('input')", ["input"]),
    ("count()", ["input"]),
    ("input.real", ["input"]),
    ("(input", ["input"]),
    ("evil('fictional-private-marker')", ["input"]),
    ("input " + " " * 1024, ["input"]),
    (" + ".join(["input"] * 50), ["input"]),
])
def test_derive_preflight_rejects_expression_dependency_disagreement(expression, dependencies):
    payload = policy({"action": "derive", "expression": expression, "dependencies": dependencies})
    payload["fields"].extend({"entity": "items", "field": name, "sensitivity": "unknown",
                              "behavior": {"action": "synthesize", "generation_policy_ref": "rule"}}
                             for name in ["input", "other"])
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": name, "data_type": "integer"} for name in ["value", "input", "other"]]}]})
    with pytest.raises(BehaviorPolicyError, match="^invalid policy field coverage$") as caught:
        validate_policy_field_coverage(parse_behavior_policy(payload), profile)
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None


@pytest.mark.parametrize(("expression", "dependencies"), [
    ("input + input", ["input"]),
    ("-(input * other) / 2", ["other", "input"]),
    ("sum + count", ["sum", "count"]),
])
def test_derive_preflight_accepts_exact_field_references_without_evaluation(expression, dependencies):
    payload = policy({"action": "derive", "expression": expression, "dependencies": dependencies})
    payload["fields"].extend({"entity": "items", "field": name, "sensitivity": "unknown",
                              "behavior": {"action": "synthesize", "generation_policy_ref": "rule"}}
                             for name in dependencies)
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 0,
        "fields": [{"name": name, "data_type": "integer"} for name in ["value", *dependencies]]}]})
    validate_policy_field_coverage(parse_behavior_policy(payload), profile)


@pytest.mark.parametrize("fallback", [False, True])
def test_observed_sensitivity_blocks_preservation(fallback):
    behavior = {"action": "preserve", "authorization_ref": "review",
                "comment": "Reviewed fictional business code"}
    if fallback:
        behavior = {"action": "substitute", "mapping": {"kind": "inline", "entries": [
            {"original": ["fictional-a"], "replacement": ["fictional-b"]}]}, "unmatched": behavior}
    decision = parse_behavior_policy(policy(behavior))
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "value", "data_type": "string", "sensitive": True}]}]})
    with pytest.raises(BehaviorPolicyError):
        validate_policy_field_coverage(decision, profile)


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("observed_sensitive", [False, True])
def test_decimal_preservation_blocked_by_default(fallback, observed_sensitive):
    behavior = {"action": "preserve", "authorization_ref": "review",
                "comment": "Fictional financial amount"}
    if fallback:
        behavior = {"action": "substitute", "mapping": {"kind": "inline", "entries": [
            {"original": ["1.00"], "replacement": ["2.00"]}]}, "unmatched": behavior}
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "amount", "data_type": "decimal", "decimal_precision": 20,
                    "decimal_scale": 2, "sensitive": observed_sensitive}]}]})
    payload = policy(behavior)
    payload["fields"][0]["field"] = "amount"
    payload["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    decision = parse_behavior_policy(payload)
    with pytest.raises(BehaviorPolicyError, match="^invalid policy field coverage$"):
        validate_policy_profile(decision, profile)


@pytest.mark.parametrize("metadata", [
    {"decimal_precision": 21, "decimal_scale": 2},
    {"decimal_precision": 20, "decimal_scale": 3},
])
def test_decimal_shape_changes_schema_fingerprint(metadata):
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "amount", "data_type": "decimal", "decimal_precision": 20,
                    "decimal_scale": 2}]}]})
    changed = profile.model_copy(deep=True)
    for key, value in metadata.items():
        setattr(changed.entities[0].fields[0], key, value)
    assert transformation_schema_fingerprint(changed) != transformation_schema_fingerprint(profile)


@pytest.mark.parametrize("field_name,semantic_type", [
    ("customer_email", None), ("value", "phone"),
])
@pytest.mark.parametrize("fallback", [False, True])
def test_name_or_semantic_sensitivity_blocks_preservation(field_name, semantic_type, fallback):
    behavior = {"action": "preserve", "authorization_ref": "review",
                "comment": "Reviewed fictional business code"}
    if fallback:
        behavior = {"action": "substitute", "mapping": {"kind": "inline", "entries": [
            {"original": ["fictional-a"], "replacement": ["fictional-b"]}]},
            "unmatched": behavior}
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": field_name, "data_type": "string", "sensitive": False,
                    "semantic_type": semantic_type}]}]})
    payload = policy(behavior)
    payload["fields"][0]["field"] = field_name
    payload["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    decision = parse_behavior_policy(payload)
    with pytest.raises(BehaviorPolicyError, match="^invalid policy field coverage$"):
        validate_policy_profile(decision, profile)
    with pytest.raises(BehaviorPolicyError, match="^invalid policy field coverage$"):
        render_policy_review(decision, profile, max_bytes=4096)


def test_review_labels_sensitive_name_without_observed_flag():
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "customer_email", "data_type": "string", "sensitive": False}]}]})
    payload = policy({"action": "drop"})
    payload["fields"][0]["field"] = "customer_email"
    payload["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    review = render_policy_review(parse_behavior_policy(payload), profile, max_bytes=4096)
    assert b'"observed_sensitivity": "sensitive"' in review
    assert b'"system_comment": "Possible email or contact field from metadata; treat as potentially sensitive."' in review


def test_review_comment_does_not_echo_untrusted_semantic_type():
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "value", "data_type": "string",
                    "semantic_type": "fictional-private-marker"}]}]})
    payload = policy({"action": "drop"})
    payload["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    review = render_policy_review(parse_behavior_policy(payload), profile, max_bytes=4096)
    assert b'"observed_sensitivity": "unknown"' in review
    assert b"fictional-private-marker" not in review


@pytest.mark.parametrize("change", ["type", "nullable", "name", "statistics"])
def test_schema_binding_detects_column_drift_not_statistics(change):
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "value", "data_type": "string"}]}]})
    payload = policy({"action": "drop"})
    payload["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    decision = parse_behavior_policy(payload)
    validate_policy_profile(decision, profile)
    field = profile.entities[0].fields[0]
    if change == "type":
        field.data_type = "integer"
    elif change == "nullable":
        field.nullable = True
    elif change == "name":
        field.name = "renamed"
    else:
        profile.entities[0].row_count = 10
        field.unique_ratio = 0.5
        validate_policy_profile(decision, profile)
        return
    with pytest.raises(BehaviorPolicyError):
        validate_policy_profile(decision, profile)


@pytest.mark.parametrize("warning_mode", ["always", "error"])
@pytest.mark.parametrize("helper", ["coverage", "fingerprint"])
def test_malformed_profile_does_not_emit_private_serialization_warnings(warning_mode, helper):
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "value", "data_type": "string"}]}]})
    field = profile.entities[0].fields[0]
    profile.entities[0].fields[0] = field.model_copy(update={"name": ["fictional-private-marker"]})
    decision = parse_behavior_policy(policy({"action": "drop"}))
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter(warning_mode)
        with pytest.raises(BehaviorPolicyError) as error:
            if helper == "coverage":
                validate_policy_field_coverage(decision, profile)
            else:
                transformation_schema_fingerprint(profile)
    assert not recorded
    assert "fictional-private-marker" not in str(error.value)
    assert error.value.__context__ is None
