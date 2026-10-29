# Documentation consistency audit — 2026-10-29

This audit reconciles the maintained guide with published stable 1.6.0,
candidate 1.7.0rc1 and their executable contracts. Input is main
`b8524e8dc61902df702b926cf714adb4c4b6d217` (PR #657); corrections are recorded
in the documentation-only continuation. Package source remains the signed
`64b7c8c3bbb0174fd7e159c4dfb42312045a1716`. No runtime, dependency, schema,
permission or accepted architectural decision changes.

## Scope and method

The tracked Markdown inventory at that input has 684 files:

| Group | Files | Treatment |
| --- | ---: | --- |
| English guide, history and maintenance | 142 | Current contract/status checks; dated evidence retains its original identity. |
| Russian guide | 48 | Corresponding workflows, release status, constraints and deferred scope; shorter pages may link the canonical English reference. |
| Root and other instructions | 10 | Safety, contributor/release policy, release notes and entrypoints. |
| Agent instructions and prompts | 11 | Source-free planning, review, local-only preservation authority and transport restrictions. |
| Runnable example guides | 8 | Paths and maintained executable fictional examples. |
| Active proposals and checkpoints | 64 | Current task reconciliation takes precedence over dated progress. |
| Archived proposals | 375 | Historical, not current feature promises or authority. |
| Baseline specifications | 24 | Shipped contract, conditional scenarios and compatibility requirements. |
| Test-fixture documentation | 2 | Golden-contract provenance and immutable compatibility baseline. |

Inventory is reproducible with `git ls-files '*.md'` at the input commit.
Repository-wide status/contract searches identify candidate discrepancies;
focused semantic review and executable checks cover the surfaces below.
This is a consistency audit, not a claim that every historical paragraph was
manually re-reviewed or that every possible runtime combination was executed.

| Surface | Cross-check |
| --- | --- |
| README, installation, CSV/related-table quickstarts, examples | Recommended stable versus explicit candidate install; parser commands, fictional fixtures and five maintained live-example tests. |
| CLI help, Python exports, MCP inventories and schemas | `test_cli_parser_contract.py`, `test_contract_fixtures.py`, `test_dataset_spec_contract.py`; documentation command and tool inventory checks. Golden fixtures remain unchanged. |
| Source adapters, configuration, Trino Basic authentication | Source/output matrix, configuration/auth references, bounded local/category evidence, safe error recovery and fictional installed feedback ledger. TLS and secret indirection remain required; no live authentication claim. |
| Generation, rules, profiles, manifests and reports | DatasetSpec 1.1, numeric confidence, independent synthetic ranges, utility versus conformance, mixed-origin versus synthetic provenance, negative-mode exit/report semantics. |
| Privacy, security, prompts and agent guidance | Source-free generation and aggregate defaults; separate opt-in row surface; exact local receipt authority, no MCP issuer, mapping exception and unchanged preservation restrictions. |
| Architecture and ownership | Public import/entrypoint inventories, application architecture and activation-patch compatibility tests; retrospective ADRs are not current WIP declarations. |
| Troubleshooting, support and dependency profiles | Fixed recovery paths, doctor local-only behavior, reviewed minimum/locked environments and separate later installed replay. |
| Roadmaps, OpenSpec, changelog and release guidance | Delivered candidate features versus remaining evidence/deferred scope; original source identities, immutable release artifacts, versioned guide and stable retention. |
| English/Russian navigation and portable documentation | Local links and strict MkDocs; publication tests cover version identities, aliases, downloads, bilingual chapters/search, provenance and retained stable content. |

## Corrections

- Root agent instructions now distinguish completed finite stable acceptance,
  published candidate and still-required review of changed activation.
- MCP permissions no longer describe the completed stable campaign as future.
- ADR index/open-question register and transformation boundary explicitly identify
  historical WIP/pre-activation statements and link later source-bound evidence.
  Unresolved decisions and the separate trust-amendment task remain unresolved.
- The proposed richer evidence envelope is explicitly unimplemented. Current
  relationship/constraint confidence is numeric; illustrative `medium` is not
  a supported serialized value. The Russian reference carries the same warning.
- Dependency compatibility names its reviewed lock and exact-source gate instead
  of an obsolete gate date. All ten documented direct versions match both
  `uv.lock` and the machine-readable compatibility policy; no dependency update.
- Both roadmaps move completed numeric/relational/statistics/CLI and versioned
  documentation delivery out of the pending list. Historical evidence gaps,
  capacity and amendment review stay visible. Monthly-date inference,
  configurable category ceiling and source-row EAV pivot/unpivot remain deferred.

Historical release reports, archived proposals, immutable golden fixtures and
legacy deep-link anchors remain intact. Conditional OpenSpec scenarios about
an incomplete campaign still describe that condition, not current release status.

## Verification and limits

- 151 documentation/architecture/activation/CLI/Python/MCP/schema/dependency and
  fictional-example tests passed in the existing test environment. The initial
  run skipped the documentation-build module because MkDocs was absent there.
- All 24 documentation-build tests then passed in a separate environment synced
  from the reviewed lock with docs and dev dependencies. No module remains
  skipped in this selected scope.
- Strict MkDocs succeeded with the complete locked docs environment. Preliminary
  attempts in other existing environments stopped at missing MkDocs/mike before
  building; they were tooling setup failures, not successful validation.
- All 29 strict OpenSpec items passed. The template's informational archive note
  is not a completed product change. Whitespace validation passed.

No new live database/provider call, dataset approval, security scan, private-input
replay, UI campaign or target-size capacity run is claimed. Existing installed
[feedback evidence](feedback-acceptance-1.7.0rc1.md) is reused with its scope.
PR CI and publication bind their own exact documentation revision; local checks
alone do not assert that these edits are already on the public site.

The whole-documentation consistency task is complete for this inventory and
contract scope. Four active changes remain with five unchecked tasks: three
entries for two unavailable historical evidence gaps, plus final-public route
capacity and the separately tracked trust-boundary amendment review. The
transformation proposal remains active; this audit is not archival of unfinished
work or authority for a new exception.
