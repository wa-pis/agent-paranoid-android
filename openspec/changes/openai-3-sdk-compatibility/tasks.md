# Tasks: openai-3-sdk-compatibility

- [ ] Wait for and identify a stable OpenAI Python SDK 3.x release; record the
  exact version selected for evaluation.
- [ ] Rebase PR #483 onto current `main` or supersede it with a focused
  implementation PR; do not merge its range-only diff.
- [ ] Run `tests/test_openai_provider.py` and provider doctor coverage against
  the selected 3.x release using fake transports, placeholder credentials, and
  synthetic metadata only.
- [ ] Add focused regression tests for every SDK request, structured-response,
  timeout, exception, or cleanup behavior changed by 3.x.
- [ ] Verify that bounded requests, response-size limits, redacted public
  errors, no-store behavior, and the fingerprint-bound human review gate remain
  enforced.
- [ ] Update both OpenAI declarations in `pyproject.toml`, the reviewed entry in
  `.github/dependency-compatibility.toml`, and `uv.lock` in one change.
- [ ] Update `docs/reference/dependency-compatibility.md` with the selected 3.x
  version and the evidence supporting the `<4.0.0` upper bound.
- [ ] Add a concise changelog entry for OpenAI SDK 3.x compatibility.
- [ ] Run the minimum OpenAI profile and the full supported Python 3.11-3.14
  matrix.
- [ ] Run `scripts/check_release.sh` and record the successful release-gate
  evidence before merge.
