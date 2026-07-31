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
