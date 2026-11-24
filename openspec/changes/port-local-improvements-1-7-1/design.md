# Port Design

## Baselines

Start the new `codex/port-local-improvements-1-7-1` branch at published tag
`v1.7.1`, commit `8aa5d40af2a9f5f15e6572fd2abafdd805df8c9e`. The original
working copy remains intact on its older branch at `26af6904`. A private
snapshot covers all 1,021 tracked/untracked source files, with a hash inventory
of the 323 local changes. Do not merge the old branch as a replacement tree.

Port behavior by module ownership and resolve each overlap against the released
implementation. Release-only modules, interfaces, security fixes and dependency
pins stay present. Keep version metadata at 1.7.1; this is development work, not
a new release or publication.

## Integration Choices

- Keep DatasetSpec 1.1, all seven scalar types, exact bounded DECIMAL arithmetic,
  conditional rules, relational scenarios, configurable inference, utility
  evidence, source-byte binding and transformation approval/session boundaries.
- Keep the released ordinary and scalable engines and their namespaces. The
  separate explicit `tiled-v1` API/CSV option is additive; it uses released row
  generation and typed CSV encoding. Unsupported streaming specifications use
  the released complete-dataset path without raising its budgets. A released
  execution policy and `--stream-csv` cannot be selected together.
- Reuse released distribution preparation. Port scalar dispatch and checked
  plain-CSV validation reuse without removing unconditional privacy, native-rule,
  business/scenario validation or relationship/temporal utility evidence.
- Preserve exact integers in comparisons, sum/count and aggregate publication;
  retain released bounded rational DECIMAL operations. Order formula, aggregate
  and repair dependencies together, keeping budget accounting and the existing
  pure-formula cycle diagnostic.
- Apply whole-column semantic counters and conservative source privacy to every
  existing adapter. Missing evidence remains unknown. Keep released bounded
  Parquet content/distinct inspection, native Arrow precision and resource caps;
  the old metadata-only Parquet experiment does not replace that release feature.
- Remove CSV distinct ceilings with the private keyed set-to-DuckDB handoff.
  Preserve parsed-byte source identity, deadlines, mining budgets, category scope
  and complete profile equality. Refresh folder caches with format 10.
- SQL query policy 1.2 retains the released 1.1 grouped aggregate language and
  adds sensitive projection provenance without new queries or permissions.
- Finite phone-only numeric storage evidence can support an independently
  authored `numeric_measure` DECIMAL replacement even when corrected phone
  semantics is unknown. Sensitive flags remain on source profiles; keys,
  protected names, other sensitive signals and sensitive null markers veto the
  exception. No source bounds are copied into the reviewed replacement.
- Preserve explicit caller text scopes through CSV/legacy/transformation
  adapters. Canonical generated category-rank metadata receives a bounded
  metadata scope while still running the full detector; raw-cell limits and
  default classifiers are unchanged.
- Add only the optional `profiling` dependency set and its CI/doctor/install
  checks. Keep all released locks and security updates; the lock adds DuckDB.

## Evidence And Documentation

Retain the 130 historical OpenSpec/benchmark files byte-for-byte below
`legacy-evidence/`, indexed by `legacy-evidence-index.json`. Their old paths,
source hashes and timing claims describe the older snapshot only. They are
neither active 1.7.1 contracts nor measurements of this port. The rejected
string-list candidate remains rejected.

Keep released versioned English/Russian documentation and release history.
Fold current behavior into those guides instead of replacing them with the
older parallel documentation layout and image set. Preserve the latter in the
unchanged original working copy and record this disposition in the inventory.
Existing released equivalents of local fixes need no duplicate implementation.

## Verification

Run the released regression suite plus adapted local safety/equivalence tests,
including DECIMAL, all source variants, scoped transformations, inference/MCP,
scalable relational workflows, budgets, atomic failure cleanup and worker-count
determinism. Compare unchanged supported seeded generation directly against the
frozen 1.7.1 source. Keep historical benchmark metadata separate from new checks.
Run coverage, lint/type, package/contract, documentation and OpenSpec gates.
Only fictional fixtures are permitted. No live database, provider request,
dataset approval, push, release or deployment is part of this port.
