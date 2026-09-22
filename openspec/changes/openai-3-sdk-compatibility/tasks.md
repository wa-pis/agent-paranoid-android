# Tasks: openai-3-sdk-compatibility

- [x] Wait for and identify a stable OpenAI Python SDK 3.x release; record the
  exact version selected for evaluation.
- [x] Rebase PR #483 onto current `main` or supersede it with a focused
  implementation PR; do not merge its range-only diff.
- [x] Run `tests/test_openai_provider.py` and provider doctor coverage against
  the selected 3.x release using fake transports, placeholder credentials, and
  synthetic metadata only.
- [x] Add focused regression tests for every SDK request, structured-response,
  timeout, exception, or cleanup behavior changed by 3.x.
- [x] Verify that bounded requests, response-size limits, redacted public
  errors, no-store behavior, and the fingerprint-bound human review gate remain
  enforced.
- [x] Update both OpenAI declarations in `pyproject.toml`, the reviewed entry in
  `.github/dependency-compatibility.toml`, and `uv.lock` in one change.
- [x] Update `docs/reference/dependency-compatibility.md` with the selected 3.x
  version and the evidence supporting the `<4.0.0` upper bound.
- [x] Add a concise changelog entry for OpenAI SDK 3.x compatibility.
- [ ] Run the minimum OpenAI profile and the full supported Python 3.11-3.14
  matrix.
- [x] Run `scripts/check_release.sh` and record the successful release-gate
  evidence before merge.

## Local evidence (2026-09-23)

- Stable candidate: OpenAI 3.18.0, Python 3.13.14, isolated environment.
- Provider and doctor contracts: 45 passed, including offline real-SDK
  success/error HTTP exchanges using its httpx2 backend (httpx on SDK 2).
- Full release gate passed: 1291 tests, 10 live integrations skipped,
  90.34% coverage, lint, types, licenses, budgets, schema and quickstart.
- The minimum and Python 3.11–3.14 CI matrix remains the merge gate.
