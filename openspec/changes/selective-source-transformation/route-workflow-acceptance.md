# Private saved-policy route acceptance — 2026-10-01

## Explicit temporal output acceptance — 2026-10-02 UTC

`temporal-workflow-acceptance.py` exercises a saved local CSV mapping and public
review/execute against installed wheel30a609b8 (full identity below). CSV output
keeps the replacement string literal, with no implicit parsing or UTC. Typed
Parquet and SQL output declare input format, output format, source timezone
Europe/Samara and target UTC: readback verifies the selected instant and SQL
TIMESTAMPTZ literal. Review/status omit source/replacement markers; original
source/policy/mapping bytes remain unchanged. No TTY receipt, external connection
or product monkeypatch; every cell is actually replaced, not preserved.

Two scenarios (CSV/Parquet) passed in1.93s initial three-case run; SQL assertion
initially assumed policy-rendered text rather than the serializer's TIMESTAMPTZ
literal. Corrected only the harness and reran SQL:1 passed0.75s. No combined green
rerun claimed. Ruff/diff-check pass. Harness SHA-256:
`be3f39834371464107f258e85c569bfe6795c21cba1488db36280d60602dfab3`.
Run installed-only PYTHONPATH with pytest `-o pythonpath=. --no-cov`.

Important boundary: this covers textual DATETIME replacement and explicit output
conversion, not implicit matching of equivalent instants or native Arrow timestamp
input. Inspection confirms the native input adapter currently rejects timestamps
as an unsupported native type; no passing native timestamp claim is made. Full
input-type coverage and final RC contracts must retain this limitation explicitly.

## Installed public-entry and refusal matrix — 2026-10-02 UTC

`scripts/accept_transformation_routes.py --public` passed all twelve typed routes
against the same installed development wheel recorded below. Public CLI
`transform-execute --json` and the actually registered `execute_transformation`
application function produce artifacts identical to the bounded publication
contract. MCP application-function parity is not twelve-route SDK/wire parity;
prior real SDK stdio acceptance remains separate evidence.

For every route the public CLI also rejects stale snapshot digest, one-byte
output ceiling and existing destination: 36 refusal cases. No new destination
or staging entry remains; the fictional existing owner artifact stays byte-exact.
Refusal output contains none of the fixture's source/replacement text markers.
No production data, live backend, SQL execution, product guard monkeypatch or
preservation receipt issuer is involved.

Harness SHA-256: `b8cf5366a5ec9716066dd83c0fcab1b19f7076b38038ed0da55a1c474f35fb57`.
Ruff and diff-check pass. Initial public CLI harness assertion expected the
private helper's bare result; corrected it to consume the documented JSON
`result` envelope, with no product change. Final invocation passed all12 plus
36 refusal assertions. The final printed scope string retains historical closed
wording; `--public` branches and this evidence distinguish actual entry points.
DATETIME conversion and skill-guided workflow remain open. This is not a
published RC, exact final-SHA review or proof of arbitrary crash/race recovery.

## Installed typed twelve-route follow-up — 2026-10-02 UTC

Extended the existing fictional harness with `--typed`; no product patch or
guard monkeypatch. All twelve combinations passed with five columns: replaced
string/integer, exact DECIMAL(5,2), DATE, and nullable string. Readback verifies
two ordered rows, explicit CSV null marker versus empty string, exact decimal
values and declared date types in Parquet and SQL literals. SQL output is inspected
as text, never executed. Captured query input uses a fictional injected Arrow
stream through actual query authorization, not a live database.

Command: `PYTHONPATH=/private/tmp/apa-matrix-installed.8cYJ0f/installed
/private/tmp/apa-py314-matrix.baFOFT/venv/bin/python
scripts/accept_transformation_routes.py --typed` (one shell command).
Installed development wheel SHA-256:
`30a609b8be9b2e977ca596f594d9ea467741ce8fdbb8cfff49cd7ba0c90ab55d`.
Harness SHA-256: `5f59636069b21b0a80a939d45287ce33176c377214fa1cd3a6f2516bfe0fa515`.
Harness base accepted main: `8670e562f50980cfd62678c6f0f51d4887cb8961`.
Installed code remains the previously recorded development candidate, not a new
wheel of this documentation/harness diff or a released 1.6.0rc1.

Each route compares CLI/MCP review metadata and fixed digest, closed CLI/workspace
execution artifacts and temporary publication bytes, 100% action-based replacement
provenance, unchanged input/policy bytes and removed temporary directories.
The first invocation had an incompatible Python-extension dependency overlay;
removed that overlay and used the existing locked Python environment. The next
invocation rejected a harness CSV input null marker on native inputs; corrected
the fixture to configure input markers only for CSV and output markers only for
CSV output. No product behavior changed. Final invocation completed all12.
Ruff and diff-check passed. Prior large-scale workflows were not repeated.

This supplements earlier basic routes and typed unit tests. It does not close
DATETIME conversion, every failure/rollback combination, public SDK execution
for every route, skill-guided acceptance or final exact-RC/public-artifact gates.

The installed development candidate completes all twelve combinations of CSV,
Parquet, PostgreSQL captured result and Trino captured result inputs with CSV,
Parquet and PostgreSQL SQL-file outputs. Each uses the same two-row fictional
string/integer replacement fixture, saved YAML, public CLI review, private
command execution, artifact readback, provenance checks and temporary cleanup.
SQL files are checked as text and never executed. Captures use a trusted local
Arrow stream through real query authorization, with no DB/API or monkeypatch.

Command: `PYTHONPATH=<installed-target> python scripts/accept_transformation_routes.py`.
Wheel version1.5.0 is a development artifact, not a released RC.
Wheel SHA256:90b094d4c3066bdfddcd1cf1c84eb37b2871fc0bffa93993038d40575dd1ab93.
Harness SHA256:a9f842ae1baa9f47d4cf8a787704afdb334b0db93a6a280cc5d36d80bfa7d1bc.
Base99cc4d0; Python3.11.2/Darwin arm64. Installed target:
/private/tmp/apa-routes-wheel.n4kBWV/installed.

Result: all12 passed. CLI review digest equals the deterministic request;
review output excludes source and replacement literals. Private file-command
execution reopens fixed snapshots and validates the expected digest. Separate
artifact readback checks every output row/cell, native integer fidelity in
Parquet, exact SQL inserts,100% replacement provenance and unchanged source/
policy bytes; fixture and publication directories are removed.

This basic matrix does not certify all null/decimal/temporal semantics, source
preservation, live query capture, public execution/MCP parity, scale per route
or RC readiness. Prior CSV and PostgreSQL scale evidence was not repeated.
Next: connect common execution/publication contracts to CLI/Python/MCP under
the existing safety amendments and independent activation review.
# MCP service parity follow-up — 2026-10-01

## Closed publication integration follow-up

Changed publication path verified on a freshly built, isolated installed wheel:
all 12 fictional routes passed again (CLI/MCP service review, common private
command, full artifact readback, provenance and cleanup). Accepted large-scale
workflows were not replayed. Wheel SHA-256:
`ac0ecb1912138d7ca8ee3177f75eeb7a9ecb777b72b3d7ba3d3836fcf0d9d21b`;
path `/private/tmp/apa-activation-wheel.6RCKz6/agent_paranoid_android-1.5.0-py3-none-any.whl`.
Harness SHA-256 remains
`6c9bb0783050ea20e59bcfe51ece3e903780e4808abcbc9394b58244c918be6d`.

Installed-wheel focused acceptance: 15 tests passed with pytest source-path
injection disabled (`-o pythonpath=`). Scope: existing fictional TTY-issued
receipt consumed by preservation/publication, stale or missing approval blocked,
fixed review to private destination and configured session ceiling rejection.
This is private fictional test authority, not human approval of any real data,
nor evidence of public activation. No external database connection or SQL writes.
Development version remains 1.5.0, not a published release candidate.

`python -m build` was unavailable locally; existing pip/Hatch wheel build used
`--no-deps --no-build-isolation` successfully, without changing the primary venv.

All 12 fictional small route combinations passed with installed CLI and MCP
application-service review parity (same review metadata and snapshot SHA-256),
followed by the existing private executor, full artifact readback, provenance,
unchanged inputs and temporary cleanup. No database access or public execution.
This does not claim new-tool SDK/wire acceptance, preservation approval, full
type coverage or additional scaling acceptance.

- Wheel: `/private/tmp/apa-mcp-review-wheel.L0CxKQ/agent_paranoid_android-1.5.0-py3-none-any.whl`
- Wheel SHA-256: `398914f145cbe95113b7767949db5cd0c7dc1280b83cd737d2af4f23f67dff5c`
- Harness SHA-256: `6c9bb0783050ea20e59bcfe51ece3e903780e4808abcbc9394b58244c918be6d`
- Installed target: `/private/tmp/apa-mcp-review-wheel.L0CxKQ/installed`
- Development version 1.5.0; not a published release candidate.

Additional candidate-source SDK stdio check: the actually registered tool
returns the same shared review; outside-workspace requests fail without the
fictional path marker in wire response or stderr. Source/policy bytes remain
unchanged. `tests/test_transformation_mcp_review.py`: 3 passed. This transport
test is separate from the installed wheel service acceptance above.

## Closed CLI approval-to-execution acceptance (2026-10-02)

Installed development wheel, fictional temporary fixtures only. The unregistered
CLI candidate reads saved source/policy bytes, requires the exact review digest,
prompts through the real controlling `/dev/tty`, writes an owner-only receipt,
then consumes that receipt in a separate noninteractive execution subprocess.
Artifact readback confirms one explicitly non-sensitive preserved field and one
replacement; source values are absent from review/status output. This simulated
operator confirmation is test evidence, not approval of any real dataset.

The same suite rejects stale digests, above-session output requests, receipt
overwrite and piped APPROVE without a controlling terminal. Profile/session
output defaults are exercised. Existing receipt boundary tests remain passing.
17 tests passed in 2.70s against installed code (`-o pythonpath=`); no product
monkeypatch, database or external API. Host test escalation was required because
the execution sandbox denies `/dev/tty`. PTY output must be drained while waiting
for child exit; the prior timeout was a harness defect, not a product fix.

- Wheel: `/private/tmp/apa-cli-candidate-wheel.S7i8x4/agent_paranoid_android-1.5.0-py3-none-any.whl`
- SHA-256: `6ab034ca3be1091b614eb46db0fe527c19068800253d590f813973822632eaff`
- Installed target: `/private/tmp/apa-cli-candidate-wheel.S7i8x4/installed`
- Harness: `tests/test_transformation_cli_candidate.py` and existing receipt tests.

Not public CLI registration, MCP execution, activation review, final RC review
or published 1.6.0rc1 acceptance. Remaining workflow wiring stays gated.

### Installed common CLI/agent candidate (2026-10-02)

The changed workspace candidate was exercised from installed code, not the
source checkout:10 tests passed in2.99s with `-o pythonpath=`. CLI and agent
subprocesses consume the same exact local receipt and return identical bounded
status, provenance and dataset bytes. Four path positions reject workspace
escape before execution. Candidate remains unregistered; this is not MCP-wire
or public activation acceptance. No new database/scaling acceptance claimed.

- Wheel: `/private/tmp/apa-shared-candidate-wheel.6HPhU5/agent_paranoid_android-1.5.0-py3-none-any.whl`
- SHA-256: `2e413fe920c4f807ae0a92e7bf3ba4ca2c8b0869a257c4d24fc9457edaf9ecfb`
- Installed target: `/private/tmp/apa-shared-candidate-wheel.6HPhU5/installed`
- Harness: `tests/test_transformation_cli_candidate.py`, `tests/test_transformation_mcp_candidate.py`.
