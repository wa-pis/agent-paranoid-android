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

A failure identifies the phase and exceeded ceiling. Investigate the measured
operation and input size before changing a budget. Do not raise a ceiling only
to make a single run pass. Platform-level RSS, disk, cancellation, and failure
cleanup are covered by separate operational-readiness gates.

## Cancellation Cleanup

Folder and single-entity generation stage artifacts beside the destination.
If the process receives an interactive cancellation while writing or
validating that staging area, the incomplete staging directory is removed and
the cancellation is re-raised. The final destination and success metadata are
not published.

Hard termination such as `SIGKILL`, power loss, or host failure cannot run
in-process cleanup. A later operational gate covers discovery and recovery for
those abandoned staging directories.
