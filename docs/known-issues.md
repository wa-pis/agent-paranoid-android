# Known Issues

English · [Русский](ru/known-issues.md)

Stable `1.6.0` completed [public verification](release-evidence-1.6.0.md).
External acceptance feedback was reconciled against current main on 2026-10-22;
the [feedback work plan](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/external-feedback-1-6)
separates historical fixes, current limitations and unverified observations.

- CSV numeric strings can remain phone-like and sensitive. Do not bypass privacy
  checks or switch exact measures to float to suppress an error; reviewed numeric
  profiling is planned. Exact decimal generation keeps its existing reviewed
  `--decimal-fields` contract.
- Trino already supports explicit runtime authentication over verified HTTPS.
  The external authentication failure still needs configuration/version evidence;
  fake-driver tests do not establish acceptance against a particular server.
- Numeric shape supports optional zero/subunit frequencies and a minimum subunit
  exponent. Older profiles can omit that evidence; reprofile before assuming it
  exists. A negative exponent is valid for values below one. Parquet distinct
  counts can be unavailable; missing statistics do not mean zero distinct values.
- Relationship validation checks declared relationships. Missing logical edges,
  source orphan rates and temporal granularity are not established by a passing
  validation report. Use reviewed declarations and explicit entity row counts.

These are development follow-ups, not changes already published in `1.6.0`.

The [separate transformation/session acceptance campaign](acceptance-matrix.md)
remains open, including genuine local-terminal preservation acceptance where
required. Existing automated and historical RC results do not establish its
completion or private-data suitability. Provider adapters remain experimental;
resource and artifact durability limits remain in their respective guides.

Resolved findings and their original risk dispositions are retained in
[Historical Security Findings](security-history.md).
