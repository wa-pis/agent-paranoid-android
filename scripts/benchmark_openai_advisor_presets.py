#!/usr/bin/env python3
"""Benchmark OpenAI advisor preset candidates on synthetic metadata only."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from test_data_agent.advisor import (
    AdvisorContractError,
    AdvisorProposal,
    build_advisor_exchange,
    build_advisor_request,
    validate_advisor_proposal,
)
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.entity import EntityProfile
from test_data_agent.core.field import FieldProfile, FieldType
from test_data_agent.core.relationship import Relationship
from test_data_agent.providers.openai import (
    OpenAIAdvisorClient,
    OpenAIAdvisorPreset,
    OpenAIAdvisorSettings,
    openai_advisor_settings_for_preset,
)


PRESETS: tuple[OpenAIAdvisorPreset, ...] = ("fast", "normal", "quality")
ONE_MILLION = Decimal(1_000_000)


@dataclass(frozen=True, slots=True)
class AdvisorPresetBenchmark:
    preset: OpenAIAdvisorPreset
    model: str
    reasoning_effort: str
    configured_max_retries: int
    profile_count: int
    valid_proposals: int
    safety_preserved: int
    validity_rate: float
    safety_preservation_rate: float
    mean_latency_ms: int
    input_tokens: int
    output_tokens: int
    reported_retries: int | None
    cost_usd: str


def representative_profiles() -> dict[str, DatasetProfile]:
    relational = DatasetProfile(
        source_type="synthetic_benchmark",
        entities=[
            EntityProfile(
                name="customers",
                row_count=10_000,
                primary_key_candidates=["customer_id"],
                fields=[
                    FieldProfile(
                        name="customer_id",
                        data_type=FieldType.INTEGER,
                        unique_ratio=1.0,
                        is_identifier=True,
                    ),
                    FieldProfile(
                        name="email",
                        data_type=FieldType.STRING,
                        sensitive=True,
                        semantic_type="email",
                    ),
                    FieldProfile(
                        name="segment",
                        data_type=FieldType.STRING,
                        distribution={
                            "kind": "categorical",
                            "categories": [
                                {"value": "synthetic_a", "count": 6_000},
                                {"value": "synthetic_b", "count": 4_000},
                            ],
                        },
                    ),
                ],
            ),
            EntityProfile(
                name="orders",
                row_count=50_000,
                primary_key_candidates=["order_id"],
                fields=[
                    FieldProfile(
                        name="order_id",
                        data_type=FieldType.INTEGER,
                        unique_ratio=1.0,
                        is_identifier=True,
                    ),
                    FieldProfile(
                        name="customer_id",
                        data_type=FieldType.INTEGER,
                        is_identifier=True,
                    ),
                    FieldProfile(name="amount", data_type=FieldType.FLOAT),
                ],
            ),
        ],
        relationships=[
            Relationship(
                parent_entity="customers",
                parent_field="customer_id",
                child_entity="orders",
                child_field="customer_id",
                confidence=1.0,
                status="synthetic",
            )
        ],
    )
    wide = DatasetProfile(
        source_type="synthetic_benchmark",
        entities=[
            EntityProfile(
                name="events",
                row_count=100_000,
                primary_key_candidates=["event_id"],
                fields=[
                    FieldProfile(
                        name="event_id",
                        data_type=FieldType.INTEGER,
                        unique_ratio=1.0,
                        is_identifier=True,
                    ),
                    FieldProfile(
                        name="contact_email",
                        data_type=FieldType.STRING,
                        sensitive=True,
                        semantic_type="email",
                    ),
                    *[
                        FieldProfile(
                            name=f"metric_{index:02d}",
                            data_type=FieldType.FLOAT,
                            nullable=index % 3 == 0,
                            null_ratio=0.1 if index % 3 == 0 else 0.0,
                        )
                        for index in range(24)
                    ],
                ],
            )
        ],
    )
    return {"relational": relational, "wide": wide}


def _live_client(settings: OpenAIAdvisorSettings) -> OpenAIAdvisorClient:
    return OpenAIAdvisorClient(settings=settings)


def _preserves_safety(profile: DatasetProfile, proposal: AdvisorProposal) -> bool:
    for entity in profile.entities:
        candidate_entity = proposal.dataset_spec.entity(entity.name)
        for field in entity.fields:
            candidate = candidate_entity.field(field.name)
            if field.sensitive and not candidate.sensitive:
                return False
            if field.is_identifier and not candidate.is_identifier:
                return False
    return True


def run_advisor_preset_benchmark(
    *,
    input_usd_per_million: Decimal,
    output_usd_per_million: Decimal,
    client_factory: Callable[[OpenAIAdvisorSettings], Any] = _live_client,
) -> list[AdvisorPresetBenchmark]:
    profiles = representative_profiles()
    results: list[AdvisorPresetBenchmark] = []
    for preset in PRESETS:
        settings = openai_advisor_settings_for_preset(preset)
        client = client_factory(settings)
        valid = safe = latency_ms = input_tokens = output_tokens = 0
        retries: list[int | None] = []
        for profile in profiles.values():
            exchange = build_advisor_exchange(
                build_advisor_request(profile, count=100)
            )
            try:
                payload = client.complete(exchange.model_copy(deep=True))
                proposal = validate_advisor_proposal(exchange.request, payload)
            except AdvisorContractError:
                proposal = None
            valid += proposal is not None
            safe += proposal is not None and _preserves_safety(
                exchange.request.profile,
                proposal,
            )
            metadata = client.last_run_metadata
            if metadata is None or metadata.provider_usage is None:
                raise RuntimeError("advisor benchmark requires provider token usage")
            latency_ms += metadata.latency_ms
            input_tokens += metadata.provider_usage.input_tokens
            output_tokens += metadata.provider_usage.output_tokens
            retries.append(metadata.retry_count)
        cost = (
            Decimal(input_tokens) * input_usd_per_million
            + Decimal(output_tokens) * output_usd_per_million
        ) / ONE_MILLION
        profile_count = len(profiles)
        results.append(
            AdvisorPresetBenchmark(
                preset=preset,
                model=settings.model,
                reasoning_effort=settings.reasoning_effort,
                configured_max_retries=settings.max_retries,
                profile_count=profile_count,
                valid_proposals=valid,
                safety_preserved=safe,
                validity_rate=round(valid / profile_count, 6),
                safety_preservation_rate=round(safe / profile_count, 6),
                mean_latency_ms=round(latency_ms / profile_count),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                reported_retries=(
                    sum(retry for retry in retries if retry is not None)
                    if all(retry is not None for retry in retries)
                    else None
                ),
                cost_usd=str(cost.quantize(Decimal("0.000001"))),
            )
        )
    return results


def _price(value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("price must be a decimal") from exc
    if not parsed.is_finite() or parsed < 0:
        raise argparse.ArgumentTypeError("price must be finite and non-negative")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-usd-per-million", required=True, type=_price)
    parser.add_argument("--output-usd-per-million", required=True, type=_price)
    args = parser.parse_args()
    results = run_advisor_preset_benchmark(
        input_usd_per_million=args.input_usd_per_million,
        output_usd_per_million=args.output_usd_per_million,
    )
    print(json.dumps([asdict(result) for result in results], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
