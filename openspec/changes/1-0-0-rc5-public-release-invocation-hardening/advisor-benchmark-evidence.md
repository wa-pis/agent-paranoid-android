# OpenAI Advisor Preset Benchmark Evidence

Date: 2026-08-08

The benchmark executed the production OpenAI advisor adapter against two
representative synthetic-only profiles (`relational` and `wide`). It sent no
source rows, raw PII, credentials, or production metadata, and retained only
the aggregate metrics below.

Historical smoke command, executed against commit
[`5bed2ea`](https://github.com/wa-pis/agent-paranoid-android/commit/5bed2ea):

```bash
uv run --extra openai python scripts/benchmark_openai_advisor_presets.py \
  --input-usd-per-million 5 --output-usd-per-million 30
```

The explicit prices match standard `gpt-5.6` pricing at execution time. The
provider returned token usage for every request. Its response object did not
report a retry count, so `reported_retries` remained `null`; configured retry
caps stayed bounded per preset.

| Preset | Reasoning | Retry cap | Valid | Safety preserved | Mean latency | Input tokens | Output tokens | Reported retries | Cost |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fast` | `none` | 0 | 2/2 | 2/2 | 9,474 ms | 6,768 | 1,901 | `null` | $0.090870 |
| `normal` | `low` | 2 | 2/2 | 2/2 | 10,292 ms | 6,768 | 1,937 | `null` | $0.091950 |
| `quality` | `high` | 2 | 2/2 | 2/2 | 10,860 ms | 6,768 | 2,081 | `null` | $0.096270 |

All candidates achieved 100% proposal validity and safety preservation.
`fast` had the lowest measured latency, token use, and cost, so RC5 selects its
bounded settings as the default: `gpt-5.6`, reasoning `none`, 4 MiB complete
request budget, 4,096 output tokens, 15-second timeout, zero SDK retries, and
no service-tier override.

## RC5 acceptance gate

The live acceptance benchmark executed against commit
[`2067dd1`](https://github.com/wa-pis/agent-paranoid-android/commit/2067dd11e77fd1428833c2e9de2b15ae8ff15908)
after explicit cost approval. It used the five fixed synthetic shapes
`narrow`, `wide`, `multi_table`, `nullable_heavy`, and `constraint_heavy`, with
20 runs per preset and 60 provider calls total. No source rows, raw values,
credentials, or production metadata were sent or retained.

```bash
.venv/bin/python scripts/benchmark_openai_advisor_presets.py \
  --runs-per-preset 20 \
  --input-usd-per-million 5 --output-usd-per-million 30
```

Latency percentiles use the deterministic nearest-rank method across all
attempts, including failed attempts. Provider usage was present for every
response. The response object did not expose retry counts, so retry reporting
remained unavailable even though the configured caps were enforced.

| Preset | Reasoning | Retry cap | Valid | Safety preserved | Errors | Timeouts | Mean | p50 | p95 | Input tokens | Output tokens | Cost |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fast` | `none` | 0 | 20/20 | 20/20 | 0 | 0 | 8,640 ms | 7,688 ms | 13,079 ms | 59,340 | 15,228 | $0.753540 |
| `normal` | `low` | 2 | 20/20 | 20/20 | 0 | 0 | 9,126 ms | 7,701 ms | 15,714 ms | 59,340 | 15,438 | $0.759840 |
| `quality` | `high` | 2 | 20/20 | 20/20 | 0 | 0 | 9,619 ms | 8,427 ms | 14,901 ms | 59,340 | 17,024 | $0.807420 |

All 60 responses completed, validated, and preserved safety, with zero errors
and zero timeouts. Total usage was 178,020 input tokens and 47,690 output
tokens, costing `$2.320800`. Because no call failed and the provider exposed no
retry count, the run showed no observable retry difference between the
zero-retry and bounded-retry presets. The acceptance gate passes and continues
to support `fast` as the lowest-latency, lowest-token, lowest-cost default.
