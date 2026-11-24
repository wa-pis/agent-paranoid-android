# Public Streaming CSV Validation

Validated 2026-11-21, unreleased. No version, tag, push or publication is
authorized by this evidence.

Final regression checks: **2,071 passed, 10 skipped**, 78.65 seconds, **91.50%**
package coverage against the 85% gate. Ruff (`src tests scripts`), mypy (125
package files), compileall, strict MkDocs and strict OpenSpec validation passed.
The built wheel passed the isolated installed-package base-profile verifier.
All acceptance source hashes and the installed wheel hash were rechecked on the
final tree. The raw JSON records these final check results.

## Installed Base-Package Acceptance

Built a wheel from the working tree, installed it without dependencies over an
isolated base environment, and ran its installed `test-data-agent` executable
outside the checkout with `PYTHONPATH` removed. PyArrow and DuckDB were absent.
The existing installed-package verifier passed the base profile and wheel-size
budget. Base dependencies remained Faker, Pydantic and PyYAML; no extra was added.

The isolated environment uses the supported minimum versions: Python 3.11.2,
Faker 25.0.0, Pydantic 2.7.0 and PyYAML 6.0. Host: Apple M4 Max, 14 logical
CPUs, 36 GiB RAM, macOS 26.6.2 arm64. Each size below is one acceptance run,
not a repeated performance comparison. Full bundle export includes mandatory
checks, the real validation report, specification/manifest generation and
publication. These timings must not be substituted for, or compared directly
with, the earlier Arrow/DuckDB component benchmark using different dependencies
and validation/report work.

| Fictional rows × fields | Workers | Installed CLI seconds | Sampled peak tree RSS, MiB | CSV bytes |
| --- | ---: | ---: | ---: | ---: |
| 100,000 × 25 | 4 | 12.029 | 524.7 | 28,175,783 |
| 750,000 × 25 | 4 | 84.563 | 734.6 | 211,321,616 |

The [raw acceptance results](installed-cli-results.json) retain the wheel hash,
all package source hashes, dependency versions, numeric RSS samples/counts,
CSV fingerprints and checks. RSS is the sampled simultaneous coordinator plus
descendant sum, including four workers and the multiprocessing helper. Sampling
is approximately 100 ms plus `ps` overhead and can miss brief peaks; this is not
an OS memory cap. Post-export verification took 0.179 / 1.303 seconds separately.

Both complete CSV hashes match the earlier full materialized `tiled-v1` output:

- 100k: `76330b20f138af1c8b49d42fe8780057cd0b735895a98b0d98713cf715ab9979`.
- 750k: `735b3374822b27e5afccaa73ebde1773ae43b7e93a1f9f06c43c8535f22a4405`.

Every exported CSV was also scanned incrementally for exact row/field counts
and the complete ordered unique identifier range. The report was valid with
all enabled sections passing; the manifest recorded `tiled-v1`, matching CSV
hashes, actual row counts, `synthetic=true` and `source_rows_copied=false`.
Published output directories were 0700 and CSV files 0600. No partial staging
remained, and the private test directory including all synthetic output was
removed after each run. Only measurements, digests and test code were retained.

To recreate the fictional specification from this checkout:

```python
from pathlib import Path
from scripts.benchmark_parallel_generation import fictional_spec

Path("fictional-spec.json").write_text(fictional_spec(100_000).model_dump_json(indent=2))
```

Then use a fresh output folder for each count:

```bash
test-data-agent generate fictional-spec.json --stream-csv --workers 4 \
  --count 750000 --seed 42 --output generated-large --json
```

## Regression Scope And Independent Review

Focused tests cover public CLI/Python dispatch and legacy fallback; real spawned
1/2/4-worker CSV equality through a partial final tile; original integer/float,
numeric-string, boolean, nullable, date/datetime, Unicode and quoted CSV values;
header/cell formula neutralization; normalized cross-tile primary-key duplicates;
mandatory privacy/schema checks even with report flags disabled; exact report
section semantics; row/cell/time/CSV and complete-bundle byte limits; no optional
imports; mutation isolation; existing destination preservation and complete
staging cleanup after CSV, metadata or publication failures.

The existing shared visitor's worker-failure, cancellation, bounded scheduling,
redaction and cleanup tests remain in force. Source-profile and MCP contracts,
source-overlap workflows and relationship/business-rule generation stay on
their original routes; streaming does not enlarge fallback limits.

Independent review found a reserved-entity-name gap for specifications mutated
after initial Pydantic validation. The streaming boundary now revalidates a
private specification snapshot with serialization warnings suppressed, before
workers or files. Regression tests reject every reserved name and duplicated
field mutations. Validation errors are converted after the exception scope to
value-free errors. The follow-up independent review found no remaining blockers.

The feature is limited to one independent valid-mode entity. Global key state
still grows with row count; arbitrary global-rule streaming and hard RSS
enforcement remain outside this change. Release-candidate approval and release
publication remain separate from implementation acceptance.

## Repeated Public-API Performance Comparison

The subsequent [public CSV benchmark](public-csv-benchmark.md) compares unchanged
serial and four-worker streaming bundle exports under the same environment and
finite budgets, with all checks retained. All 12 runs and artifact audits passed;
three repeats per path/size reproduced the same CSV. Raw timings, exclusive
stages, tree/coordinator RSS, validator coverage, source hashes and cleanup are
saved in [public-csv-results.json](public-csv-results.json). Its current-dependency
API measurements are separate from the installed minimum-version acceptance
above. The benchmark harness adds 17 passing focused tests; production code and
default limits are unchanged by this comparison.
