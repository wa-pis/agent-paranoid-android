# Change Proposal: 1-2-0-json-depth-preparse-bound

## Summary

Apply the existing local JSON-depth budget before materializing JSON datasets,
profile/spec imports, and profile-cache documents.

## Motivation

Dataset JSON was checked only after `json.loads`, while JSON profile/spec and
cache importers did not uniformly enforce the depth budget. An adversarially
nested but byte-bounded document could therefore consume parser work before the
application rejected it, leaving accepted Low finding FS-11 open.

## Scope

In scope:

- Add one non-recursive structural-depth scan before local JSON parsing.
- Reuse `TEST_DATA_AGENT_MAX_JSON_DEPTH` for datasets, profile/spec imports, and
  profile caches.
- Preserve normal JSON syntax validation in the standard-library parser.
- Add synthetic regressions and update public resource-budget documentation.

Out of scope:

- Replacing the standard-library JSON parser.
- Adding a streaming JSON dependency.
- Changing JSON byte, row, cell, or scalar-length budgets.
- Changing provider, MCP, database, or generated-output behavior.

## Safety Impact

Excessive nesting fails closed before nested Python objects or Pydantic models
are materialized. No partial dataset, profile, spec, or cache value is returned.

## Compatibility

The existing depth setting now applies uniformly to whole JSON document
structure. Defaults and accepted normal inputs remain unchanged; deliberately
low custom limits may reject documents whose root containers were previously
not counted by the dataset-only post-parse check.

## Release Impact

This changes a local input security boundary and therefore requires the next
release candidate. This change does not create a tag or publish artifacts.
