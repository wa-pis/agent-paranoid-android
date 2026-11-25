# Design: Public Streaming CSV

## Boundaries

Reuse `generation/tiled_generator.py` for deterministic 4,096-row logical tiles
and the bounded ordered visitor in `adapters/parallel_generation.py` for spawned
process lifecycle. `io/streaming_csv.py` owns the explicit streaming consumer,
per-tile validation, global key/count state and incremental standard-library CSV
serialization. Keep filesystem/process I/O out of deterministic generation.

`io/workflows.py` owns eligibility selection and the existing bundle transaction:
preflight, private staging, specification/report/manifest artifacts, final bundle
size checks, publication and failure cleanup. Preserve `DatasetGenerationResult`
and existing artifact names. Do not route a reviewed source workflow through a
consumer that lacks its source-row overlap checks.

## Opt-In Contract

`generate_dataset_bundle(..., streaming=ParallelGenerationPolicy(...))` defaults
to `None`. The `generate SPEC --stream-csv` CLI constructs a finite policy with
at most 1,000,000 rows and 25,000,000 cells; `--workers` is one through four,
defaults to four only for this flag, and is invalid without it. A source-profile
input rejects this option. The flag implies CSV when `--format` is omitted and
rejects an explicitly selected non-CSV format. Default invocations and MCP
schemas are unchanged.

The Python policy also requires an effective CSV output format; a non-CSV
combination fails before generation. Only valid mode, one independent entity,
no relationships, no constraints and no business-rule applier are eligible.
Ineligible specifications
use the current generator/solver/business-rule pipeline and its ordinary row
cap. Never apply a streaming-specific larger cap to that fallback. Decide
eligibility before changing generation limits or starting workers.

The flag requests the tiled engine explicitly; it is not an automatic row-count
threshold. Small explicit runs use the same eligible engine so that increasing
counts does not silently switch seed namespaces. A missing explicit seed uses
the existing saved/default seed resolution before tiles are scheduled.

## Checks And Publication

Validate the reviewed effective specification before generation. For every
ordered tile, retain mandatory `solve_constraints` / privacy/schema enforcement
with the tile row count, independently of optional report flags. Reconcile
per-tile results into the existing validation report contract. Check ordered
starts, complete row counts and whole-run primary-key uniqueness, including
duplicates across tile boundaries. Primary-key sets are the only row-sized
retained state; candidate and serialization buffers remain tile-sized.

Use the current CSV quoting/CRLF/scalar behavior and `neutralize_csv_cell` for
headers and values. Avoid Arrow conversion: it is unnecessary for CSV and can
change otherwise valid scalar representations. Enforce the output byte budget
incrementally before writes and again across the full artifact bundle. Reuse
private, no-follow atomic writers and the existing staged-directory publication
instead of writing directly into the destination.

On worker/validation/I/O/deadline/cancellation failure, stop and join owned
workers, discard incomplete staging and preserve destination safety. Keep errors
value-free. Normal cleanup cannot promise recovery from SIGKILL, repeated
interrupts or OS failure. Do not claim constant memory or a hard RSS cap.

## Determinism And Evidence

Keep `tiled-v1` tile width, RNG/Faker seed derivation, absolute identifiers and
ordered consumption unchanged. For a fixed engine/specification/seed/dependency
snapshot, streaming CSV bytes must equal the full tiled API's CSV bytes with
one, two and four workers, including a partial last tile. They need not equal
legacy generation under the same seed; default/fallback exports retain legacy
semantics. The manifest's existing engine field records the actual selection.

Preserve the historical Arrow/DuckDB benchmark and its raw evidence as the
experiment that informed this choice. Test the implemented public route
separately, including an isolated base installation without optional modules.
Do not present the earlier benchmark timing as a new public-export measurement.
