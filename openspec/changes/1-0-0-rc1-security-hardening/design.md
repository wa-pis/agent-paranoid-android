# Design: 1-0-0-rc1-security-hardening

## Approach

Implement the smallest boundary-first hardening sequence:

1. Define an effective privacy classification for every `FieldSpec` from its
   explicit flags, semantic type, field name, distribution, and configured
   privacy rules.
2. Add `assert_spec_safe(spec)` in the safety layer. It must reject raw
   categorical values and unsafe distributions for sensitive or unknown fields
   before generation. The default project invariant must not be weakened by a
   caller-provided opt-out flag.
3. Call the check from spec loading, the public generation functions, the
   workflow bundle, the agent service, and the generator MCP service. The
   checks should be idempotent so defense-in-depth does not change behavior.
4. Split Trino execution into a private internal executor and a public safe
   service. Public calls accept validated query objects or use dedicated
   metadata/profile methods. No public function should accept arbitrary SQL
   and pass it directly to the DB-API cursor.
5. Add tests at the lowest service boundary and at every public adapter. The
   same malicious fixtures must be rejected through Python, CLI, and MCP.
6. Correct contract drift: implement validation flags, wire locale into Faker,
   fix container version defaults, bound JSON input shape, and extend the
   manifest with enough runtime information to explain reproducibility.
7. Run the RC audit and publish evidence against the exact candidate artifacts.

## Data And Contracts

Affected areas:

- `src/test_data_agent/safety.py`: spec-level privacy gate and safe errors.
- `src/test_data_agent/core/privacy.py`: effective classification and masking
  policy; no endpoint-preserving raw masks for sensitive values.
- `src/test_data_agent/generation/entity_generator.py` and
  `src/test_data_agent/io/workflows.py`: mandatory pre-generation enforcement.
- `src/test_data_agent/mcp_generator_server.py`: spec validation before MCP
  generation.
- `src/test_data_agent/mcp_trino_server.py`: private executor and safe public
  operations.
- `src/test_data_agent/validation/reconciliation.py`: honor the supported
  `ValidationSettings` contract or remove unsupported flags.
- `src/test_data_agent/core/settings.py` and generator setup: effective Faker
  locale and documented mode semantics.
- `src/test_data_agent/io/artifacts.py`: reproducibility metadata and output
  evidence, including generator/runtime/serializer identity as appropriate.
- `compose.yaml`, `Dockerfile`, and release checks: version consistency.
- `src/test_data_agent/io/readers.py`: bounded JSON row, cell, and nested-value
  handling.
- `tests/`: direct API, adversarial privacy, SQL, contract, and RC smoke tests.
- `docs/roadmap.md`, README, SECURITY, support/governance docs, and the dated
  security review: public release evidence and accepted-risk disposition.

## Failure Modes

- Unsafe specs fail before any generated row or output artifact is written.
- Unsafe SQL fails before a DB-API cursor is created or executed.
- Validation configuration errors fail closed with a clear contract error;
  silent ignoring of supported settings is not allowed.
- A locale or dependency identity that cannot be recorded causes the manifest
  to be incomplete and the reproducibility check to fail.
- Release drift between package, Docker, Compose, image labels, and release
  metadata blocks the RC.
- Failed checks leave no successful-looking partial output and do not expose
  source values in errors or logs.

## Alternatives

### Validate only in CLI and MCP wrappers

Rejected. The review demonstrated that direct Python entry points are a real
and documented surface. Transport-level validation is not a sufficient trust
boundary.

### Keep `execute_query()` public and document it as internal

Rejected. A public function that accepts SQL is too easy to misuse and
contradicts the read-only project contract. Raw execution must be private.

### Add more regexes without changing the boundary

Rejected as the primary fix. Detection improvements are useful, but a missing
spec-level gate and exact-row-only protection remain architectural problems.

### Move all hardening to post-1.0

Rejected for P0 findings. The RC must validate the core safety promise before
it becomes the stable compatibility baseline.
