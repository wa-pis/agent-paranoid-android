from __future__ import annotations

from typing import Any

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
