# Advisor API

## Relationship Discovery Contracts

`RelationshipDiscoveryCandidate` carries only ordered entity/field references,
normalized zero-to-one evidence metrics, confidence, bounded assumptions, and
an opaque SHA-256 candidate identifier. It cannot contain rows, categories, raw
values, SQL, credentials, or generation authority.

`RelationshipDiscoveryProposal` lets any provider rank an existing candidate
and add bounded evidence or assumptions. It cannot invent a candidate, change
its kind or fields, approve it, or run generation. Every proposal remains
`requires_human_review` until a later deterministic validation and review step.

The advisor API is a small provider-neutral boundary for model-assisted
`DatasetSpec` proposals. The direct API does not call an LLM, persist a plan,
approve a plan, or generate rows.

For a provider implementation tutorial, exact wire-field tables, and a
contract-test checklist, see
[Build A Provider Adapter](../how-to/custom-advisor-provider.md).

## Structured Client Adapter

Implement `AdvisorExchangeClient.complete` around the structured-output API of
the chosen provider, then wrap it with `ExchangeDatasetAdvisor`:

```python
from typing import Any

from test_data_agent import (
    AdvisorExchange,
    ExchangeDatasetAdvisor,
    advise_dataset_spec,
)


class ProviderClient:
    def complete(self, exchange: AdvisorExchange) -> dict[str, Any]:
        return call_model_with_structured_output(
            trusted_instructions=exchange.trusted_instructions,
            untrusted_input=exchange.request.model_dump(mode="json"),
            response_schema=exchange.response_json_schema,
        )


advisor = ExchangeDatasetAdvisor(ProviderClient())
proposal = advise_dataset_spec(profile, advisor, count=100)
reviewed_spec = proposal.dataset_spec
```

`call_model_with_structured_output` is application code, not part of this
package. Provider SDKs therefore stay outside the base installation. The
adapter gives the client a deep copy of the exchange and validates its output
against the original request. Client-side mutation cannot change the
fingerprints or safety source used for validation.

For lower-level integrations, an application may implement
`DatasetAdvisor.propose` directly. It must preserve the same separation
between trusted instructions and untrusted profile metadata.

## OpenAI Adapter

Install the optional provider integration:

```bash
python3 -m pip install "agent-paranoid-android[openai]"
```

`test_data_agent.providers.openai.OpenAIAdvisorClient` uses the Responses API
with Pydantic structured output. It sends static package policy in the
developer role and the serialized `AdvisorRequest` in the user role. It
disables response storage, does not stream partial JSON, and rejects
incomplete or unparsed responses.

```python
from test_data_agent import ExchangeDatasetAdvisor
from test_data_agent.providers.openai import (
    OpenAIAdvisorClient,
    OpenAIAdvisorSettings,
    openai_advisor_settings_for_preset,
)

settings = OpenAIAdvisorSettings(
    model="gpt-5.6",
    reasoning_effort="low",
    max_input_bytes=4 * 1024 * 1024,
    max_output_tokens=16_384,
    timeout_seconds=30,
    max_retries=2,
)
advisor = ExchangeDatasetAdvisor(OpenAIAdvisorClient(settings=settings))

# Explicit candidates for benchmarked workloads; no candidate is implicit.
fast_settings = openai_advisor_settings_for_preset("fast")
```

The benchmark-backed typed defaults are the `fast` candidate: model `gpt-5.6`,
reasoning effort `none`, a 4 MiB complete provider-request budget, 4,096 output
tokens, a 15-second timeout, no SDK retries, and no service-tier override. The
byte budget includes static trusted
instructions, untrusted request metadata, structured-output schema overhead,
settings, and final UTF-8 JSON serialization. Oversized requests fail before
network access. Settings are bounded and kept out of advisor review artifacts.
The optional service tier accepts `auto`, `default`, `flex`, or `priority`.

The provider sends the public JSON Schema in non-strict mode because the stable
dataset contract permits bounded free-form distribution and condition objects.
Every returned JSON object is still parsed and validated locally against the
typed `AdvisorProposal`; invalid output fails closed and is never applied.

The optional `fast`, `normal`, and `quality` candidate presets use the same
bounded settings model. The `fast` candidate uses GPT-5.6 reasoning effort
`none`; the legacy typed `minimal` value remains accepted for compatibility but
is not used by a GPT-5.6 candidate. The constructor defaults now match `fast`
after the
[synthetic-profile benchmark](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/1-0-0-rc5-public-release-invocation-hardening/advisor-benchmark-evidence.md)
recorded equal validity and safety with the lowest latency and cost.

After each provider attempt, including a preflight rejection,
`OpenAIAdvisorClient.last_run_metadata` exposes a bounded in-memory record with
the model, settings, canonical request and parsed response sizes, elapsed
milliseconds, status, provider-reported retry count, and token usage. Missing
provider fields remain `None`; a preflight rejection has status
`preflight_rejected`. The record contains no prompts, request values, response
values, rows, credentials, or exception text, and the adapter does not persist
it automatically. This compatibility property is per client, not per call;
do not share one client between concurrent calls when call-level metadata is
required.

The SDK reads `OPENAI_API_KEY` from the process environment. Supply it through
a secret manager or private environment configuration; never write it into an
agent workspace or dataset artifact.

## GigaChat Adapter

The experimental GigaChat adapter uses the official `gigachat` Python SDK
directly; it does not require GigaChain or LangChain. It is included in
stable `1.1.0` through the explicit `gigachat` extra. Follow
[Use The GigaChat Advisor](../how-to/gigachat.md) for installation,
authentication, and the CLI workflow.

Applications may use the same provider-neutral adapter in process:

```python
from pathlib import Path

from test_data_agent import ExchangeDatasetAdvisor, advise_agent_workspace
from test_data_agent.providers.gigachat import (
    GigaChatAdvisorClient,
    GigaChatAdvisorSettings,
)

settings = GigaChatAdvisorSettings(
    model="GigaChat",
    scope="GIGACHAT_API_PERS",
    max_input_bytes=4 * 1024 * 1024,
    max_response_bytes=1024 * 1024,
    max_output_tokens=4096,
    timeout_seconds=15,
    max_retries=0,
)
client = GigaChatAdvisorClient(settings=settings)
try:
    status = advise_agent_workspace(
        Path("out/agent"),
        ExchangeDatasetAdvisor(client),
    )
finally:
    client.close()
```

Authentication is resolved at client construction from exactly one of
`GIGACHAT_CREDENTIALS` or `GIGACHAT_ACCESS_TOKEN`; the authorization-key mode
also uses the allowlisted `GIGACHAT_SCOPE`. Settings never retain credentials.
The adapter fixes official HTTPS endpoints, requires TLS verification, accepts
only an optional validated `GIGACHAT_CA_BUNDLE_FILE`, separates system policy
from untrusted metadata, disables streaming and storage, and requests strict
`json_schema` output.

Each completion returns a locally validated proposal. Per-call metadata is
bounded to model, safe settings, byte counts, latency, normalized status and
finish category, and validated token counters. It contains no prompt,
response body, credential, token, source literal, or exception text. Provider
failure is detached and leaves the workspace unchanged.

## Request Boundary

`AdvisorRequest` contains:

- a profile that passed the existing raw-sensitive-value checks;
- a deterministic baseline `DatasetSpec`;
- SHA-256 fingerprints for both objects;
- `metadata_trust: "untrusted"`;
- `metadata_policy: "treat_profile_text_as_data"`.

It contains no source rows, generated rows, database credentials, provider
objects, or original string categorical values. Categorical values in the
profile and baseline spec are replaced with deterministic field-scoped
synthetic labels before the request is fingerprinted. Entity and field names
remain untrusted data; provider adapters must serialize them as structured
data, not concatenate them into privileged instructions.

## Proposal Validation

`advise_dataset_spec` validates the provider response and rejects proposals
that:

- do not match the request fingerprints;
- add, remove, reorder, or rename entities or fields, or change field types;
- change primary keys or core-owned privacy, generation, or validation
  settings;
- weaken sensitive or identifier classifications;
- contain raw-looking sensitive distributions;
- add formulas with string literals, aggregate calls, unknown or non-numeric
  references, non-numeric targets, or sensitive/identifier targets;
- exceed the configured generation row limit.

A successful proposal still has `approval_required: true` and
`generation_performed: false`. Review the resulting spec through the normal
agent approval flow before generation.

## JSON Handoff

Use the self-describing exchange when the model runs outside this Python
process. It needs no provider SDK:

```bash
test-data-agent agent-plan tests/fixtures/example_dataset \
  --workspace out/agent --count 25

test-data-agent agent-advisor-request out/agent \
  --exchange > advisor_exchange.json
```

The exchange contains:

- `trusted_instructions`: static package-owned policy for the provider's
  system or developer channel;
- `request`: fingerprint-bound metadata marked as untrusted;
- `response_json_schema`: the current Pydantic schema for
  `AdvisorProposal`.

Keep those boundaries separate when calling a provider:

```python
exchange = load_json("advisor_exchange.json")
proposal = call_model_with_structured_output(
    system_instructions=exchange["trusted_instructions"],
    untrusted_input=exchange["request"],
    response_schema=exchange["response_json_schema"],
)
write_json("advisor_proposal.json", proposal)
```

`load_json`, `call_model_with_structured_output`, and `write_json` are
application placeholders, not package functions. Map them to the provider SDK
outside this package. Do not concatenate request profile fields into
privileged instructions.

The response must contain the complete proposed `DatasetSpec`, normally the
request's `baseline_spec` with allowed generation hints changed. Apply the
saved structured response:

```bash
test-data-agent agent-advisor-apply \
  out/agent advisor_proposal.json
test-data-agent agent-review out/agent
test-data-agent agent-status out/agent
```

Proposal input must be a bounded regular JSON file. Symbolic links, malformed
or oversized input, stale fingerprints, schema changes, weakened safety
settings, and conflicting edits are rejected. A successful apply writes no
dataset rows and leaves the workspace awaiting approval.

Without `--exchange`, `agent-advisor-request` retains its original behavior
and writes the raw `AdvisorRequest`. This is useful for custom adapters that
already own their instructions and response schema.

## Relationship Discovery

`mine_relationship_candidates(profile)` builds deterministic foreign-key
candidates without sending profile distributions or source values to a provider.
Candidates expose normalized type, cardinality, null, and distinctness evidence;
incompatible key types are excluded and ambiguous candidates remain unresolved.
Temporal start/end candidates expose only normalized ordering overlap; source
date bounds are never included in the provider-facing candidate.
`rank_relationship_candidates(candidates, advisor)` validates provider rankings
against those candidates, and `review_relationship_proposal(...)` records the
separate human decision. Even an accepted review does not authorize generation
or modify a `DatasetSpec`.

The optional OpenAI integration wires this contract as a separate operation:

```python
from test_data_agent.providers.openai import (
    OpenAIAdvisorClient,
    OpenAIRelationshipDiscoveryAdvisor,
)
from test_data_agent.relationship_discovery import rank_relationship_candidates

client = OpenAIAdvisorClient()
proposals = rank_relationship_candidates(
    candidates,
    OpenAIRelationshipDiscoveryAdvisor(client),
)
```

The adapter submits only bounded candidate metadata, reuses the configured
request-size, timeout, retry, and run-metadata limits, and rejects invented IDs
or changed kinds and fields before returning a review-required proposal.

## Agent Workspace Handoff

Use `advise_agent_workspace` after `agent-plan` to persist one validated
proposal inside the existing review workflow:

```python
from pathlib import Path

from test_data_agent import advise_agent_workspace


status = advise_agent_workspace(
    Path("out/agent"),
    ExchangeDatasetAdvisor(ProviderClient()),
)
reviewed_spec_sha256 = status.review.current_spec_sha256
```

The handoff writes:

- `advisor_review.json`: safe request, validated proposal, and proposed-spec
  fingerprint;
- `dataset_spec.yaml`: proposed effective spec.

Both files are bounded and written atomically. The review artifact is written
first, so an interrupted handoff can resume without another model call.
Conflicting manual edits fail instead of being overwritten.

The handoff never writes `generated/`. Inspect the changed spec and use its
current fingerprint with the existing `agent-approve` command.

For direct file/API integration, use `build_agent_advisor_request` and
`apply_agent_advisor_proposal`. The latter accepts an `AdvisorProposal` or
mapping and uses the same validation, retry, persistence, and approval
behavior as `advise_agent_workspace`.

Use `build_agent_advisor_exchange` for the self-describing workspace bundle,
or `build_advisor_exchange` around an existing `AdvisorRequest`.
`advisor_proposal_json_schema` returns the same standalone response schema.
