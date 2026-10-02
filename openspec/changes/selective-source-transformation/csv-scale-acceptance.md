# Private CSV scale acceptance — 2026-09-28

## Scope and candidate

This checkpoint tests the private, replacement-only CSV route. It does not
activate public execution, approve preservation, test private client data,
certify all 12 routes, or publish 1.6.0rc1.

- Base: `737268d8e92b2876deb71fc035685bd3a3b01859`; candidate is this PR's code.
- Local development wheel retains version `1.5.0`; it is NOT a released RC.
- Wheel SHA-256: `6f93cd68e938c56bde1033fef58758290c4f80f29c723459f6063bf0b66bbceb`.
- Runtime: Python 3.11.2, Darwin arm64. Installed wheel import location verified
  under `/private/tmp/apa-csv-scale-wheel.pcVR7P/installed/test_data_agent/`.
- Harness: `scripts/accept_transformation_csv_scale.py`; no product monkeypatch,
  external API/database, supplied private input, or approval receipt.

## Reproduction

Build the candidate wheel with the pinned hatchling backend, install it into
an isolated target using `uv pip install --no-deps --target <wheel-target>`
(dependencies must already be present), then run:

```sh
PYTHONPATH=<wheel-target> python scripts/accept_transformation_csv_scale.py --rows 300000 --columns 50
```

Only fictional temporary inputs and outputs are created. The saved YAML
profile explicitly selects 1M rows, 100 columns, 100M cells and 512MiB input/output
ceilings. Total input/output run budgets are 512MiB; review is 1MiB and elapsed
work is bounded by 1800 seconds. No implicit budget escalation.

The fixture alternates two fictional row patterns. All 50 fields have explicit
replacement actions; global CSV mappings and one column override exercise
precedence and a non-cascading target. Full readback checks every row and column,
exact row count/order, mixed-origin manifest, 100% replacement provenance,
unchanged input digest, and temporary-input/output cleanup.

## Results

**Passed: 300,000 rows x50 columns =15,000,000 cells**, through installed-wheel
profile → saved-policy/file review → private temporary publication → complete
readback and cleanup. CSV output:90,150,450 bytes. Elapsed:272.572s (~4m33s).
All row/column, mapping, manifest/provenance, input-digest and cleanup assertions
passed. This establishes this fictional private CSV scenario, not arbitrary
data widths, peak-memory containment, public activation or the1M x100 target.

Small harness smoke (10 x3): passed in 0.029s. This only validates the harness.
Candidate full-run cumulative stage timings: profile68.522s, review135.900s.

## Regression gates

- Full offline suite: 2557 passed; two release-fixture tests initially failed
  because subprocess `git` resolved to Apple's unavailable system Git.
  Retried only those two with `/opt/homebrew/bin` first in PATH: passed.
  Ten live-service integration tests deselected, not claimed passed.
- Coverage: 90.99%, required 85%.
- Ruff: source, tests and scripts passed. Mypy: all135 source files passed.
- Compileall, OpenSpec strict and diff whitespace checks passed.

Residual work: SQL-result capture/worker budget propagation, public interface
and activation review, full target1M x100/multi-route acceptance, documentation
and final RC release gates. No hard RSS/wire guarantee is claimed.
