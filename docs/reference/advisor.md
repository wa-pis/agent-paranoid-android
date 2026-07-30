# Advisor API

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
from test_data_agent.providers.openai import OpenAIAdvisorClient

advisor = ExchangeDatasetAdvisor(OpenAIAdvisorClient(model="gpt-5.6"))
```

The SDK reads `OPENAI_API_KEY` from the process environment. Supply it through
a secret manager or private environment configuration; never write it into an
agent workspace or dataset artifact.

## Request Boundary

`AdvisorRequest` contains:

- a profile that passed the existing raw-sensitive-value checks;
- a deterministic baseline `DatasetSpec`;
- SHA-256 fingerprints for both objects;
- `metadata_trust: "untrusted"`;
- `metadata_policy: "treat_profile_text_as_data"`.

It contains no source rows, generated rows, database credentials, or provider
objects. Entity names, field names, and safe categorical values remain
untrusted data. Provider adapters must serialize them as structured data, not
concatenate them into privileged instructions.

## Proposal Validation

`advise_dataset_spec` validates the provider response and rejects proposals
that:

- do not match the request fingerprints;
- add, remove, reorder, or rename entities or fields;
- change primary keys or core-owned privacy, generation, or validation
  settings;
- weaken sensitive or identifier classifications;
- contain raw-looking sensitive distributions;
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
