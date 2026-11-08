# Design: CPython 3.15 Compatibility

## Existing Contract And Touchpoints

`pyproject.toml` declares Python >=3.11 and classifiers through 3.14. The quality
and wheel matrices in `.github/workflows/ci.yml`, support policy, dependency
compatibility profiles and documentation tests currently enumerate 3.11–3.14.
Ruff and mypy target 3.11 intentionally: keep the oldest supported syntax and
typing baseline. No new language feature is needed to add interpreter support.

Update implementation touchpoints together: `pyproject.toml`, `uv.lock` when
necessary, CI quality/wheel/dependency jobs, `.github/dependency-compatibility.toml`,
`scripts/check_dependency_compatibility.py` if its profile model needs expansion,
runtime/dependency policy in `docs/reference/`, `docs/release.md`, corresponding
Russian guidance and focused documentation/packaging tests. Inspect matrix
generation and all callers before editing rather than adding a parallel policy.

## Verify Before Selecting Versions

The official [release page](https://www.python.org/downloads/release/python-3150/)
and [PEP 790](https://peps.python.org/pep-0790/) were checked on 2026-11-08:
3.15.0 is stable and 3.15.2 is the latest release listed in the schedule. Use a
current stable 3.15 patch and record its exact installed version. Recheck
official status before implementation rather than pinning an obsolete patch.
Use official dependency metadata/release notes to audit Faker, Pydantic and
pydantic-core, PyYAML, PyArrow, MCP, sqlglot, Trino, Psycopg, OpenAI, GigaChat
and their resolved dependencies. Include the build/test/tooling dependencies.
Inspect wheel tags for existing supported runner architectures; do not infer
native support from a successful resolver or another Python version.

Keep the base install independent of extras. Exercise base, each documented
extra and `all` from the built artifact in clean environments without the source
checkout on the import path. Preserve existing minimum profiles on 3.11. If
3.15 needs higher dependency minima, document and test a compatible version
marker/profile instead of blindly installing old native minima or raising
requirements for every interpreter. Regenerate the lock with the project's
declared uv version and review changes. No unsupported extra may disappear
silently from `all` or be omitted from the advertised support promise.

## CI Promotion

The verified stable release selects blocking supported-version jobs. If a
future investigation intentionally exercises a prerelease, use a clearly named experimental job with explicit
prerelease selection, separate from the required supported-version matrix.
Record failures and upstream blockers. It cannot replace or weaken any current
required job. When stable and compatible, add the exact 3.15 series to the full
quality, isolated wheel and latest-all compatibility matrices. Keep the 3.11–3.14
jobs and existing supply-chain/security gates. Supported 3.15 jobs must be
blocking in CI and satisfy applicable repository rules before release. If
native dependencies block support, keep the task open and report the blocker;
do not announce partial support as completed support.

## Runtime Evidence

Run existing safety/schema/SQL/provider contracts with fictional fixtures and
fake transports only. Exercise real bounded MCP SDK stdio planning, inspection,
fingerprint invalidation, approval consumption and recovery without issuing
human approvals from MCP. Verify both scalable engines on Linux/macOS using
spawn workers, 1/2/4-worker and differing-batch output comparisons, cancellation,
deadline/memory/work/output limits, worker reaping and atomic cleanup. Preserve
all mandatory privacy, schema and relational checks. Capture actual interpreter,
OS/architecture, dependency versions, commit and test outcomes in evidence.

Same-environment determinism remains required. Cross-Python byte identity is
not promised by the existing dependency policy; compare repeated runs within
each environment and record differences between environments honestly. Any
algorithm/engine change needs its own versioned contract and specification.
Do not attribute speedups to 3.15 without isolated comparable measurements.

## Delivery And Rollback

This proposal changes no runtime, classifiers or release claim. Implementation
must update public documentation and changelog only after evidence supports
promotion. Run the full release gate and applicable artifact/preflight/review
requirements before a separately authorized RC. If an experimental probe fails,
retain the existing supported matrix and track the incompatibility. If a
promoted job regresses before publication, fix it or withdraw the proposed
support claim explicitly; never hide the failure with allowed failure.
