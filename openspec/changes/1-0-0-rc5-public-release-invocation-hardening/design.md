# Design: 1-0-0-rc5-public-release-invocation-hardening

## Approach

Implement RC5 in six bounded stages:

1. Complete public-artifact acceptance. Resolve the RC4 PyPI/public-index
   state, verify wheel and sdist filenames, hashes, version metadata, and
   signatures/attestations from clean environments. Run the literal README
   commands for base, `trino`, `mcp`, and `mcp,trino` profiles, including
   `--version`, `demo`, and `doctor`.
2. Split result and transport accounting. Consume
   `database_result_bytes` incrementally while reading cursor rows. Build the
   final MCP result, serialize it with the production JSON serializer, and
   charge `transport_response_bytes` for the complete envelope before writing
   it to stdout or another transport. Reserve a fixed minimal error envelope
   and fail with that envelope when the normal result does not fit.
3. Add cumulative invocation controls. Extend the typed budget with
   `max_profiled_columns`, `max_statements`, `max_invocation_seconds`, and an
   optional `max_cumulative_estimated_scan_bytes`. Create a monotonic deadline
   at invocation start, enforce it before each query/column operation, and
   share the same counters through nested profiling. Start with 100 columns,
   150 statements, and 120 seconds; retain evidence for any different values.
4. Normalize public wording and rerun release gates. Every document must
   distinguish default aggregate-only responses from explicit opt-in
   row-returning responses. Stable promotion reuses the accepted RC5 source
   tree and permits only release metadata changes.
5. Bound local planning throughput. Change agent folder profiling to an
   `auto` metadata-cache policy with an explicit refresh path, retain a bounded
   row-level sample while streaming schema statistics where practical, and
   enforce a monotonic local profile deadline plus sample/size limits.
6. Bound and measure optional AI advice. Introduce typed fast/normal/quality
   advisor settings for model, reasoning effort, complete prompt/input budget,
   output tokens, timeout, and retries. Record only non-sensitive run metadata.
   Add a separate candidate-ranking adapter for relationship discovery; it
   receives deterministic candidate evidence only and remains review-gated.

## Data And Contracts

- `src/test_data_agent/trino_work_budget.py`: typed database and transport
  counters, monotonic deadline, cumulative column/statement/scan limits, and a
  bounded error-envelope path.
- `src/test_data_agent/trino_client.py` and MCP transport composition:
  incremental database-result accounting and final serialized transport-result
  accounting before output.
- `src/test_data_agent/trino_profiling.py`: cumulative column and statement
  consumption across table and nested column profiling.
- `src/test_data_agent/profiling/`: one-pass/local-deadline profile path and
  metadata-only cache policy for repeated agent planning.
- `src/test_data_agent/providers/openai.py` and advisor configuration:
  benchmarked presets, complete request accounting, timeout/retry behavior, and
  non-sensitive latency/usage metadata.
- `src/test_data_agent/relationship_discovery.py`: provider adapter boundary for
  candidate ranking without candidate invention, source rows, or direct spec
  mutation.
- `src/test_data_agent/trino_config.py` and `docs/reference/configuration.md`:
  application-level environment names, defaults, units, and failure behavior.
- `README.md`, `docs/getting-started/installation.md`, `docs/mcp_examples.md`,
  `docs/how-to/mcp.md`, `docs/ai_integration.md`, and
  `docs/reference/application-boundaries.md`: consistent default-versus-opt-in
  MCP wording and exact public RC installation commands.
- `openspec/specs/safe-mcp-workflow/spec.md`, release evidence, package
  metadata, checksums, SBOM, provenance, and attestations: one versioned
  acceptance contract.

Transport output accounting must measure the same final serialized JSON shape
that the production MCP transport writes, including envelope fields, keys,
escaping, dictionaries, nested metadata, and error objects. A normal response
must not be materialized in full if its measured size already exceeds the
transport budget; use bounded incremental construction or a conservative
preflight estimate followed by final serialization verification.

## Failure Modes

- Missing public PyPI wheel or sdist, mismatched hash, missing attestation, or
  README failure blocks RC5 acceptance and stable promotion.
- A database result that exceeds `database_result_bytes` stops cursor
  consumption and closes resources before returning a bounded error.
- A final MCP response that exceeds `transport_response_bytes` is replaced by
  a fixed error envelope whose own serialized size is reserved below the
  configured limit. If the configured limit is below that minimum, reject the
  configuration at startup.
- A wide-table profile fails closed before another column or statement starts
  when cumulative columns, statements, scan estimate, or deadline is spent.
- Each invocation gets independent counters and a fresh deadline. Helpers
  cannot reset or restore consumed budget, and concurrent invocations cannot
  consume one another's counters.
- Documentation or configuration that claims all MCP responses are source-free
  fails the documentation gate; only default aggregate-only surfaces receive
  that guarantee.
- A local profile that reaches its deadline or sample budget fails closed and
  leaves no partial profile cache trusted.
- An advisor request that exceeds its complete prompt budget, timeout, or retry
  policy fails with a bounded provider error and no prompt/source data in
  diagnostics.
- A relationship-ranking response that changes candidate identity or bypasses
  review is rejected before it can affect a `DatasetSpec`.

## Alternatives

- Use one `response_bytes` counter for both database and transport output:
  rejected because it cannot account for JSON/envelope expansion precisely.
- Rely only on Trino per-query session limits: rejected because fan-out can
  exceed safe total work while every individual query remains compliant.
- Keep defaults at 1000 columns and 2048 statements without evidence: rejected
  until operational benchmarks justify those values.
- Treat the existing RC4 tag as sufficient publication evidence: rejected
  because a tag is not a public PyPI install or an external-artifact smoke
  test.
- Keep agent folder cache opt-in while the library cache is opt-out: rejected
  because repeated review-first planning needlessly repeats safe metadata work.
- Let a byte cap on `AdvisorRequest` stand in for a complete provider budget:
  rejected because instructions, wrappers, schemas, and tokenization add
  unaccounted work.
