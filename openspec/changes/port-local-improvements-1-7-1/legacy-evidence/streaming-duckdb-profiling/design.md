# Design

## One-Pass Handoff

`profiling/schema_profiler.py` continues to own CSV parsing, whitespace/null
normalization, sensitivity/type inference, samples, category order and profile
construction. Accumulators keep their existing SHA-256 sets while the sum of
per-field distinct entries is at most 1,000,000 for the current entity. The sum
counts entries in separate field sets, not a global deduplication of columns.

At the first entry above that threshold, mark accumulators as count-only, drain
their existing sets and resume the suspended cell iterator. The triggering cell
is already in the drained sets. No source cell is skipped, read again or fed
twice into inference. Existing set iteration order is irrelevant to counts;
remaining source rows retain their original inference and sampling order.
Low-cardinality inputs can remain on sets regardless of row count, within the
normal input budgets.

The internal `profiling/duckdb_distinct.py` adapter receives only the initial
sets, a lazy `(field_ordinal, digest)` iterator and the invocation budget. It
returns a count for every field, including zero for all-null fields. It does
not accept paths to source files, field names or caller SQL. No new public
backend selector or API export is needed.

## Scratch Disclosure Boundary

Create a fresh 32-byte secret key in memory for each counting invocation. Before
Arrow receives any digest, replace it with HMAC-SHA256 of the existing digest.
The initial and remaining streams use the same key. Equal values within a field
still yield equal tokens, while independent invocations cannot link tokens by
a stable hash or test low-entropy source candidates without the key.

Use a new private `TemporaryDirectory` (`0700` on POSIX), never a source-named
database or a caller-chosen spill path. The database is `:memory:`. Only ordinal
integers and keyed 32-byte tokens may reach Arrow or spill; source strings,
names, ordinary SHA-256 digests and the key must not. Tokens and keys are absent
from profiles, caches, logs, exceptions and transport responses.

The single fixed grouped exact-distinct query consumes a lazy Arrow reader in
batches of at most 50,000 tokens. Explicit configuration disables external
access, extension installation/loading, Python replacement scans and logging.
Set a 128 MiB buffer limit, one query thread, one asynchronous I/O thread and a
2 GiB spill limit, applying the latter with a separate `SET`. Lock configuration
before the count query. These subsystem settings do not cap total process RSS.

## Budgets And Failure

Preserve existing preflight input bytes, per-row/cell accounting, bounded
sampling and per-field deadline checks. Set native `max_execution_time` from
the remaining invocation budget immediately before the count query; check the
deadline again before returning. DuckDB 2.0.1 is the minimum supported version
for the native query-deadline contract.

Arrow may wrap producer errors. Preserve the original safe structured profile
budget error or cancellation, while replacing backend, import and cleanup
details with value-free failures. Close the reader and connection and remove
scratch on success and failure before returning a completed profile. Failure
must not publish a partial profile, trusted cache or generation result.

Abrupt process termination can leave scratch behind. It contains only keyed
tokens under a private directory; the key is never saved. This does not promise
secure erasure, protection against a compromised owner process, or cleanup after
SIGKILL/machine failure.

## Packaging And Compatibility

`profiling` contains `duckdb>=2.0.1,<3.0.0` and `pyarrow>=15.0.0`. `all` includes
both, while base installations remain small. Lazy imports occur only at actual
handoff; a missing or broken backend fails with safe recovery guidance. The
unreleased extra is installed from the checkout until a new artifact is
published; stable 1.5.0 does not provide it.

Identical completed profile content and fingerprints keep cache format 5 valid.
Full-pipeline comparison must include fields, sensitivity, distributions,
identifier pools, keys, inferred relationships/constraints, local-category
allowlists, profile/spec fingerprints and cache round trips, using the same
synthetic CSV bytes. Test late duplicates and a mid-row handoff as well as
encodings, nulls, types and multiple entities. Verify private real spill and
absence of raw values/unkeyed digests, cleanup under faults and native query
deadline enforcement. Performance evidence remains a component result until
complete-profile timing and RSS are measured separately.
