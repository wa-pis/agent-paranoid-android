# Change Proposal: installed-demo-and-product-clarity

## Summary

Add a self-contained `test-data-agent demo --output PATH` workflow that works
after a normal package installation. The demo uses only a small synthetic
fixture shipped in the wheel, produces a deterministic generated dataset, and
reports the created artifacts without requiring the source repository,
network, OpenAI, MCP, Trino, or optional dependencies.

Use the same workflow to make the first README screen outcome-oriented: show a
small input, one command, representative synthetic output, preserved
properties, and explicit non-guarantees.

## Motivation

The current quickstarts are useful for repository development but depend on
fixtures checked into the source tree. A PyPI user needs a safe first run that
proves the package is installed and usable without making the user discover
internal test data or integrations first.

## Scope

In scope:

- Add the `demo` CLI command with an explicit output path and deterministic seed.
- Ship a fictional, non-sensitive demo fixture as a wheel resource.
- Reuse the public profiling/spec/generation/validation path where practical.
- Write output through the existing bounded and atomic artifact conventions.
- Reject an existing output directory unless an explicit overwrite contract is
  introduced and documented.
- Add isolated-wheel smoke coverage and failure-path tests.
- Make the README demo the primary first workflow and document preserved and
  intentionally non-preserved properties.

Out of scope:

- New providers, MCP tools, Trino access, network calls, or OpenAI dependency
  requirements.
- Using fixtures from `tests/` or copying any source rows into output.
- A hosted demo service or a second generation engine.
- Statistical anonymity, re-identification resistance, or a privacy
  certification claim.

## Safety Impact

- The bundled fixture must be fictional and safe to publish.
- The command must remain deterministic, offline, and seed-controlled.
- Generated output must report `synthetic: true` and
  `source_rows_copied: false`.
- Existing output and partial failures must not produce a successful-looking
  incomplete bundle.
- The demo must exercise the same safety and validation boundaries as normal
  package workflows.

## Compatibility

- This adds a CLI command and packaged resource without changing existing
  commands, exit codes, or artifact contracts.
- The demo output layout becomes a documented example contract and should be
  versioned if consumers begin to rely on individual filenames.
- The wheel must remain usable without optional extras.
