#!/usr/bin/env python3
"""Benchmark OpenAI advisor preset candidates on synthetic metadata only."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from openai import APITimeoutError

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
MINIMUM_PROFILE_SHAPES = 5
MAXIMUM_RUNS_PER_PRESET = 25


@dataclass(frozen=True, slots=True)
class AdvisorPresetBenchmark:
    preset: OpenAIAdvisorPreset
    model: str
    reasoning_effort: str
    configured_max_retries: int
    profile_shapes: tuple[str, ...]
    profile_shape_count: int
    run_count: int
    valid_proposals: int
    safety_preserved: int
    validity_rate: float
    safety_preservation_rate: float
    mean_latency_ms: int
    p50_latency_ms: int
    p95_latency_ms: int
    error_count: int
    error_rate: float
    timeout_count: int
    timeout_rate: float
    input_tokens: int
    output_tokens: int
    usage_reported_runs: int
    reported_retries: int | None
    retry_count_reported_runs: int
    status_counts: dict[str, int]
    cost_usd: str


def representative_profiles() -> dict[str, DatasetProfile]:
    narrow = DatasetProfile(
        source_type="synthetic_benchmark",
        entities=[
            EntityProfile(
                name="records",
                row_count=1_000,
                primary_key_candidates=["record_id"],
                fields=[
                    FieldProfile(
                        name="record_id",
                        data_type=FieldType.INTEGER,
                        unique_ratio=1.0,
                        is_identifier=True,
                    ),
                    FieldProfile(
                        name="label",
                        data_type=FieldType.STRING,
                        distribution={
                            "kind": "categorical",
                            "categories": [
                                {"value": "synthetic_alpha", "count": 700},
                                {"value": "synthetic_beta", "count": 300},
                            ],
                        },
                    ),
                    FieldProfile(
                        name="contact_email",
                        data_type=FieldType.STRING,
                        sensitive=True,
                        semantic_type="email",
                    ),
                ],
            )
        ],
    )
    multi_table = DatasetProfile(
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
    nullable_heavy = DatasetProfile(
        source_type="synthetic_benchmark",
        entities=[
            EntityProfile(
                name="optional_events",
                row_count=25_000,
                primary_key_candidates=["event_id"],
                fields=[
                    FieldProfile(
                        name="event_id",
                        data_type=FieldType.INTEGER,
                        unique_ratio=1.0,
                        is_identifier=True,
                    ),
                    FieldProfile(
                        name="owner_email",
                        data_type=FieldType.STRING,
                        nullable=True,
                        null_ratio=0.7,
                        sensitive=True,
                        semantic_type="email",
                    ),
                    *[
                        FieldProfile(
                            name=f"optional_metric_{index:02d}",
                            data_type=(
                                FieldType.FLOAT if index % 2 == 0 else FieldType.STRING
                            ),
                            nullable=True,
                            null_ratio=0.65,
                        )
                        for index in range(10)
                    ],
                ],
            )
        ],
    )
    constraint_heavy = DatasetProfile.model_validate(
        {
            "source_type": "synthetic_benchmark",
            "entities": [
                {
                    "name": "invoices",
                    "row_count": 12_000,
                    "primary_key_candidates": ["invoice_id"],
                    "fields": [
                        {
                            "name": "invoice_id",
                            "data_type": "integer",
                            "unique_ratio": 1.0,
                            "is_identifier": True,
                        },
                        {
                            "name": "status",
                            "data_type": "string",
                            "distribution": {
                                "kind": "categorical",
                                "categories": [
                                    {"value": "synthetic_open", "count": 3_000},
                                    {"value": "synthetic_paid", "count": 9_000},
                                ],
                            },
                        },
                        {"name": "issued_at", "data_type": "datetime"},
                        {
                            "name": "paid_at",
                            "data_type": "datetime",
                            "nullable": True,
                            "null_ratio": 0.25,
                        },
                        {"name": "subtotal", "data_type": "float"},
                        {"name": "tax", "data_type": "float"},
                        {"name": "total", "data_type": "float"},
                    ],
                }
            ],
            "constraints": [
                {
                    "type": "formula",
                    "entity": "invoices",
                    "fields": ["subtotal", "tax", "total"],
                    "expression": "subtotal + tax = total",
                    "confidence": 1.0,
                    "status": "confirmed",
                },
                {
                    "type": "temporal",
                    "entity": "invoices",
                    "fields": ["issued_at", "paid_at"],
                    "confidence": 1.0,
                    "status": "confirmed",
                },
                {
                    "type": "conditional_required",
                    "entity": "invoices",
                    "fields": ["paid_at"],
                    "condition": {"field": "status", "equals": "synthetic_paid"},
                    "confidence": 1.0,
                    "status": "confirmed",
                },
            ],
        }
    )
    return {
        "narrow": narrow,
        "wide": wide,
        "multi_table": multi_table,
        "nullable_heavy": nullable_heavy,
        "constraint_heavy": constraint_heavy,
    }


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


def _nearest_rank(values: list[int], percentile: float) -> int:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * percentile) - 1)]


def _is_timeout_error(error: AdvisorContractError) -> bool:
    cause = error.__cause__
    while cause is not None:
        if isinstance(cause, (APITimeoutError, TimeoutError)):
            return True
        cause = cause.__cause__
    return False


def run_advisor_preset_benchmark(
    *,
    input_usd_per_million: Decimal,
    output_usd_per_million: Decimal,
    runs_per_preset: int,
    client_factory: Callable[[OpenAIAdvisorSettings], Any] = _live_client,
) -> list[AdvisorPresetBenchmark]:
    profiles = representative_profiles()
    profile_names = tuple(profiles)
    if len(profiles) < MINIMUM_PROFILE_SHAPES:
        raise ValueError("advisor benchmark requires at least five profile shapes")
    if runs_per_preset < len(profiles):
        raise ValueError("runs_per_preset must cover every profile shape")
    if runs_per_preset > MAXIMUM_RUNS_PER_PRESET:
        raise ValueError("runs_per_preset exceeds the bounded maximum of 25")
    results: list[AdvisorPresetBenchmark] = []
    for preset in PRESETS:
        settings = openai_advisor_settings_for_preset(preset)
        client = client_factory(settings)
        valid = safe = errors = timeouts = input_tokens = output_tokens = 0
        latency_samples: list[int] = []
        retries: list[int | None] = []
        usage_reported_runs = 0
        status_counts: Counter[str] = Counter()
        for run_index in range(runs_per_preset):
            profile = profiles[profile_names[run_index % len(profile_names)]]
            exchange = build_advisor_exchange(build_advisor_request(profile, count=100))
            proposal: AdvisorProposal | None
            try:
                payload = client.complete(exchange.model_copy(deep=True))
                proposal = validate_advisor_proposal(exchange.request, payload)
            except AdvisorContractError as exc:
                proposal = None
                errors += 1
                timeouts += _is_timeout_error(exc)
            valid += proposal is not None
            safe += proposal is not None and _preserves_safety(
                exchange.request.profile,
                proposal,
            )
            metadata = client.last_run_metadata
            if metadata is None:
                raise RuntimeError("advisor benchmark requires provider run metadata")
            latency_samples.append(metadata.latency_ms)
            status_counts[metadata.status] += 1
            if metadata.provider_usage is not None:
                usage_reported_runs += 1
                input_tokens += metadata.provider_usage.input_tokens
                output_tokens += metadata.provider_usage.output_tokens
            retries.append(metadata.retry_count)
        cost = (
            Decimal(input_tokens) * input_usd_per_million
            + Decimal(output_tokens) * output_usd_per_million
        ) / ONE_MILLION
        reported_retry_values = [retry for retry in retries if retry is not None]
        results.append(
            AdvisorPresetBenchmark(
                preset=preset,
                model=settings.model,
                reasoning_effort=settings.reasoning_effort,
                configured_max_retries=settings.max_retries,
                profile_shapes=profile_names,
                profile_shape_count=len(profiles),
                run_count=runs_per_preset,
                valid_proposals=valid,
                safety_preserved=safe,
                validity_rate=round(valid / runs_per_preset, 6),
                safety_preservation_rate=round(safe / runs_per_preset, 6),
                mean_latency_ms=round(sum(latency_samples) / runs_per_preset),
                p50_latency_ms=_nearest_rank(latency_samples, 0.50),
                p95_latency_ms=_nearest_rank(latency_samples, 0.95),
                error_count=errors,
                error_rate=round(errors / runs_per_preset, 6),
                timeout_count=timeouts,
                timeout_rate=round(timeouts / runs_per_preset, 6),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                usage_reported_runs=usage_reported_runs,
                reported_retries=(
                    sum(reported_retry_values)
                    if len(reported_retry_values) == runs_per_preset
                    else None
                ),
                retry_count_reported_runs=len(reported_retry_values),
                status_counts=dict(sorted(status_counts.items())),
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


def _run_count(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("run count must be an integer") from exc
    if parsed < MINIMUM_PROFILE_SHAPES or parsed > MAXIMUM_RUNS_PER_PRESET:
        raise argparse.ArgumentTypeError("run count must be between 5 and 25")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-usd-per-million", required=True, type=_price)
    parser.add_argument("--output-usd-per-million", required=True, type=_price)
    parser.add_argument(
        "--runs-per-preset",
        required=True,
        type=_run_count,
    )
    args = parser.parse_args()
    results = run_advisor_preset_benchmark(
        input_usd_per_million=args.input_usd_per_million,
        output_usd_per_million=args.output_usd_per_million,
        runs_per_preset=args.runs_per_preset,
    )
    print(json.dumps([asdict(result) for result in results], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
