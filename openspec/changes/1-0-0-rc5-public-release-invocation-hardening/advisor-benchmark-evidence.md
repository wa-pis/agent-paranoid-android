# OpenAI Advisor Preset Benchmark Evidence

Date: 2026-08-08

The benchmark executed the production OpenAI advisor adapter against two
representative synthetic-only profiles (`relational` and `wide`). It sent no
source rows, raw PII, credentials, or production metadata, and retained only
the aggregate metrics below.

Command:

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
