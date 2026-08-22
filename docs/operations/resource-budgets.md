# Operational Resource Budgets

The release gate exercises profiling, deterministic multi-entity generation,
and validation against checked-in time and peak-allocation ceilings. Its input
is created locally from synthetic identifiers and low-cardinality categories;
it never reads production data or contacts an external service.

Run the same gate locally:

```bash
PYTHONPATH=src python3 scripts/check_operational_budgets.py
```

The command prints one JSON record for each phase. The current representative
workload uses 2,500 rows in each of two related entities and applies these
per-phase ceilings:

| Budget | Ceiling |
| --- | ---: |
| Wall-clock time | 15 seconds |
| Peak traced allocation | 256 MiB |

These ceilings are release-regression guards, not hardware sizing promises.
They are deliberately high enough for ordinary CI variance while still
detecting accidental unbounded work or large allocation growth. Tightening a
ceiling requires repeated measurements on every supported CI runtime.

Local JSON datasets, JSON profile/spec imports, and profile-cache documents are
also scanned for structural depth before `json.loads` or Pydantic materializes
them. `TEST_DATA_AGENT_MAX_JSON_DEPTH` defaults to `100`; brackets inside JSON
strings do not count toward the limit. Oversized nesting fails before a partial
dataset, profile, or spec can be returned.

A failure identifies the phase and exceeded ceiling. Investigate the measured
operation and input size before changing a budget. Do not raise a ceiling only
to make a single run pass. Platform-level RSS, disk, cancellation, and failure
cleanup are covered by separate operational-readiness gates.

## Database Source Budgets

The JDBC-style endpoint, qualified wildcard, and SQL query source budgets in
this section apply to stable `1.3.1`.

Database-source configuration and profiling have independent limits before
generation begins:

- PostgreSQL and Trino JDBC-style URLs are capped at 4,096 UTF-8 bytes and
  parsed hosts at 253 characters. PostgreSQL database identifiers are capped at
  63 characters; Trino catalog and schema identifiers at 255 characters.
- One PostgreSQL profile defaults to 100 tables, 1,000 explicit or
  metadata-expanded columns, 1,500 statements, 10,000 aggregate/metadata
  result rows, 100,000 result cells, and a shared 120-second deadline.
- One Trino invocation defaults to 100 profiled columns, 150 statements, a
  120-second deadline, and 4 MiB each for database results and the serialized
  transport response. Shared-hardened deployments additionally require a
  finite cumulative estimated-scan ceiling.
- One SQL query source defaults to 64 KiB of UTF-8 SQL, 500 AST nodes, depth
  32, and 100 projected fields after wildcard expansion. It also consumes the
  selected adapter's existing statement, result, deadline, and scan budgets.

Qualified wildcards do not bypass these ceilings. Metadata expansion must
finish as one validated, sorted, explicit-column snapshot before aggregate
work starts. Exhaustion fails before the next operation and publishes no
partial profile. Exact environment names, defaults, and absolute caps are in
[Configuration](../reference/configuration.md).

## Artifact Persistence Contract

Atomic visibility is not the same as durable persistence. Generated artifacts,
profiles, specs, and agent workspace state use these boundaries:

- completion-state and advisor-handoff writes that use atomic writers create a
  sibling temporary file and atomically replace the destination;
- new folder, review, and agent-plan bundles are completed in a sibling staging
  directory and published with one same-filesystem directory rename;
- a single-entity update to an existing directory uses several per-file moves,
  so it is not one atomic multi-file transaction;
- approval receipt and result markers are separately atomic, and an
  interruption between them is represented as a recoverable agent state.

For an exception or interactive cancellation that the process can handle, the
workflow removes staging data or rolls moved files back. Agent recovery then
revalidates the existing checkpoint, spec fingerprint, manifest, report, and
generated files before publishing missing completion metadata. Recovery does
not regenerate rows.

Artifact writers do not call `fsync` for file contents or parent-directory
metadata. Therefore a hard stop, kernel or host crash, storage failure, or
power loss can leave an abandoned staging directory or lose a recently written
or renamed artifact. Atomic replacement prevents partial visibility for the
state transitions and new bundles that use it during normal operation; it does
not cover every standalone artifact command or promise persistence across
those failures.

**Disposition:** artifact `fsync` support is deferred until after 1.0 and is
not release-blocking for RC4 or stable 1.0. The repository maintainer owns the
follow-up. Revisit this decision before promising crash/power-loss durability,
when deployment requirements demand it, after an artifact-loss incident, or
when a platform-specific implementation and crash-consistency test plan are
ready. The HMAC audit log has separate flush behavior and does not broaden the
artifact durability contract.

## Cancellation Cleanup

Folder and single-entity generation stage artifacts beside the destination.
If the process receives an interactive cancellation while writing or
validating that staging area, the incomplete staging directory is removed and
the cancellation is re-raised. The final destination and success metadata are
not published.

Hard termination such as `SIGKILL`, power loss, or host failure cannot run
in-process cleanup and may leave an abandoned staging directory. Follow the
recovery guidance below; do not interpret staging data as a completed bundle.

## Disk Exhaustion

Generation checks estimated bundle size and available capacity before work
starts. Free space can still disappear concurrently. If a write receives
`ENOSPC` after creating a partial staged file, folder, review, and single-entity
workflows remove the staging directory, propagate the operating-system error,
and publish neither the destination nor success metadata.

Free space on the target filesystem and retry with the same reviewed spec and
seed. Do not treat files from an abandoned or failed staging directory as a
successful synthetic bundle.

## Generation Timeout

The generation deadline is checked between deterministic workflow stages. If
the deadline expires after rows or metadata have been staged, folder, review,
and single-entity workflows remove the entire staging directory before
returning the timeout error. They publish neither a final destination nor
success metadata.

Increase `TEST_DATA_AGENT_MAX_GENERATION_SECONDS` only after confirming that
the requested row count and rule complexity are expected. Retrying with the
same spec and seed remains deterministic.

## Interrupted Publication

Folder and review bundles use an atomic directory rename. If publication is
interrupted after that rename but before the caller receives success, the new
destination is removed. Single-entity publication may update several files in
an existing directory; it keeps temporary backups and rolls every moved file
back, restoring replaced files while leaving unrelated files untouched. It
publishes `generation_manifest.json` last and reports completion only after
the manifest-recorded artifact hashes pass read validation. Replacing any
same-named sibling requires explicit overwrite approval.

The caller receives the original interruption error. A failed publication does
not leave a generation manifest or output file that can be mistaken for a
successful run when the process can complete rollback. This process-level
behavior is not a crash/power-loss guarantee.
