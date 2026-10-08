# Agent and advisor guide

Read this guide for `agent-plan`, advisor providers, OpenAI integration,
confidence/evidence, or relationship discovery.

The agent layer may plan work and produce typed specifications or hypotheses.
It must not bypass deterministic safety, generation, validation, approval, or
audit boundaries.

Advisor requests should have typed, bounded settings for model/reasoning,
prompt/input bytes or tokens, output tokens, timeout, retries, and total
invocation work. Account for the complete provider request, not only the
serialized application payload. Record bounded, redacted metrics; never log
credentials, prompts, source values, or secrets.

Inferred facts and relationships must carry evidence and confidence. AI
relationship assistance may rank or explain candidates supplied by the local
profiler, but it must not invent tables, fields, source rows, or relationships;
mutate a `DatasetSpec` directly; or auto-approve a result. Candidate identity,
kind, and referenced fields must be checked deterministically, and the result
must remain explicitly review-gated.

Provider adapters should remain optional and provider-neutral at the contract
boundary. Normal tests use fake transports and synthetic profiles; no
production data or private infrastructure context may be sent to an external
provider.

Local category preservation does not weaken this boundary. Even when a
reviewed field keeps an explicitly allowlisted business enum for deterministic
generation, every provider-bound source literal uses a field-scoped synthetic
label and is restored only inside the fingerprint-bound local review flow.

Categorical constraint predicates are part of the same provider-bound data as
their distributions. Replace every string, number, boolean, or null category
and matching `equals`, `not_equals`, or `in_values` value with field-scoped
labels before serialization. Reject values outside that field's categorical
domain; numeric distribution bounds remain unchanged.

OpenAI and GigaChat apply the same category projection immediately before transport. The original request and fingerprints remain local and unchanged. Unrepresented local categorical predicates reject before sending; invalid restored proposals produce redacted invalid-response errors. Provider byte budgets include the serialized labels.

Imported field distributions must be empty metadata objects or declare a
supported typed distribution kind. Nonempty opaque objects, missing kinds
and unsupported kinds are rejected before advisor/provider serialization.
The same contract applies to profiles and generation specifications; generic
errors must not reproduce rejected source contents.

Provider-bound metadata uses a shared semantic projection. Opaque condition
extras, unused constraint members, identifier prefix/pattern text and local
auxiliary annotations are not provider input. Date bounds and formula syntax
are canonicalized; represented categorical predicates still use field-scoped
labels. Only established semantic classifications are provider metadata;
unknown semantic annotations remain local. Schema identifiers remain
confidential metadata, so operators must choose the recipient accordingly. Local immutable
metadata and original fingerprints may be restored only after the returned
proposal matches its projected immutable contract; projection cannot grant new
proposal or approval authority. Custom exchange clients use the same boundary.
