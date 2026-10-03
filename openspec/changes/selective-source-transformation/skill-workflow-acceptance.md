# Installed offline skill-guided acceptance — 2026-10-02 UTC

Executable harness: `skill-workflow-acceptance.py`. This is deterministic offline
guided-caller acceptance, not an external model benchmark or automatic registration
of a skill into another agent. No product monkeypatch, provider or database calls.

Both installed `SKILL.md` resources are discovered using the documented
`importlib.resources.files("test_data_agent").joinpath("skills", name, "SKILL.md")`
path. Installed version/help determine capabilities; the guidance chooses the
reviewed-spec generation route for synthetic data and the distinct review/execute
route for one-to-one transformation. Only fictional local fixtures are used.

- Usage: reviewed spec → seeded generation → validation, three rows; replay
  produces byte-identical CSV. Manifest declares synthetic and no source-row copying.
- Transformation: saved policy → value-free review digest → public execution,
  ordered output readback. Source/replacement markers are absent from review/status.
  Changing to direct preserve without a receipt rejects and leaves no output or
  receipt; the guided caller does not impersonate a controlling-TTY operator.
- Unavailable capability: actual separately installed public baseline1.5.0 rejects
  transform-execute help with exit2. Caller stops, with no generation substitute,
  output or receipt. No fake command inventory or patched product parser.

Installed candidate wheel SHA-256:
`30a609b8be9b2e977ca596f594d9ea467741ce8fdbb8cfff49cd7ba0c90ab55d`;
target `/private/tmp/apa-matrix-installed.8cYJ0f/installed`, development1.5.0.
Python3.14.2 locked environment `/private/tmp/apa-py314-matrix.baFOFT/venv`.
Harness SHA-256: `37c481ca54aca14e32cbfeb91e2f3bd3e73d92bb9a0bc4e6834ef6598883806a`.
Run with candidate-only PYTHONPATH and pytest `-o pythonpath=. --no-cov`.
For the baseline case set `APA_SKILL_BASELINE` to the actual baseline install;
without it the test explicitly skips, never simulates a pass.

Results: usage1 passed3.17s initial run; transformation1 passed2.29s corrected
focused run; unavailable baseline1 passed0.54s focused run. Not a single fresh
combined3-case run. Initial failures were harness text whitespace/case assumptions
and a removed historical baseline directory. Normalize skill text whitespace;
restore published1.5.0 to `/private/tmp/apa-skill-baseline.TjzfRV` with uv,
no dependencies or changes to the primary environment. Offline cache lookup was
empty; package retrieval then succeeded. Baseline METADATA SHA-256
`97d4e638c8507109d5d24968ee125980da29e0c4b68a015580b7e24fcbde32fc`
identifies inspected metadata, not a wheel digest. Ruff/diff-check passed.

This adds complete local guided workflows beyond packaging/help discovery.
It is not final reviewed1.6.0rc1, public artifact acceptance, human permission
for any real dataset or evidence of future integrations. Final RC gates remain.
