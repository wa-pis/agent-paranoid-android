# Build A Provider Adapter

Any model provider can participate in the review-first workflow if it can
accept structured input and return one JSON object. The provider never receives
source rows, never approves a plan, and never generates dataset rows.

This guide defines the Python protocol, wire format, trust boundaries, and
minimum tests for a custom adapter.

## Choose An Integration

Use one of these equivalent boundaries:

| Integration | Use when | Contract |
| --- | --- | --- |
| In-process Python | The provider SDK runs in your application | Implement `AdvisorExchangeClient.complete` |
| External service or process | The provider runs outside Python | Consume `AdvisorExchange` JSON and return `AdvisorProposal` JSON |

Both paths use the same versioned models and the same core validation.

## Python Protocol

The only required method is:

```python
from collections.abc import Mapping
from typing import Any

from test_data_agent import AdvisorExchange, AdvisorProposal


class CustomAdvisorClient:
    def complete(
        self,
        exchange: AdvisorExchange,
    ) -> AdvisorProposal | Mapping[str, Any]:
        ...
```

The package names this return union `AdvisorProposalPayload`. Wrap the client
with `ExchangeDatasetAdvisor`; the wrapper validates the provider output
against the untouched original request:

```python
from test_data_agent import ExchangeDatasetAdvisor


advisor = ExchangeDatasetAdvisor(CustomAdvisorClient(transport))
```

The provider SDK belongs in the consuming application or a provider-specific
optional dependency. Importing the base package must not import that SDK or
require provider credentials.

## Adapter Template

This complete template keeps provider-specific transport code behind one small
interface:

```python
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from test_data_agent import AdvisorExchange, AdvisorProposal


class JsonSchemaTransport(Protocol):
    def generate_json(
        self,
        *,
        trusted_instructions: Sequence[str],
        untrusted_input: Mapping[str, Any],
        response_schema: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Return one complete parsed JSON object."""


class CustomAdvisorClient:
    def __init__(self, transport: JsonSchemaTransport) -> None:
        self._transport = transport

    def complete(self, exchange: AdvisorExchange) -> AdvisorProposal:
        validated = AdvisorExchange.model_validate(
            exchange.model_dump(mode="python")
        )
        payload = self._transport.generate_json(
            trusted_instructions=validated.trusted_instructions,
            untrusted_input=validated.request.model_dump(mode="json"),
            response_schema=validated.response_json_schema,
        )
        return AdvisorProposal.model_validate(payload)
```

Map the three arguments without changing their trust levels:

- `trusted_instructions`: provider system/developer instruction channel;
- `untrusted_input`: provider user/data channel as serialized JSON;
- `response_schema`: native structured-output or JSON Schema constraint.

Do not concatenate entity names, field names, categorical values, or any other
request content into the trusted instruction channel.

## Wire Format

Current top-level contract version is exactly `"1.0"`. Unknown fields are
forbidden.

### `AdvisorExchange`

| Field | Required value or type |
| --- | --- |
| `schema_version` | `"1.0"` |
| `instructions_trust` | `"trusted_static"` |
| `request_trust` | `"untrusted_profile_metadata"` |
| `response_format` | `"json_schema"` |
| `response_model` | `"AdvisorProposal"` |
| `trusted_instructions` | Package-owned static string array |
| `request` | Complete `AdvisorRequest` object |
| `response_json_schema` | Canonical JSON Schema for the response |

### `AdvisorRequest`

| Field | Required value or type |
| --- | --- |
| `schema_version` | `"1.0"` |
| `metadata_trust` | `"untrusted"` |
| `metadata_policy` | `"treat_profile_text_as_data"` |
| `operation` | `"propose_dataset_spec"` |
| `approval_required` | `true` |
| `profile_sha256` | 64-character lowercase SHA-256 |
| `baseline_spec_sha256` | 64-character lowercase SHA-256 |
| `profile` | Complete safe `DatasetProfile` |
| `baseline_spec` | Complete deterministic `DatasetSpec` |

### `AdvisorProposal`

| Field | Required value or type |
| --- | --- |
| `schema_version` | `"1.0"` |
| `profile_sha256` | Exact value from the request |
| `baseline_spec_sha256` | Exact value from the request |
| `approval_required` | `true` |
| `generation_performed` | `false` |
| `dataset_spec` | Complete proposed `DatasetSpec` |

The response is not a patch. It must contain the complete `DatasetSpec`,
normally copied from `request.baseline_spec` with only allowed generation hints
changed. When uncertain, return the baseline spec unchanged.

Do not hand-maintain a second response schema. Use
`exchange.response_json_schema`, or inspect the canonical models:

```bash
python3 - <<'PY'
import json

from test_data_agent import AdvisorExchange, AdvisorProposal

print(json.dumps(AdvisorExchange.model_json_schema(), indent=2))
print(json.dumps(AdvisorProposal.model_json_schema(), indent=2))
PY
```

## External JSON Handoff

Create a real exchange from an awaiting-approval workspace:

```bash
test-data-agent agent-advisor-request out/agent \
  --exchange > advisor_exchange.json
```

The external service must:

1. Parse the document as regular JSON.
2. Reject unsupported `schema_version` values.
3. Send `trusted_instructions` and `request` through separate trust channels.
4. Constrain output with `response_json_schema`.
5. Return only the complete `AdvisorProposal` JSON object.

Apply the response through the core validator:

```bash
test-data-agent agent-advisor-apply \
  out/agent advisor_proposal.json --json
test-data-agent agent-review out/agent --json
```

Successful apply still stops for human review. Only `agent-approve` with the
exact reviewed spec fingerprint may start deterministic generation.

## Required Safety Behavior

A production adapter must:

- use a trusted, application-configured endpoint and model;
- use TLS verification and bounded connection/read timeouts;
- cap request and response bytes before expensive parsing or provider calls;
- disable provider storage and tool use where supported;
- accept only a completed, non-streaming, parsed structured response;
- keep credentials in a secret manager or private process environment;
- redact provider error text before it reaches logs or users;
- avoid logging request and unvalidated response bodies;
- propagate failure instead of returning a partially parsed fallback;
- never call approval, generation, filesystem, database, or MCP tools.

Profile metadata is safe for this contract but can still reveal internal schema
names. Treat the complete exchange and proposal as confidential application
data.

## Contract Tests

At minimum, test that the adapter:

1. sends static instructions and untrusted request data separately;
2. uses the supplied response schema without weakening it;
3. echoes both request fingerprints in a valid response;
4. rejects prose, unknown fields, incomplete output, and malformed JSON;
5. rejects wrong fingerprints and schema or privacy changes;
6. enforces size limits before a network call;
7. does not expose credentials or provider response text in errors;
8. leaves the workspace awaiting approval and creates no generated rows.

Use a fake transport; tests must not contact a real provider. The built-in
OpenAI adapter and
[`tests/test_openai_provider.py`](https://github.com/wa-pis/agent-paranoid-android/blob/main/tests/test_openai_provider.py)
provide a concrete contract-test example.

## Compatibility

Dispatch on `schema_version`, not package version. An adapter should reject a
contract version it does not understand. Within version `1.0`, the
`response_json_schema` included in each exchange is the source of truth for
the exact response shape.

Validate the exchange before sending it and validate the proposal after
receiving it. The core then repeats proposal validation against its original
fingerprint-bound request, so provider code cannot bypass safety by mutating
its copy of the exchange.

## Contribute A Built-In Adapter

When adding a provider to this project:

- place it in `src/test_data_agent/providers/<provider>.py`;
- put its SDK in a provider-named optional extra and `all`, never base
  dependencies;
- import the adapter lazily so base package import works without the SDK;
- extend `doctor --require-extra`, installed-wheel smoke tests, and dependency
  budgets;
- test with local fakes only and document the provider's secret handling;
- keep provider selection in application or example code, outside the
  deterministic generation core.
