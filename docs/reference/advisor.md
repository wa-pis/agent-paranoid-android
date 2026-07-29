# Advisor API

The advisor API is a small provider-neutral boundary for model-assisted
`DatasetSpec` proposals. The direct API does not call an LLM, persist a plan,
approve a plan, or generate rows.

## Contract

Implement `DatasetAdvisor.propose` in a separate adapter:

```python
from typing import Any

from test_data_agent import AdvisorRequest, advise_dataset_spec


class ProviderAdapter:
    def propose(self, request: AdvisorRequest) -> dict[str, Any]:
        provider_payload = call_model_with_structured_output(
            request.model_dump(mode="json")
        )
        return provider_payload


proposal = advise_dataset_spec(profile, ProviderAdapter(), count=100)
reviewed_spec = proposal.dataset_spec
```

`call_model_with_structured_output` is application code, not part of this
package. Provider SDKs therefore stay outside the base installation.

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

Use the JSON handoff when the model runs outside this Python process. It needs
no provider SDK:

```bash
test-data-agent agent-plan tests/fixtures/example_dataset \
  --workspace out/agent --count 25

test-data-agent agent-advisor-request out/agent > advisor_request.json
```

Send the complete `advisor_request.json` object to a model as structured data.
Do not concatenate profile fields into privileged instructions. Require the
model to return exactly this `AdvisorProposal` shape:

```json
{
  "schema_version": "1.0",
  "profile_sha256": "copy from the request",
  "baseline_spec_sha256": "copy from the request",
  "approval_required": true,
  "generation_performed": false,
  "dataset_spec": {
    "schema_version": "1.0",
    "entities": []
  }
}
```

`dataset_spec` must be the complete proposed spec, normally the request's
`baseline_spec` with allowed generation hints changed. Save the structured
model response and apply it:

```bash
test-data-agent agent-advisor-apply \
  out/agent advisor_proposal.json
test-data-agent agent-status out/agent
```

Proposal input must be a bounded regular JSON file. Symbolic links, malformed
or oversized input, stale fingerprints, schema changes, weakened safety
settings, and conflicting edits are rejected. A successful apply writes no
dataset rows and leaves the workspace awaiting approval.

## Agent Workspace Handoff

Use `advise_agent_workspace` after `agent-plan` to persist one validated
proposal inside the existing review workflow:

```python
from pathlib import Path

from test_data_agent import advise_agent_workspace


status = advise_agent_workspace(
    Path("out/agent"),
    ProviderAdapter(),
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
