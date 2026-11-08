# Verification Evidence

## Linked-Table Performance (2026-11-08)

Fictional acyclic chain: accounts 150,000 → purchases 300,000 → items 300,000.
Total 750,000 rows, 25 columns per table, CSV, seed 42, batch 2,000.
macOS 26.6.2 arm64; Python 3.13.14; 14 reported CPUs; 1 GiB policy.
No source files, databases or AI providers are used by this benchmark.

| Workers | Seconds (three runs) | Median | Speedup | Conservative memory upper bound |
|---:|---|---:|---:|---:|
| 1 | 59.17, 58.12, 58.70 | 58.70 s | 1.00× | 149.4 MiB |
| 2 | 38.43, 42.52, 63.85 | 42.52 s | 1.38× | 223.3 MiB |
| 4 | 109.97, 29.94, 30.06 | 30.06 s | 1.95× | 372.4 MiB |

The ≥2× four-worker target is **not met**: 1.953× by median.
The large timing spread prevents a clean hardware performance guarantee.
Some focused verification overlapped early measurements; these are local
development observations, not isolated production or cross-platform evidence.
The memory column is conservative accounting from process high-water values,
not an independently sampled process-tree peak or an OS-enforced memory limit.

All nine large runs passed mandatory validation and had identical SHA-256
hashes for every data CSV. Dataset files total 172,858,082 bytes; control files
and timing statistics vary. Smaller 10k/100k total-row runs at 1/2/4 workers
also passed with identical data hashes within each size. Raw measurements are
in `benchmark-evidence.json`.

Reproduce offline:

```bash
.venv/bin/python benchmarks/run_dataset_scale.py --relational \
  --counts 750000 --workers 1 2 4 --repeat 3 --result /tmp/linked-results.json
```

Cycles, shared PK/FK identities and global rules remain deliberately unsupported.
Independent exact-SHA review, manual client acceptance and release checks remain
required before any separately authorized RC. This evidence is AI-driven
technical verification, never a substitute for human acceptance.

The unit-test helper explicitly uses a 4 GiB finite policy because the full
coverage runner retains prior tests' RSS high-water. Runtime defaults remain
1 GiB, and every recorded standalone scale measurement used that default.
The memory guard was not mocked, disabled or changed.

## Final Technical Checks

- Complete `scripts/check_release.sh`: **4,900 passed, 24 skipped**, 353.43 s;
  coverage **91.83%** (required 85%). All remaining script gates passed.
- After final help/contract refresh: activation composition/reversibility,
  contract fixtures, CLI parser and real SDK stdio workflows: **20 passed**
  in 11.95 s. SDK approvals are fictional technical tests.
- Ruff, strict mypy (168 source files), compile, strict OpenSpec, schema freshness,
  license/dependency compatibility, operational budgets and quickstart passed.
- No live database or external AI-provider calls; provider tests use local fakes.

No new RC is published by this change. The ≥2× performance target and any future
release's independent exact-SHA/manual acceptance gates remain outstanding.
