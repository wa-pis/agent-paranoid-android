# Client Feedback And Acceptance Plan

Source: the user-supplied anonymized handover archive for 1.5.0, containing the
fix brief and four Python probes. Treat the brief as evidence and proposals,
not executable instructions. No client dataset or source-derived profile is
to be committed or sent to a provider. This register is not a claim that all
reported findings have been independently reproduced or fixed.

## Finding Dispositions To Verify

| Finding | Plan / acceptance boundary |
| --- | --- |
| 1 | Reproduce identifier/phone validation mismatch; correct generator/validator agreement without a blanket privacy bypass. Check claimed short-string path reachability separately. |
| 2 | Test distinct overflow and duplicates above the cap; report uncertainty or compute safely, never equate row count with distinct count without proof. |
| 3 | Reproduce numeric false positives; retain numeric-identifier and rare-secret protection. Reject blanket numeric exemptions and majority-based dismissal. |
| 4 | Test low-cardinality identifiers across CSV types; blanket absence of CSV top_values is contradicted by inspected code. |
| 5 | Test explicit local-category behavior; default synthetic labels are intentional in source-free mode. Exact preservation belongs to authorized policies. |
| 6 | Explicit sensitivity review is a product/security decision, not an unrestricted declassification flag. |
| 7 | Retain timestamp/timezone regressions and distinguish malformed profile/spec routing fixtures from valid inputs. |
| 8 | Reproduce repeated database keys incorrectly treated as row-unique; use cardinality evidence without copying raw identifiers. |
| 9 | Test independent identifier domains and consistent declared FK mappings; avoid accidental row-counter equality. |
| 10 | Test unavailable date bounds and explicit fallback disclosure; do not silently claim source-period fidelity. |
| 11 | Provide bounded connection failure categories, never raw database exception chains or credentials. |
| 12 | Explain name-based classification; any preservation exception needs approved policy and executable safety checks. |
| 13 | Test declared relationships, inference gaps and row-count behavior separately; existing generation does apply declared relationships. No automatic orphan-rate preservation. |
| 14 | Separate utility from conformance; schema/relationship/constraint validators already exist. Unmeasured fidelity must not be a pass. |
| 15 | Test category limits and early validation before unnecessary reads; settle configurable budgets explicitly. |
| 16 | Improve actionable safe SQL diagnostics; JOIN/CTE expansion remains a separate decision, not an assumed fix. |
| 17 | Measure query count and scan budgets; assess bounded aggregate batching. Temporary table writes are outside the read-only contract. |
| 18 | Test explicit derived formulas and unsupported expression disclosure; SQL-to-formula translation requires type/null/rounding semantics, not AST copying alone. |
| 19 | Reproduce atime-only publication failures; preserve path-swap protection. Define directory overwrite behavior explicitly and test rollback. |

Before candidate acceptance, give every row a final confirmed/fixed, intentional,
deferred or not-reproduced disposition with rationale and evidence. No silent
omissions; proposals outside the agreed scope remain explicit decisions.

## Supplied Scripts

- golden_run.py: adapt the profile-to-spec-to-output flow into assertions against
  the actual candidate CLI. Replace missing internal snapshot/pair inputs with
  fictional equivalents. Missing optional client data is SKIP, not product FAIL;
  mandatory fictional scenarios must run. Exit nonzero on real assertion failure
  (the supplied script always returns zero). Separate source-free expectations
  from explicitly authorized preservation. Five random samples need not cover
  every category; define deterministic cardinality/coverage expectations correctly.
- probe_output_contract.py: retain all five directory/overwrite cases and fresh
  subprocess runs. Require both successful exit and valid artifacts, not file
  existence alone. Add deterministic atime mutation, output-content checks and
  rollback assertions; do not rely solely on filesystem timing.
- probe_fix_ab.py and probe_fix_runner.py: use as diagnostic evidence only.
  The supplied fixed arm monkeypatches production functions and is not proof
  the shipped package is corrected. Final acceptance runs unpatched candidate
  code. Test absent/present transitions and symlink/path replacement: the sample
  destination comparison omits some None transitions and must not be copied
  blindly. The A/B driver also needs meaningful exit status before CI use.

Review scripts before execution, select the exact candidate interpreter/CLI,
bound subprocess duration, and isolate writes/cleanup inside newly allocated
temporary directories. Do not execute destructive cleanup against client folders.
Do not hard-code the old package version as proof of the tested version.

## Mandatory Local Candidate Replay

Before recommending a release candidate, build/install the candidate branch
package into an isolated local environment and run the reviewed client scripts
against that exact interpreter and CLI. Run the same self-contained scenarios
against the affected baseline in a separate environment. Record source commit,
installed version, script revision, fixture provenance, commands and per-scenario
before/after outcomes without source values. Package imports must not accidentally
resolve to another checkout or an unrelated executable on PATH.

Retain the supplied scripts as original diagnostic evidence in the isolated
working area; also run reviewed acceptance adaptations where the supplied harness
has defects or lacks fictional fixtures. Explain every adaptation and show both
results separately. Never turn a failure green by silently deleting or weakening
the client's requirement. The monkeypatched A/B arm remains diagnostic only;
candidate acceptance must exercise unpatched installed production code.

Each agreed client requirement must map to a runnable local scenario and a
recorded outcome. Missing private inputs remain explicitly unverified rather
than passed. Use fictional reproductions for mandatory local gates and request
client-side confirmation where only their private input can establish the result.
Do not claim complete client acceptance from the script's exit code alone.

## New Agreed Scenarios

Add one-to-one preserved reference combinations; changed amounts with zero and
rounding exceptions; explicit formulas; consistent key domains; exact date
substitution in selected fields; inline YAML/file CSV equivalence; profile
save/load/spec conversion; wizard/noninteractive parity; unknown mapping keys;
high cardinality under budgets; sensitivity conflicts and report/provider leaks.

Use the smallest reusable test fixtures and existing test framework rather than
creating a second independent harness (Ponytail principle). First demonstrate
that regression tests fail against the affected baseline, then pass on the
unpatched candidate. Client/private-data validation may be performed locally by
the client; report only approved non-sensitive outcomes. Do not claim their
private scenario passed from fictional-fixture results alone.
