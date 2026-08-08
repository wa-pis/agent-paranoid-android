from __future__ import annotations

import json
from dataclasses import asdict
from decimal import Decimal

from scripts.benchmark_openai_advisor_presets import (
    PRESETS,
    representative_profiles,
    run_advisor_preset_benchmark,
)
from test_data_agent.advisor import AdvisorProposal
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
        client_factory=FakeBenchmarkClient,
    )

    assert set(profiles) == {"relational", "wide"}
    assert [result.preset for result in results] == list(PRESETS)
    serialized = json.dumps([asdict(result) for result in results])
    assert "contact_email" not in serialized
    assert "synthetic_a" not in serialized
    for result in results:
        assert result.profile_count == 2
        assert result.validity_rate == 1.0
        assert result.safety_preservation_rate == 1.0
        assert result.mean_latency_ms == 10
        assert result.input_tokens == 200
        assert result.output_tokens == 40
        assert result.reported_retries == 0
        assert result.cost_usd == "0.000280"
