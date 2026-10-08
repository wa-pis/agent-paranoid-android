"""Synthetic source-value canaries never cross the semantic provider boundary."""
import json

import pytest

from test_data_agent.advisor import (
    AdvisorContractError, AdvisorProposal, ExchangeDatasetAdvisor,
    build_advisor_exchange, build_advisor_request,
)
from test_data_agent.core.constraint import Constraint
from test_data_agent.providers.category_privacy import _provider_safe_request, _restore_local_categories
from tests.test_gigachat_provider import safe_exchange

CANARY = "fictional-source-metadata-canary"


def request_with_metadata(distribution):
    profile = safe_exchange().request.profile.model_copy(deep=True)
    field = profile.entities[0].fields[1]
    field.distribution = distribution
    profile.constraints = [Constraint(type="conditional_required", entity="customers",
        fields=[field.name], confidence=1.0, condition={"field": field.name, "equals": "fixture",
        "raw_rows": [{"source": CANARY}]}, expected={"raw_rows": [CANARY]}, expression=CANARY)]
    # Categorical predicate must have a represented domain.
    if distribution.get("kind") != "categorical":
        profile.constraints = []
    return build_advisor_request(profile)


@pytest.mark.parametrize("distribution", [
    {"kind": "synthetic_identifier", "prefix": CANARY},
    {"kind": "date_range", "min": "2020-01-01" + CANARY, "max": "2020-12-31" + CANARY},
    {"kind": "masked_patterns", "patterns": [{"pattern": CANARY, "count": 3}]},
    {"kind": "categorical", "categories": [{"value": "fixture", "count": 3}]},
])
def test_projection_removes_value_carriers_and_restores_noop(distribution):
    request = request_with_metadata(distribution)
    original = request.model_dump(mode="json")
    if distribution.get("kind") == "date_range":
        assert CANARY in original["profile"]["entities"][0]["fields"][1]["distribution"]["min"]
        assert CANARY in original["profile"]["entities"][0]["fields"][1]["distribution"]["max"]
    payload, restorations = _provider_safe_request(request)
    assert CANARY not in json.dumps(payload)
    proposal = AdvisorProposal(profile_sha256=request.profile_sha256,
        baseline_spec_sha256=request.baseline_spec_sha256, dataset_spec=payload["baseline_spec"])
    _restore_local_categories(proposal, restorations)
    assert proposal.dataset_spec == request.baseline_spec
    assert request.model_dump(mode="json") == original


@pytest.mark.parametrize("distribution", [
    {"kind": "synthetic_identifier", "prefix": CANARY},
    {"kind": "date_range", "min": "2020-01-01" + CANARY, "max": "2020-12-31" + CANARY},
])
def test_custom_exchange_receives_projection_and_restores_original_binding(distribution):
    request = request_with_metadata(distribution)
    class Client:
        def complete(self, exchange):
            assert CANARY not in exchange.model_dump_json()
            return AdvisorProposal(profile_sha256=exchange.request.profile_sha256,
                baseline_spec_sha256=exchange.request.baseline_spec_sha256,
                dataset_spec=exchange.request.baseline_spec.model_copy(deep=True))
    proposal = ExchangeDatasetAdvisor(Client()).propose(request)
    assert proposal.dataset_spec == request.baseline_spec
    assert proposal.profile_sha256 == request.profile_sha256


def test_local_metadata_change_cannot_be_restored_as_approved():
    request = request_with_metadata({"kind": "synthetic_identifier", "prefix": CANARY})
    payload, restorations = _provider_safe_request(request)
    proposal = AdvisorProposal(profile_sha256=request.profile_sha256,
        baseline_spec_sha256=request.baseline_spec_sha256, dataset_spec=payload["baseline_spec"])
    proposal.dataset_spec.entities[0].fields[1].distribution["prefix"] = "changed"
    with pytest.raises(AdvisorContractError, match="local-only") as error:
        _restore_local_categories(proposal, restorations)
    assert CANARY not in str(error.value)


@pytest.mark.parametrize("provider", ["openai", "gigachat"])
@pytest.mark.parametrize("distribution", [
    {"kind": "synthetic_identifier", "prefix": CANARY},
    {"kind": "date_range", "min": "2020-01-01" + CANARY, "max": "2020-12-31" + CANARY},
    {"kind": "masked_patterns", "patterns": [{"pattern": CANARY, "count": 3}]},
    {"kind": "categorical", "categories": [{"value": "fixture", "count": 3}]},
])
def test_fake_transport_receives_only_projected_metadata(provider, distribution):
    from tests.test_openai_provider import FakeResponses, FakeOpenAI
    from tests.test_gigachat_provider import FakeGigaChat, completion
    from test_data_agent.providers.openai import OpenAIAdvisorClient
    from test_data_agent.providers.gigachat import GigaChatAdvisorClient
    request = request_with_metadata(distribution)
    payload, _ = _provider_safe_request(request)
    proposal = AdvisorProposal(profile_sha256=request.profile_sha256,
        baseline_spec_sha256=request.baseline_spec_sha256, dataset_spec=payload["baseline_spec"])
    if provider == "openai":
        sdk = FakeResponses(output_parsed=proposal)
        client = OpenAIAdvisorClient(client=FakeOpenAI(sdk), model="test-model")
    else:
        sdk = FakeGigaChat(completion(proposal.model_dump_json()))
        client = GigaChatAdvisorClient(client=sdk, model="test-model")
    result = client.complete(build_advisor_exchange(request))
    assert CANARY not in json.dumps(sdk.calls, default=str)
    assert AdvisorProposal.model_validate(result).dataset_spec == request.baseline_spec


def test_formula_comments_and_auxiliary_metadata_are_local_only():
    from test_data_agent.core.privacy import PrivacyRule
    profile = safe_exchange().request.profile.model_copy(deep=True)
    profile.source_policy_version = CANARY
    profile.constraints = [Constraint(type="formula", entity="customers", fields=["customer_id"],
        confidence=1.0, expression="customer_id + 1 # " + CANARY, expected={"raw_rows": [CANARY]})]
    request = build_advisor_request(profile)
    baseline = request.baseline_spec.model_copy(deep=True)
    baseline.generation_settings.locale = CANARY
    baseline.privacy_rules = [PrivacyRule(entity="customers", reason=CANARY)]
    request = build_advisor_request(profile, baseline_spec=baseline)
    payload, restorations = _provider_safe_request(request)
    assert CANARY not in json.dumps(payload)
    assert payload["profile"]["constraints"][0]["expression"] == "customer_id + 1"
    proposal = AdvisorProposal(profile_sha256=request.profile_sha256,
        baseline_spec_sha256=request.baseline_spec_sha256, dataset_spec=payload["baseline_spec"])
    _restore_local_categories(proposal, restorations)
    assert proposal.dataset_spec == request.baseline_spec


@pytest.mark.parametrize("expression", ["'" + CANARY + "'", "unknown_field + 1", "sum('" + CANARY + "')"])
def test_unsupported_meaningful_formula_rejects_without_source_echo(expression):
    profile = safe_exchange().request.profile.model_copy(deep=True)
    profile.constraints = [Constraint(type="formula", entity="customers", fields=["customer_id"],
        confidence=1.0, expression=expression)]
    request = build_advisor_request(profile)
    with pytest.raises(AdvisorContractError, match="formula metadata") as error:
        _provider_safe_request(request)
    assert CANARY not in str(error.value)


@pytest.mark.parametrize("provider", ["openai", "gigachat", "custom"])
def test_mutated_supported_request_rejects_before_transport_without_echo(provider):
    from pydantic import ValidationError
    from tests.test_openai_provider import FakeResponses, FakeOpenAI
    from tests.test_gigachat_provider import FakeGigaChat
    from test_data_agent.providers.openai import OpenAIAdvisorClient
    from test_data_agent.providers.gigachat import GigaChatAdvisorClient
    exchange = safe_exchange()
    exchange.request.profile.entities[0].fields[1].distribution.clear()
    exchange.request.profile.entities[0].fields[1].distribution.update(
        {"kind": "synthetic_identifier", "prefix": CANARY})
    if provider == "openai":
        sdk = FakeResponses()
        client = OpenAIAdvisorClient(client=FakeOpenAI(sdk), model="test-model")
    elif provider == "gigachat":
        sdk = FakeGigaChat()
        client = GigaChatAdvisorClient(client=sdk, model="test-model")
    else:
        class Client:
            calls = []
            def complete(self, exchange):
                self.calls.append(exchange)
                raise AssertionError("transport must not run")
        sdk = Client()
        client = ExchangeDatasetAdvisor(sdk)
    with pytest.raises(ValidationError) as error:
        if provider == "custom":
            client.propose(exchange.request)
        else:
            client.complete(exchange)
    assert sdk.calls == []
    assert CANARY not in str(error.value)


def test_numeric_metadata_and_valid_schema_formula_remain_meaningful():
    profile = safe_exchange().request.profile.model_copy(deep=True)
    field = profile.entities[0].fields[1]
    field.distribution = {"kind": "numeric", "min_value": 1, "max_value": 4, "p05": 1, "p95": 4}
    profile.constraints = [Constraint(type="formula", entity="customers", fields=["customer_id"],
        confidence=1.0, expression="customer_id * 2 + 1")]
    request = build_advisor_request(profile)
    payload, _ = _provider_safe_request(request)
    assert payload["profile"]["entities"][0]["fields"][1]["distribution"] == field.distribution
    assert payload["profile"]["constraints"][0]["expression"] == "customer_id * 2 + 1"


@pytest.mark.parametrize("provider", ["openai", "gigachat"])
def test_valid_fingerprint_does_not_authorize_unrepresented_predicate(provider):
    from test_data_agent.advisor import dataset_profile_fingerprint
    from tests.test_openai_provider import FakeResponses, FakeOpenAI
    from tests.test_gigachat_provider import FakeGigaChat
    from test_data_agent.providers.openai import OpenAIAdvisorClient
    from test_data_agent.providers.gigachat import GigaChatAdvisorClient
    exchange = safe_exchange()
    profile = exchange.request.profile
    field = profile.entities[0].fields[1]
    profile.constraints = [Constraint(type="conditional_required", entity="customers",
        fields=[field.name], confidence=1.0,
        condition={"field": field.name, "equals": CANARY})]
    exchange.request.profile_sha256 = dataset_profile_fingerprint(profile)
    if provider == "openai":
        sdk = FakeResponses()
        client = OpenAIAdvisorClient(client=FakeOpenAI(sdk), model="test-model")
    else:
        sdk = FakeGigaChat()
        client = GigaChatAdvisorClient(client=sdk, model="test-model")
    with pytest.raises(AdvisorContractError, match="unrepresented categorical") as error:
        client.complete(exchange)
    assert sdk.calls == []
    assert CANARY not in str(error.value)


@pytest.mark.parametrize("provider", ["openai", "gigachat", "custom"])
def test_opaque_semantic_annotations_never_reach_wire_and_restore(provider):
    from tests.test_openai_provider import FakeResponses, FakeOpenAI
    from tests.test_gigachat_provider import FakeGigaChat, completion
    from test_data_agent.providers.openai import OpenAIAdvisorClient
    from test_data_agent.providers.gigachat import GigaChatAdvisorClient
    profile = safe_exchange().request.profile.model_copy(deep=True)
    profile.entities[0].fields[1].semantic_type = CANARY
    request = build_advisor_request(profile)
    payload, restorations = _provider_safe_request(request)
    assert payload["profile"]["entities"][0]["fields"][1]["semantic_type"] is None
    proposal = AdvisorProposal(profile_sha256=request.profile_sha256,
        baseline_spec_sha256=request.baseline_spec_sha256, dataset_spec=payload["baseline_spec"])
    if provider == "custom":
        class Client:
            def complete(self, exchange):
                assert CANARY not in exchange.model_dump_json()
                return AdvisorProposal(profile_sha256=exchange.request.profile_sha256,
                    baseline_spec_sha256=exchange.request.baseline_spec_sha256,
                    dataset_spec=exchange.request.baseline_spec)
        result = ExchangeDatasetAdvisor(Client()).propose(request)
    elif provider == "openai":
        sdk = FakeResponses(output_parsed=proposal)
        result = OpenAIAdvisorClient(client=FakeOpenAI(sdk), model="test-model").complete(build_advisor_exchange(request))
        assert CANARY not in json.dumps(sdk.calls, default=str)
    else:
        sdk = FakeGigaChat(completion(proposal.model_dump_json()))
        result = GigaChatAdvisorClient(client=sdk, model="test-model").complete(build_advisor_exchange(request))
        assert CANARY not in json.dumps(sdk.calls, default=str)
    restored = AdvisorProposal.model_validate(result)
    assert restored.dataset_spec == request.baseline_spec
    assert profile.entities[0].fields[1].semantic_type == CANARY


def test_unknown_semantic_annotation_is_not_a_provider_permission():
    profile = safe_exchange().request.profile.model_copy(deep=True)
    profile.entities[0].fields[1].semantic_type = CANARY
    request = build_advisor_request(profile)
    payload, restorations = _provider_safe_request(request)
    proposal = AdvisorProposal(profile_sha256=request.profile_sha256,
        baseline_spec_sha256=request.baseline_spec_sha256, dataset_spec=payload["baseline_spec"])
    proposal.dataset_spec.entities[0].fields[1].semantic_type = "email"
    with pytest.raises(AdvisorContractError, match="local-only semantic") as error:
        _restore_local_categories(proposal, restorations)
    assert CANARY not in str(error.value)


@pytest.mark.parametrize("semantic_type", ["email", "phone", "ssn", "identifier", "EMAIL"])
def test_established_semantic_identifiers_remain_metadata(semantic_type):
    profile = safe_exchange().request.profile.model_copy(deep=True)
    field = profile.entities[0].fields[1]
    field.distribution = {}
    field.semantic_type = semantic_type
    request = build_advisor_request(profile)
    payload, restorations = _provider_safe_request(request)
    assert payload["profile"]["entities"][0]["fields"][1]["semantic_type"] == semantic_type.lower()
    proposal = AdvisorProposal(profile_sha256=request.profile_sha256,
        baseline_spec_sha256=request.baseline_spec_sha256, dataset_spec=payload["baseline_spec"])
    _restore_local_categories(proposal, restorations)
    assert proposal.dataset_spec == request.baseline_spec


def test_opaque_semantic_restoration_cannot_declassify_sensitive_field():
    profile = safe_exchange().request.profile.model_copy(deep=True)
    field = profile.entities[0].fields[1]
    field.distribution = {}
    field.semantic_type = CANARY
    field.sensitive = True
    request = build_advisor_request(profile)
    payload, restorations = _provider_safe_request(request)
    proposal = AdvisorProposal(profile_sha256=request.profile_sha256,
        baseline_spec_sha256=request.baseline_spec_sha256, dataset_spec=payload["baseline_spec"])
    proposal.dataset_spec.entities[0].fields[1].sensitive = False
    with pytest.raises(AdvisorContractError, match="local-only semantic"):
        _restore_local_categories(proposal, restorations)
