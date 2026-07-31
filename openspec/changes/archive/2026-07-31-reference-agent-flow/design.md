# Design: reference-agent-flow

The example is intentionally application code rather than another core
orchestration abstraction:

1. `plan` detects the source, persists the normal agent plan, calls
   `ExchangeDatasetAdvisor`, and stops awaiting approval.
2. `status` uses the read-only workspace inspection API.
3. `approve` passes an explicit reviewed SHA-256 to the existing approval
   gate, which performs deterministic generation and validation.

`BaselineAdvisorClient` implements `AdvisorExchangeClient` and returns the
baseline spec unchanged. It is safe, deterministic, and replaceable with a
provider-specific structured-output client. No model SDK enters the base
package.

The example emits existing typed JSON results. It does not add a parallel
workspace format, proposal schema, approval path, or generation engine.
