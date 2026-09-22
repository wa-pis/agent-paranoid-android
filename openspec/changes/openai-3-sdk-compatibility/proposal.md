# Change Proposal: openai-3-sdk-compatibility

## Summary

Evaluate OpenAI Python SDK 3.x before expanding the optional `openai` extra
from `<3.0.0` to `<4.0.0`. The range change must ship only after the adapter,
doctor smoke, supported-Python matrix, lockfile, and dependency compatibility
policy provide evidence for an identified 3.x release.

Dependabot PR #483 is therefore a tracked input to this work, not sufficient
compatibility evidence by itself. It remains deferred until the tasks in this
change are complete or is superseded by an implementation PR based on the
then-current `main` branch.

## Motivation

The OpenAI SDK is optional, but it implements a real provider boundary with
structured responses, bounded requests, redacted failures, and local review
gates. Declaring all future 3.x releases installable before exercising those
contracts would turn package metadata into an unsupported compatibility
promise and is intentionally rejected by the repository release gate.

## Scope

In scope:

- Select an identified stable OpenAI SDK 3.x release for evaluation.
- Exercise provider request, response, error, timeout, redaction, and doctor
  contracts without a live provider call.
- Update both OpenAI extra declarations, the reviewed compatibility policy,
  `uv.lock`, compatibility documentation, and release notes together.
- Run the complete supported-Python and release gates before declaring 3.x
  supported.
- Close or supersede PR #483 only after the evidence is reviewable.

Out of scope:

- Pre-authorizing unreleased or untested OpenAI SDK versions.
- Adding the OpenAI SDK to the base installation.
- Making AI mandatory for profiling, generation, validation, or export.
- Sending production data, source rows, credentials, or private infrastructure
  context to an external provider during compatibility testing.
- Changing provider-neutral advisor, `DatasetSpec`, CLI, MCP, or artifact
  contracts solely to make a dependency bump pass.

## Safety Impact

The compatibility evaluation must preserve the existing provider trust
boundary: only bounded safe metadata may enter an advisor request; responses
remain untrusted and review-only; credentials, prompts, provider text, source
values, and nested provider exceptions must not enter logs or public errors.
Tests use fake transports, placeholder credentials, and synthetic metadata, so
no live provider access or production data is required.

## Compatibility

Until this change is completed, `openai>=2.46.0,<3.0.0` remains the supported
package range. Completion may expand the optional extra to `<4.0.0` only for a
reviewed 3.x release and must not change the base package or provider-neutral
interfaces. Any required adapter migration is internal unless the evaluation
identifies a public contract change, which requires a separate OpenSpec.
