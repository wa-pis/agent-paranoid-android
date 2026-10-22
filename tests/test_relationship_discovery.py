from __future__ import annotations

from typing import Any

import pytest

from test_data_agent.advisor import RelationshipDiscoveryProposal
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.entity import EntityProfile
from test_data_agent.core.field import FieldProfile, FieldType
from test_data_agent.relationship_discovery import (
    mine_relationship_candidates,
    rank_relationship_candidates,
    review_relationship_proposal,
)


def _profile() -> DatasetProfile:
    return DatasetProfile(
        entities=[
            EntityProfile(
                name="account",
                row_count=10,
                primary_key_candidates=["account_id"],
                fields=[
                    FieldProfile(
                        name="account_id",
                        data_type=FieldType.INTEGER,
                        unique_ratio=1.0,
                        is_identifier=True,
                        distribution={
                            "kind": "categorical",
                            "categories": [{"value": "secret", "count": 1}],
                        },
                    )
                ],
            ),
            EntityProfile(
                name="payment",
                row_count=20,
                fields=[
                    FieldProfile(
                        name="account_id",
                        data_type=FieldType.FLOAT,
                        null_ratio=0.1,
                        unique_ratio=0.4,
                        is_identifier=True,
                    )
                ],
            ),
        ]
    )


def _proposal(candidate_id: str) -> RelationshipDiscoveryProposal:
    candidate = mine_relationship_candidates(_profile())[0]
    return RelationshipDiscoveryProposal(
        candidate_id=candidate_id,
        kind=candidate.kind,
        fields=candidate.fields,
        confidence=0.9,
        evidence=["Metadata suggests a foreign key."],
    )


def test_mining_is_deterministic_and_excludes_profile_values() -> None:
    first = mine_relationship_candidates(_profile())
    second = mine_relationship_candidates(_profile())

    assert first == second
    assert len(first) == 1
    assert first[0].fields[0].entity == "account"
    assert "secret" not in first[0].model_dump_json()
    assert first[0].raw_values_included is False


def test_lower_bound_parent_cannot_supply_key_evidence() -> None:
    profile = _profile()
    profile.entities[0].fields[0].unique_ratio_kind = "lower_bound"
    assert mine_relationship_candidates(profile) == []


def test_lower_bound_child_is_not_reported_as_distinct_ratio() -> None:
    profile = _profile()
    profile.entities[1].fields[0].unique_ratio_kind = "lower_bound"
    candidate = mine_relationship_candidates(profile)[0]
    assert "child_distinct_ratio" not in {item.metric for item in candidate.evidence}


def test_ranking_uses_copy_and_requires_human_review() -> None:
    candidates = mine_relationship_candidates(_profile())

    class MutatingAdvisor:
        def rank(self, received: list[Any]) -> list[RelationshipDiscoveryProposal]:
            received[0].confidence = 0.0
            return [_proposal(received[0].candidate_id)]

    proposals = rank_relationship_candidates(candidates, MutatingAdvisor())

    assert candidates[0].confidence > 0.0
    assert proposals[0].review_status == "requires_human_review"
    assert proposals[0].approved is False
    assert proposals[0].generation_performed is False


def test_human_review_never_authorizes_generation() -> None:
    candidate = mine_relationship_candidates(_profile())[0]
    review = review_relationship_proposal(
        _proposal(candidate.candidate_id),
        decision="accepted",
        reviewer="data-owner",
    )

    assert review.decision == "accepted"
    assert review.generation_authorized is False


def test_candidate_reports_cardinality_null_and_distinctness() -> None:
    candidate = mine_relationship_candidates(_profile())[0]
    evidence = {item.metric: item.value for item in candidate.evidence}

    assert evidence["type_compatibility"] == 1.0
    assert evidence["cardinality_ratio"] == 0.5
    assert evidence["child_null_ratio"] == 0.1
    assert evidence["child_distinct_ratio"] == 0.4


def test_incompatible_key_types_are_not_candidates() -> None:
    profile = _profile()
    profile.entity("payment").field("account_id").data_type = FieldType.DATE

    assert mine_relationship_candidates(profile) == []


def test_ambiguous_low_confidence_candidates_remain_unresolved() -> None:
    profile = _profile()
    profile.entity("account").field("account_id").unique_ratio = 0.2
    profile.entity("payment").field("account_id").null_ratio = 0.9
    profile.entities.append(
        EntityProfile(
            name="legacy_account",
            row_count=8,
            primary_key_candidates=["account_id"],
            fields=[
                FieldProfile(
                    name="account_id",
                    data_type=FieldType.INTEGER,
                    unique_ratio=0.2,
                    is_identifier=True,
                )
            ],
        )
    )

    candidates = [
        candidate
        for candidate in mine_relationship_candidates(profile)
        if candidate.fields[1].entity == "payment"
    ]

    assert len(candidates) == 2
    assert all(candidate.confidence < 0.5 for candidate in candidates)
    assert {candidate.fields[0].entity for candidate in candidates} == {
        "account",
        "legacy_account",
    }


def test_temporal_candidate_exposes_only_normalized_range_overlap() -> None:
    profile = DatasetProfile(
        entities=[
            EntityProfile(
                name="session",
                row_count=10,
                fields=[
                    FieldProfile(
                        name="started_at",
                        data_type=FieldType.DATETIME,
                        distribution={
                            "kind": "datetime_range",
                            "min": "2026-01-01T10:00:00",
                            "max": "2026-01-01T11:00:00",
                        },
                    ),
                    FieldProfile(
                        name="ended_at",
                        data_type=FieldType.DATETIME,
                        distribution={
                            "kind": "datetime_range",
                            "min": "2026-01-01T11:30:00",
                            "max": "2026-01-01T12:00:00",
                        },
                    ),
                ],
            )
        ]
    )

    candidate = mine_relationship_candidates(profile)[0]
    evidence = {item.metric: item.value for item in candidate.evidence}

    assert candidate.kind == "temporal"
    assert evidence["range_overlap"] == 1.0
    assert "2026-01-01" not in candidate.model_dump_json()


def test_temporal_overlap_and_inverted_ranges_remain_reviewable() -> None:
    profile = DatasetProfile(
        entities=[
            EntityProfile(
                name="window",
                row_count=1,
                fields=[
                    FieldProfile(
                        name="start_date",
                        data_type=FieldType.DATE,
                        distribution={
                            "kind": "date_range",
                            "min": "2026-01-10",
                            "max": "2026-01-20",
                        },
                    ),
                    FieldProfile(
                        name="end_date",
                        data_type=FieldType.DATE,
                        distribution={
                            "kind": "date_range",
                            "min": "2026-01-15",
                            "max": "2026-01-25",
                        },
                    ),
                ],
            )
        ]
    )
    overlapping = mine_relationship_candidates(profile)[0]
    profile.entity("window").field("end_date").distribution = {
        "kind": "date_range",
        "min": "2026-01-01",
        "max": "2026-01-05",
    }
    inverted = mine_relationship_candidates(profile)[0]

    assert {item.metric: item.value for item in overlapping.evidence}[
        "range_overlap"
    ] == 0.5
    assert {item.metric: item.value for item in inverted.evidence}[
        "range_overlap"
    ] == 0.0
    assert inverted.confidence < overlapping.confidence


def test_absent_parent_is_not_invented_from_child_name() -> None:
    profile = _profile()
    profile.entities = [profile.entity("payment")]
    assert mine_relationship_candidates(profile) == []


def test_same_name_and_type_do_not_certify_same_key_domain() -> None:
    profile = _profile()
    profile.entity("payment").field("account_id").data_type = FieldType.INTEGER
    original = profile.model_dump_json()
    candidate = mine_relationship_candidates(profile)[0]
    assert candidate.metadata_trust == "untrusted"
    assert any("domain identity" in assumption and "untested" in assumption
               for assumption in candidate.assumptions)
    assert profile.relationships == []
    assert profile.model_dump_json() == original


def test_candidate_review_does_not_change_inferred_generation() -> None:
    from test_data_agent.generation import generate_dataset, infer_dataset_spec

    profile = _profile()
    profile.entity("account").field("account_id").distribution = {}
    profile.entity("payment").field("account_id").data_type = FieldType.INTEGER
    before = infer_dataset_spec(profile)
    candidate = mine_relationship_candidates(profile)[0]
    review_relationship_proposal(_proposal(candidate.candidate_id),
                                 decision="accepted", reviewer="data-owner")
    after = infer_dataset_spec(profile)
    assert before == after
    assert after.relationships == []
    rows = generate_dataset(after, seed=7)
    parents = {row["account_id"] for row in rows["account"]}
    children = {row["account_id"] for row in rows["payment"] if row["account_id"] is not None}
    assert parents.isdisjoint(children)


def test_metadata_mining_consumes_one_shared_work_budget() -> None:
    import pytest
    from test_data_agent.profiling.budget import (
        LocalProfileBudget, LocalProfileLimits, LocalProfileLimitError,
    )

    budget = LocalProfileBudget(LocalProfileLimits(max_inference_evaluations=1))
    with pytest.raises(LocalProfileLimitError, match="inference_evaluations"):
        mine_relationship_candidates(_profile(), budget=budget)


def test_candidate_count_limit_rejects_instead_of_truncating(monkeypatch) -> None:
    import pytest
    from test_data_agent.core.limits import InputLimitError

    profile = _profile()
    another_parent = profile.entity("account").model_copy(deep=True)
    another_parent.name = "other_account"
    profile.entities.append(another_parent)
    monkeypatch.setattr("test_data_agent.relationship_discovery.MAX_RELATIONSHIP_CANDIDATES", 1)
    with pytest.raises(InputLimitError, match="candidate limit"):
        mine_relationship_candidates(profile)


def test_cli_discovery_is_deterministic_offline_and_metadata_only(tmp_path, monkeypatch) -> None:
    import json
    from test_data_agent.cli import main
    from test_data_agent.io.artifacts import dataset_profile_fingerprint
    from test_data_agent.relationship_discovery import RelationshipDiscoveryReport

    def unexpected(*args, **kwargs):
        raise AssertionError("database access is not part of saved-profile discovery")

    monkeypatch.setattr("test_data_agent.postgres_client.PostgresClient", unexpected)
    source = tmp_path / "profile.json"
    first = tmp_path / "candidates.json"
    second = tmp_path / "second.json"
    profile = _profile()
    source.write_text(profile.model_dump_json())
    original = source.read_bytes()
    for output in (first, second):
        assert main(["discover-relationships", str(source), "--output", str(output)]) == 0
    assert first.read_bytes() == second.read_bytes()
    assert source.read_bytes() == original
    report = RelationshipDiscoveryReport.model_validate_json(first.read_text())
    assert report.profile_fingerprint == dataset_profile_fingerprint(profile)
    assert report.review_status == "requires_human_review"
    assert report.generation_authorized is False
    assert len(report.candidates) == 1
    assert "secret" not in first.read_text()
    assert "relationships" not in json.loads(first.read_text())


def test_cli_only_uses_entities_from_authorized_profile(tmp_path) -> None:
    from test_data_agent.cli import main
    from test_data_agent.relationship_discovery import RelationshipDiscoveryReport

    source = tmp_path / "profile.json"
    output = tmp_path / "candidates.json"
    profile = _profile()
    profile.entities = [profile.entity("payment")]
    source.write_text(profile.model_dump_json())
    assert main(["discover-relationships", str(source), "--output", str(output)]) == 0
    assert RelationshipDiscoveryReport.model_validate_json(output.read_text()).candidates == []


def test_cli_budget_failure_leaves_existing_report_unchanged(tmp_path, monkeypatch) -> None:
    from test_data_agent.cli import main

    source = tmp_path / "profile.json"
    output = tmp_path / "candidates.json"
    source.write_text(_profile().model_dump_json())
    output.write_text("previous-report")
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "1")
    assert main(["discover-relationships", str(source), "--output", str(output), "--overwrite"]) == 2
    assert output.read_text() == "previous-report"


def test_cli_report_payload_limit_publishes_no_partial_report(tmp_path, monkeypatch) -> None:
    from test_data_agent.cli import main

    source = tmp_path / "profile.json"
    output = tmp_path / "candidates.json"
    source.write_text(_profile().model_dump_json())
    # The input fits; the indented candidate report exceeds this bound.
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_PROFILE_PAYLOAD_BYTES", str(len(source.read_bytes()) + 1))
    assert main(["discover-relationships", str(source), "--output", str(output)]) == 2
    assert not output.exists()


@pytest.mark.parametrize("entity,attribute", [
    ("account", "unique_ratio"), ("payment", "unique_ratio"), ("payment", "null_ratio"),
])
def test_unknown_metadata_is_not_numeric_relationship_evidence(entity, attribute):
    profile = _profile()
    setattr(profile.entity(entity).field("account_id"), attribute, None)
    assert mine_relationship_candidates(profile) == []


def temporal_entity() -> EntityProfile:
    return EntityProfile(name="windows", row_count=1, fields=[
        FieldProfile(name=name, data_type=FieldType.DATE, distribution={
            "kind": "date_range", "min": "2026-01-01", "max": "2026-02-01",
        }) for name in ("start_date", "end_date")
    ])


def test_temporal_mining_does_not_restart_work_allowance():
    from test_data_agent.profiling.budget import (
        LocalProfileBudget, LocalProfileLimits, LocalProfileLimitError,
    )

    profile = DatasetProfile(entities=[temporal_entity()])
    assert len(mine_relationship_candidates(profile)) == 1
    # Parent iteration, temporal entity/fields, then the comparison share one budget.
    budget = LocalProfileBudget(LocalProfileLimits(max_inference_evaluations=4))
    with pytest.raises(LocalProfileLimitError, match="inference_evaluations"):
        mine_relationship_candidates(profile, budget=budget)


def test_temporal_and_foreign_key_candidates_share_count_cap(monkeypatch):
    from test_data_agent.core.limits import InputLimitError

    profile = _profile()
    profile.entities.append(temporal_entity())
    assert len(mine_relationship_candidates(profile)) == 2
    monkeypatch.setattr("test_data_agent.relationship_discovery.MAX_RELATIONSHIP_CANDIDATES", 1)
    with pytest.raises(InputLimitError, match="candidate limit"):
        mine_relationship_candidates(profile)



def test_cli_expired_publication_rolls_back_report(tmp_path, monkeypatch):
    from test_data_agent.cli import main
    from test_data_agent.profiling.budget import (
        LocalProfileBudget, LocalProfileDimension, LocalProfileLimitError,
    )

    class ExpiredPublicationBudget(LocalProfileBudget):
        def check_deadline(self, stage):
            if stage == "relationship report publication":
                raise LocalProfileLimitError(LocalProfileDimension.DEADLINE_SECONDS,
                                             attempted=2, limit=1, stage=stage)
            super().check_deadline(stage)

    monkeypatch.setattr("test_data_agent.profiling.budget.LocalProfileBudget", ExpiredPublicationBudget)
    source = tmp_path / "profile.json"
    output = tmp_path / "candidates.json"
    source.write_text(_profile().model_dump_json())
    output.write_text("previous-report")
    assert main(["discover-relationships", str(source), "--output", str(output), "--overwrite"]) == 2
    assert output.read_text() == "previous-report"
    assert not list(tmp_path.glob(".*.tmp"))


def test_generic_key_name_with_competing_parents_remains_untrusted():
    profile = _profile()
    parent = profile.entity("account")
    parent.fields[0].name = "id"
    parent.primary_key_candidates = ["id"]
    profile.entity("payment").fields[0].name = "id"
    other = parent.model_copy(deep=True)
    other.name = "legacy_account"
    profile.entities.append(other)
    candidates = [candidate for candidate in mine_relationship_candidates(profile)
                  if candidate.fields[1].entity == "payment"]
    assert len(candidates) == 2
    assert all(candidate.metadata_trust == "untrusted" for candidate in candidates)
    assert profile.relationships == []



def test_discovery_report_cannot_be_parsed_or_generated_as_a_spec(tmp_path):
    from pydantic import ValidationError
    from test_data_agent.cli import main
    from test_data_agent.core.dataset import DatasetSpec, parse_dataset_spec_payload
    from test_data_agent.io.artifacts import dataset_profile_fingerprint
    from test_data_agent.relationship_discovery import RelationshipDiscoveryReport

    profile = _profile()
    report = RelationshipDiscoveryReport(profile_fingerprint=dataset_profile_fingerprint(profile),
                                         candidates=mine_relationship_candidates(profile))
    for parse in (DatasetSpec.model_validate, parse_dataset_spec_payload):
        with pytest.raises((ValueError, ValidationError), match="not generation specifications"):
            parse(report.model_dump(mode="json"))
    source = tmp_path / "candidates.json"
    output = tmp_path / "generated"
    source.write_text(report.model_dump_json())
    assert main(["generate", str(source), "--output", str(output), "--seed", "7"]) == 2
    assert not output.exists()
