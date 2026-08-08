from __future__ import annotations

import json
from dataclasses import asdict
from decimal import Decimal

import pytest

from scripts.benchmark_openai_advisor_presets import (
    PRESETS,
    representative_profiles,
    run_advisor_preset_benchmark,
)
from test_data_agent.advisor import AdvisorContractError, AdvisorProposal
from test_data_agent.providers.openai import (
    OpenAIAdvisorRunMetadata,
    OpenAIAdvisorSettings,
    OpenAIAdvisorUsage,
)


class FakeBenchmarkClient:
    def __init__(self, settings: OpenAIAdvisorSettings) -> None:
        self.settings = settings
        self.last_run_metadata: OpenAIAdvisorRunMetadata | None = None

    def complete(self, exchange):
        self.last_run_metadata = OpenAIAdvisorRunMetadata(
            model=self.settings.model,
            settings=self.settings,
            request_bytes=1_000,
            response_bytes=500,
            latency_ms=10,
            status="completed",
            retry_count=0,
            provider_usage=OpenAIAdvisorUsage(
                input_tokens=100,
                output_tokens=20,
                total_tokens=120,
            ),
        )
        return AdvisorProposal(
            profile_sha256=exchange.request.profile_sha256,
            baseline_spec_sha256=exchange.request.baseline_spec_sha256,
            dataset_spec=exchange.request.baseline_spec.model_copy(deep=True),
        ).model_dump(mode="json")


def test_advisor_preset_benchmark_uses_safe_synthetic_profiles() -> None:
    profiles = representative_profiles()
    results = run_advisor_preset_benchmark(
        input_usd_per_million=Decimal("1"),
        output_usd_per_million=Decimal("2"),
        runs_per_preset=5,
        client_factory=FakeBenchmarkClient,
    )

    assert set(profiles) == {
        "narrow",
        "wide",
        "multi_table",
        "nullable_heavy",
        "constraint_heavy",
    }
    assert [result.preset for result in results] == list(PRESETS)
    serialized = json.dumps([asdict(result) for result in results])
    assert "contact_email" not in serialized
    assert "synthetic_alpha" not in serialized
    assert "synthetic_paid" not in serialized
    for result in results:
        assert result.profile_shape_count == 5
        assert result.run_count == 5
        assert result.validity_rate == 1.0
        assert result.safety_preservation_rate == 1.0
        assert result.mean_latency_ms == 10
        assert result.p50_latency_ms == 10
        assert result.p95_latency_ms == 10
        assert result.error_count == 0
        assert result.timeout_count == 0
        assert result.input_tokens == 500
        assert result.output_tokens == 100
        assert result.usage_reported_runs == 5
        assert result.reported_retries == 0
        assert result.retry_count_reported_runs == 5
        assert result.status_counts == {"completed": 5}
        assert result.cost_usd == "0.000700"


class TimeoutBenchmarkClient(FakeBenchmarkClient):
    def __init__(self, settings: OpenAIAdvisorSettings) -> None:
        super().__init__(settings)
        self.calls = 0

    def complete(self, exchange):
        self.calls += 1
        if self.calls == 2:
            self.last_run_metadata = OpenAIAdvisorRunMetadata(
                model=self.settings.model,
                settings=self.settings,
                request_bytes=1_000,
                latency_ms=50,
                status="provider_error",
            )
            try:
                raise TimeoutError("synthetic timeout")
            except TimeoutError as exc:
                raise AdvisorContractError("provider timeout") from exc
        return super().complete(exchange)


def test_advisor_preset_benchmark_aggregates_safe_failure_metrics() -> None:
    results = run_advisor_preset_benchmark(
        input_usd_per_million=Decimal("1"),
        output_usd_per_million=Decimal("2"),
        runs_per_preset=5,
        client_factory=TimeoutBenchmarkClient,
    )

    for result in results:
        assert result.valid_proposals == 4
        assert result.safety_preserved == 4
        assert result.error_count == 1
        assert result.error_rate == 0.2
        assert result.timeout_count == 1
        assert result.timeout_rate == 0.2
        assert result.p50_latency_ms == 10
        assert result.p95_latency_ms == 50
        assert result.usage_reported_runs == 4
        assert result.reported_retries is None
        assert result.retry_count_reported_runs == 4
        assert result.status_counts == {"completed": 4, "provider_error": 1}
        assert result.cost_usd == "0.000560"


@pytest.mark.parametrize("runs_per_preset", [4, 26])
def test_advisor_preset_benchmark_bounds_paid_run_count(
    runs_per_preset: int,
) -> None:
    with pytest.raises(ValueError, match="runs_per_preset"):
        run_advisor_preset_benchmark(
            input_usd_per_million=Decimal("1"),
            output_usd_per_million=Decimal("2"),
            runs_per_preset=runs_per_preset,
            client_factory=FakeBenchmarkClient,
        )
