# Local verification: 2026-10-22

## Scope And Identity

This is local working-tree evidence, not an exact-commit public deployment or
release acceptance. Runtime code under `src/` is unchanged. Historical release,
review and ADR records are retained. New builds identify uncommitted docs as
`+dirty` and public verification rejects that identity.

GitHub's latest stable release is `v1.6.0`, published 2026-10-17. Its catalog
source is `258c035c22408becf17ab090635710a50dda8ccc`; public-verification run
`39018919261` was rechecked as completed/successful for that exact source and
`verify-published-release.yml`. This is reused package evidence, not acceptance
of these documentation changes.

## Content And Navigation

- Primary navigation reduced from 58 to 22 page entries. See `inventory.md` for
  the per-page disposition and canonical owner.
- Home, installation and first CSV instructions shortened. The duplicate
  221-line dataset workflow is now a section-preserving bridge to canonical guides.
- Current guides no longer ask readers to reconstruct RC promotion history.
  Source-free generation, mixed-origin transformation and local-only exact
  preservation approval remain explicit at their points of use.
- All rendered local links/anchors were checked across 426 root and native mike
  version/alias HTML pages with zero broken targets. Legacy RC anchors and shortened-page bookmarks remain reachable.

## Commands And Results

- `python -m pytest tests/test_documentation.py tests/test_documentation_build.py
  tests/test_release_artifacts.py tests/test_ci_change_scope.py
  tests/test_agent_guidance.py tests/test_containers.py -q`: 168 passed.
- `python -m ruff check src tests scripts`: passed.
- `python -m mypy`: passed for all 155 configured source files.
- `python -m compileall -q src tests scripts`: passed.
- `mkdocs build --strict`: passed, including retained historical pages/anchors.
- Official OpenSpec CLI 1.14.3: change and `public-documentation` baseline both
  passed `validate --strict`. The temporary CLI adds no repository dependency.
- `python -m scripts.build_documentation ... --verify-release`: built current
  stable root, mike-managed 1.6.0 guide/copy alias and all four download formats.
  Real plugin integration tests retained stable content byte-for-byte while
  adding a 1.7.0rc1 preview, including previous version directories.
  Portable metadata, artifact hashes and standalone internal chapter links passed.
  Public checks also validate the native stable alias and its destination identity.
- A locally built wheel was installed separately from the source tree. `doctor`,
  offline demo, the Python API example and CSV walkthrough passed using fictional
  inputs and new temporary destinations. Their manifests reported synthetic data,
  no copied source rows and valid validation. These are not live database,
  provider or real-dataset tests.
- The final 70-page plugin-built PDF was rendered with an isolated Chrome profile, text
  extracted and all pages visually inspected. No content exceeded the checked page margins.
  Browser-control UI inspection was unavailable; no interactive browser claim is made.

- Dependency-license checks passed for all 109 installed distributions; new tools
  are confined to the documentation group. The lock adds only documentation
  dependencies and retains the latest main certifi security update.
- On owner request, local `main` was fast-forwarded from `cfd8812d` to `fe4ac35a`
  and all documentation edits restored. The single CHANGELOG conflict retained
  both upstream guidance/security entries and the documentation changes. Runtime
  code remains unchanged. The pre-update stash is retained as a recovery copy.
- GitHub Pages remains the host. No Read the Docs service configuration, account
  change, public deployment or remote state push was performed locally.

## Earlier Broader Suite Limitations

Before the main refresh and standard-plugin integration, the broader coverage
run completed with 4203 passed, 23 skipped and 10 failures;
coverage was 91.48%, above the 85% threshold. It is not a green full release gate.
The failures were in unchanged runtime tests:

- Eight controlling-terminal/stdio cases failed in the sandbox. Separate
  unrestricted terminal runs passed the controlling-terminal group (6 cases),
  common MCP stdio group (6 cases) and individual CLI receipt/execution case.
  One grouped replay first hit its one-second output wait, then passed alone.
- Two GigaChat property tests exceeded Hypothesis's 200 ms deadline in the
  instrumented run. A targeted replay passed one and reported a timing
  `FlakyFailure` for the other (273.78 ms versus 153.22 ms on replay), not a
  failed value invariant. Provider code and test deadlines were not changed.

The complete runtime suite was not repeated for this documentation-tooling
revision; these earlier limitations remain visible for reviewed-commit CI. No live
preservation approval, dataset permission or new runtime activation follows
from these fictional tests or documentation exports.

## Public Delivery — 2026-10-22

PR #631 merged at `d10145be9f01085eb1648b7192045ab020095b20` after required
checks passed. The blocking dependency audit was cleared by updating only the
locked OpenTelemetry API to 1.45.1; the exported dependency set then passed
pip-audit without exceptions. Dependency ranges were retained.

[Documentation run 39842360108](https://github.com/wa-pis/agent-paranoid-android/actions/runs/39842360108)
successfully built, deployed, publicly verified and retained the native mike state.
An independent invocation of `scripts.verify_documentation` against
`https://wa-pis.github.io/agent-paranoid-android/` also passed with the expected
identity: package 1.6.0 at `258c035c22408becf17ab090635710a50dda8ccc`,
documentation revision `d10145be9f01085eb1648b7192045ab020095b20`, maintained
stable guidance. Verification included the public entry page, version selector,
stable alias, download manifest and SHA-256 hashes of PDF, standalone HTML,
Markdown ZIP and offline-site ZIP.

No package version was changed or republished. Earlier local suite limitations
remain historical evidence; they are not relabelled as new runtime acceptance.
Collect user feedback before archiving. A failed future deployment still uses
the documented previous-artifact recovery; no automatic rollback is claimed.
