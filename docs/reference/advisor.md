# Advisor API

The advisor API is a small provider-neutral boundary for model-assisted
`DatasetSpec` proposals. It does not call an LLM, persist a plan, approve a
plan, or generate rows.

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
