# Design: CSV Encoding Performance

## Measure Before Choosing The Change

Profile bounded fictional data using the current ordinary and streaming CSV
encoders. Select the smallest implementation that removes measurable repeated
work while preserving the existing CSV bytes and supported edge behavior.
Do not add a backend, dependency, user option or value cache for this change.

The selected change is a two-line guard in the shared `neutralize_csv_cell`.
After the existing string/empty check, an exact built-in string whose first
character is outside ` \t\r\n=+-@` returns unchanged. Its first character cannot
be removed by the original `lstrip`, and neither original formula condition
can match. All whitespace/operator prefixes and every string subclass retain
the original method calls. Both CSV paths use this helper; their loops and
atomic writers remain unchanged.

Preserve the established field order, header emission, missing/extra field
handling, scalar formatting, quoting, delimiters, CRLF records and Unicode
encoding. Header and cell formula neutralization must retain every existing
dangerous-prefix and whitespace/control-character case. Preserve exceptions,
input non-mutation and supported scalar/subclass behavior.

Streaming must retain bounded tiles rather than materialize the full dataset
or CSV. Any preparation must remain local to the current encoding operation;
later rows, calls and specification edits must not inherit a cached decision.

## Shared Safety And Publication Boundaries

The same formatting guarantees apply to specifications from all source adapters.
No source-row reads, SQL changes or source-label shortcuts are introduced.
Mandatory schema, privacy, relationship and constraint checks retain their
existing order and settings. All generated tiles remain validated before writes.

Keep the existing time, row, cell and byte bounds, private temporary-file
permissions, cleanup and atomic file/bundle publication. An encoding, budget,
worker or I/O failure must not publish a partial trusted output or replace a
protected destination. Ordinary and tiled generation retain their distinct seed
namespaces and each must reproduce its own prior CSV bytes.

## Evidence

Compare frozen previous encoders with the candidate over fictional supported
scalars, Unicode, quoting/newline cases, formula headers/cells, schema edges,
subclasses and failures. Retain existing privacy, budget and atomic-publication
regressions and input non-mutation checks.

Repeat the unchanged public CSV benchmark for 100,000 and 750,000 rows × 25
fields: three fresh subprocesses per size/path, alternating order, fixed seed
and existing limits, without concurrent heavy verification. Record exclusive
stages, sampled process-tree RSS, actual validator coverage and artifact audits.
Compare byte counts/hashes with the latest value-normalization series while
preserving every historical artifact. Separate bounded encoder diagnostics from
full public API performance.

