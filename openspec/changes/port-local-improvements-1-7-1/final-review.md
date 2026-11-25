# Final Port Review — 2026-11-25

Status: local feature branch ready for review; no unresolved findings.
Fresh executable results: [final checks](final-review-checks.json).

## Reviewed Source

- Feature branch: `codex/port-local-improvements-1-7-1`.
- Final implementation: `1a40ad089412603450a68864d4a420a47d437339`.
- Remote default resolved to `main`; the fresh fetch confirmed development
  `49d12c515c3aa7d012b038c5d1c96b50195fbcc1`. The starting worktree was clean
  at `bd19407a`, two commits ahead and zero behind that tip. No merge was needed.
- This continuation retains the explicit historical release/benchmark bases.
  It does not upgrade dependencies or rewrite unpublished commits.
- The [final runtime/policy manifest](final-runtime-policy.json) freezes 177
  files with canonical map SHA-256
  `8de3784ce88523bb25d0f5f09b68cf1673ab826043718bfe533c2ca92c658c9e`.
  Later reporting changes do not alter that implementation.

## Findings Resolved

1. FLOAT validation had lost released scalar coercion. A finite native Decimal
   failed Python/Parquet validation while equivalent CSV/JSON input passed.
   The shared checker now retains released coercion, its numeric fast path and
   the finite-value guard. Four format regressions first reproduced two failures,
   then passed; input identity, exact DECIMAL and privacy checks remain intact.
2. Folder CSV published computed numeric summaries without applying shared
   sensitivity policy to the derived values. A protected quantile then caused
   spec inference to reject a profile accepted by the single-file path.
   The final numeric distribution is now checked before mining, publication or
   caching; protected summaries mark the field sensitive and are omitted.
   Cache format 12 rejects prior formats 10 and 11 so it cannot bypass the correction.
   Six regressions cover both row orders, cache readback and old-cache rebuild.
3. The first complete run exposed premature FLOAT rounding of integer quantiles.
   A constant non-Luhn identifier acquired a Luhn-shaped quantile, while single
   observations above 2**53 also lost precision. Integer ranks and interpolation
   now use exact arithmetic with one ties-to-even rounding; constant FLOAT
   endpoints remain unchanged. Public single/folder/cache regressions and exact
   numeric cases pass with unchanged corpus labels and the privacy guard intact.
4. The profiling guide incorrectly generalized the non-null ratio denominator.
   It now distinguishes folder ratios from the released single-file
   distinct/total-row ratio. Existing metrics and key-candidate behavior remain.

Separate agents reviewed generation/validation/public export, profiling/spill
and privacy/source provenance. All runtime fixes received independent rechecks.
No actionable findings remain within these reviewed paths. This review is not
an activation-safety approval or release acceptance.

## Fresh Checks

- Combined focused regressions: **337 passed**, zero skipped or failed.
- Final full suite: **6,255 passed, 25 skipped**, zero failures/errors;
  coverage **92.24%** (floor 85%). The interrupted and failed
  earlier attempts are recorded separately and are not passing gates.
- Ruff, mypy and compilation of production code, tests and scripts passed.
- Both generated JSON schemas match; dependency compatibility, all 113
  installed dependency licenses and operational resource checks passed.
- Strict MkDocs and all active OpenSpec validation passed.
- A newly built wheel passed installed-package checks in isolated `base`,
  `profiling` and `all` environments. These temporary copies retain the prior
  dependency versions; offline replacement changes only the project wheel.
  All 174 packaged Python files match the frozen tested implementation.
- Wheel: **469,217 bytes**, below 512 KiB; SHA-256
  `783381c941e51159189cee7ee4b4763390310814eb03ea62ed5f011c60240f8e`.
- Fresh replay from the installed `all` wheel exactly matches all **27** saved
  target cases with identical shared dependency versions. Generated bundles are
  removed. The original 21-case release comparison and six intentional ordering
  fixes remain historical; this replay does not pretend to rerun the release.
- Original checkout: **323/323** file hashes unchanged. Historical archive:
  **130/130** hashes unchanged. Earlier verification, checks, manifests and
  release-parity evidence have not been rewritten.

## Difference From Development

The branch adds shared contextual semantics/privacy guards, complete bounded CSV
distinct counting with optional private DuckDB spill, explicit tiled/streaming
CSV, validation/normalization reuse, exact integer calculations and dependency
ordering fixes. Existing DatasetSpec 1.1, DECIMAL, released engines, relationships,
rules, scenarios, budgets, typed CSV and atomic publication remain covered.
The final fixes change only four production modules; the freshness policy is
the only other change against the original 177-file runtime/policy manifest.

The large historical benchmark archive is source-bound reference material.
Its timings do not measure this branch against 1.7.1 or development.

## Limits And Delivery

Checks use macOS arm64 and Python 3.11.15. The other retained Python/OS CI jobs,
the earlier minimum-dependency 140-test environment and 100,000/750,000 × 25-field
performance campaigns were not repeated. Live databases/providers, real dataset
approvals and new transformation activation acceptance were not exercised.
No source data, new permission, MCP issuer, tag, push, main merge or publication
was introduced. The deliverable is a local feature branch for human review.
