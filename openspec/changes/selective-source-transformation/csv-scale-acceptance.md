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

## Configurable target harness — 2026-10-05

The CSV harness now accepts explicit `--max-bytes` and `--max-seconds`,
retaining 512MiB / 1800s defaults. The selected byte budget applies both to
saved per-file/total-input/output limits and to run limits. Invalid nonpositive,
nonfinite time or oversized integer budgets fail before fixture creation.
Small synthetic 10 × 3 scenario passed with 1MiB / 60s, plus five invalid-budget
startup checks and Ruff. This is harness validation, not measured target proof.
For 1M × 100, this fixture's CSV source is 550,000,900 bytes and replacement
output is 600,500,900 bytes; both exceed 512MiB. Use an explicit sufficient
byte budget instead of treating row/cell configuration as a byte-limit override.

**Target run PASSED:** exact installed runtime
`b49ceed5fc3d64698f4cfd4135b2958edd915512`, wheel SHA-256
`bcce6365fbb6724d2d583796a61567d99bbdc6c9a9e86eb7e02a5d65f156ae8e`.
Command: `--rows 1000000 --columns 100 --max-bytes 1073741824 --max-seconds 3600`.
Local resumable state: `/private/tmp/apa-csv-target-current.json`;
log: `/private/tmp/apa-csv-target-b49ceed-xi8v0xap/run.log`; PID 80161.
Profile 286.211s; review cumulative 579.090s; full completion 1188.870s.
All 100,000,000 cells passed ordered replacement readback, mapping precedence,
non-cascade behavior, manifest/provenance, unchanged input digest and cleanup.
Output: 600,500,900 bytes. The terminal JSON is retained in the log.
This proves only the private CSV route against this exact isolated wheel;
no public/all-route/RC pass is claimed.
