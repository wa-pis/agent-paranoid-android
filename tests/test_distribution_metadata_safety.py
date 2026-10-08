"""Reject opaque distribution payloads before either external advisor transport."""
from __future__ import annotations

import copy
from typing import Any

import pytest
from pydantic import ValidationError

from test_data_agent.core.field import FieldProfile, FieldSpec, FieldType

CANARY = "fictional-opaque-source-canary"
INVALID = [
    {"raw_rows": [{"value": CANARY}]},
    {"kind": "fictional_unsupported", "nested": {"raw_rows": [CANARY]}},
    {"kind": None, "raw_rows": [CANARY]},
    {"kind": [], "raw_rows": [CANARY]},
    {"kind": {}, "raw_rows": [CANARY]},
]


@pytest.mark.parametrize("model", [FieldProfile, FieldSpec])
@pytest.mark.parametrize("distribution", INVALID)
def test_opaque_distribution_rejected_by_shared_field_contract(model, distribution) -> None:
    with pytest.raises(ValidationError, match="supported kind") as raised:
        model(name="status", data_type=FieldType.STRING, distribution=distribution)
    assert CANARY not in str(raised.value)


@pytest.mark.parametrize("model", [FieldProfile, FieldSpec])
def test_empty_distribution_and_supported_metadata_remain_valid(model) -> None:
    assert model(name="status", data_type=FieldType.STRING).distribution == {}
    assert model(name="status", data_type=FieldType.STRING, distribution={}).distribution == {}
    field = model(name="status", data_type=FieldType.STRING,
        distribution={"kind": "categorical", "categories": [{"value": "fictional", "count": 3}]})
    assert field.typed_distribution is not None
    assert field.distribution["categories"] == [{"value": "fictional", "count": 3.0}]


@pytest.mark.parametrize("model", [FieldProfile, FieldSpec])
def test_distribution_assignment_refuses_opaque_metadata_without_mutation(model) -> None:
    field = model(name="status", data_type=FieldType.STRING)
    with pytest.raises(ValidationError, match="supported kind"):
        field.distribution = copy.deepcopy(INVALID[0])
    assert field.distribution == {}


@pytest.mark.parametrize("provider", ["openai", "gigachat"])
@pytest.mark.parametrize("representation", ["profile", "baseline_spec"])
@pytest.mark.parametrize("distribution", INVALID[:2])
def test_provider_revalidates_mutated_distribution_before_fake_sdk(provider, representation, distribution) -> None:
    from tests.test_gigachat_provider import FakeGigaChat, safe_exchange
    from tests.test_openai_provider import FakeOpenAI, FakeResponses
    from test_data_agent.providers.openai import OpenAIAdvisorClient
    from test_data_agent.providers.gigachat import GigaChatAdvisorClient

    exchange = safe_exchange()
    dataset = getattr(exchange.request, representation)
    field = dataset.entities[0].fields[1]
    # Exercise mutation after construction; adapters must revalidate the serialized request.
    field.distribution.clear()
    field.distribution.update(copy.deepcopy(distribution))
    if provider == "openai":
        sdk: Any = FakeResponses()
        client: Any = OpenAIAdvisorClient(client=FakeOpenAI(sdk), model="test-model")
    else:
        sdk = FakeGigaChat()
        client = GigaChatAdvisorClient(client=sdk, model="test-model")
    with pytest.raises(ValidationError, match="supported kind") as raised:
        client.complete(exchange)
    assert sdk.calls == []
    assert CANARY not in str(raised.value)
