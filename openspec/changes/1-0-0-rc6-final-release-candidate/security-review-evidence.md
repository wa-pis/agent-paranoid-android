# RC6 Independent Security Review Evidence

Status: **Findings recorded — remediation required**

This file records successive independent reviews. A completed review is
evidence, not approval: the RC6 acceptance checklist remains incomplete until
the exact immutable RC6 commit has an explicit approval disposition.

## Attribution

- Reviewer: **codex-security-reviewer-rc6** (stable pseudonym)
- Base release: **v1.0.0rc5**
  (`c475d1ca8ea58fc317a37bd89f4e577447278466`)
- Reviewed commit: **29afe41b574e5e6ffe0570ac5f8cbd4447b2f90b**
- Review date: **2026-08-08 UTC**
- Scan ID: **a79fde05-6eea-460c-8e55-fa45e7b13883**
- Review record: [Issue #330](https://github.com/wa-pis/agent-paranoid-android/issues/330)
- Signature or approval URL: **Pending — PRs #331 through #335 are remediation
  evidence, not approval of an immutable RC6 commit**

## Scope

- Rare-category sanitization and structural-identity preservation
- OpenAI per-call metadata, provider-error isolation, and redaction
- Trino deployment profile parsing and shared-hardened fail-closed startup
- MCP admission limits, backend error redaction, and opt-in row-returning
  privacy policy
- Semantic-provider execution/output boundaries and filesystem publication
  race resistance
- CLI/log diagnostic escaping and deployed repository/PyPI release controls
- Release version identity, public artifact verification, and RC6 acceptance

## Reviewed Files

The reviewed diff was exactly
`v1.0.0rc5..29afe41b574e5e6ffe0570ac5f8cbd4447b2f90b`:

```text
CHANGELOG.md
README.md
docs/getting-started/installation.md
docs/index.md
docs/rc6-acceptance-checklist.md
docs/reference/configuration.md
docs/release-evidence-1.0.0rc5.md
docs/release.md
docs/roadmap.md
mkdocs.yml
openspec/changes/1-0-0-rc5-public-release-invocation-hardening/tasks.md
openspec/changes/1-0-0-rc6-final-release-candidate/design.md
openspec/changes/1-0-0-rc6-final-release-candidate/proposal.md
openspec/changes/1-0-0-rc6-final-release-candidate/security-review-evidence.md
openspec/changes/1-0-0-rc6-final-release-candidate/tasks.md
pyproject.toml
src/test_data_agent/advisor.py
src/test_data_agent/cli_doctor.py
src/test_data_agent/mcp_trino_server.py
src/test_data_agent/providers/openai.py
src/test_data_agent/trino_config.py
src/test_data_agent/trino_work_budget.py
src/test_data_agent/version.py
tests/test_advisor.py
tests/test_cli_doctor.py
tests/test_dataset_spec_contract.py
tests/test_documentation.py
tests/test_openai_provider.py
tests/test_release_artifacts.py
tests/test_trino_config.py
tests/test_trino_work_budget.py
tests/test_version.py
uv.lock
```

## Findings And Disposition

| Severity | Finding | Disposition | Evidence |
| --- | --- | --- | --- |
| Low | RC6-S1: profile-indexed replacement can leave a raw rare category in a reordered baseline and provider-bound `AdvisorRequest` | **Closed by PR #335** | [PR #335](https://github.com/wa-pis/agent-paranoid-android/pull/335), merge `5b3ad7f`; exact-tree follow-up reproduced no leak and verified persisted placeholder provenance |
| Low | RC6-S2: provider-call and structured-validation failures can retain provider context or derive public text from a dynamic exception class | **Closed by PRs #334 and #336** | [PR #334](https://github.com/wa-pis/agent-paranoid-android/pull/334), merge `33ba64e`, removes retained `__cause__`/`__context__`; [PR #336](https://github.com/wa-pis/agent-paranoid-android/pull/336), merge `f459ab8`, replaces dynamic class names with the fixed `OpenAI advisor request failed` message |
| Low | RC6-S3: SDK client initialization failures can retain or directly expose raw exception text | **Closed by PRs #334 and #336** | [PR #334](https://github.com/wa-pis/agent-paranoid-android/pull/334), merge `33ba64e`, detaches expected `OpenAIError`; [PR #336](https://github.com/wa-pis/agent-paranoid-android/pull/336), merge `f459ab8`, catches ordinary constructor exceptions and raises the fixed local initialization error outside the handler |
| Low | RC6-S4: incomplete responses interpolate raw `response.status` into the public advisor error | **Closed by PR #333** | [PR #333](https://github.com/wa-pis/agent-paranoid-android/pull/333), merge `e8aba91`; fixed local message and synthetic status-redaction regression |
| Informational | RC6-S5: provider-call and structured-validation error text no longer appears in normal formatted tracebacks | **Closed by PR #331** | [PR #331](https://github.com/wa-pis/agent-paranoid-android/pull/331), merge `d491acb` |
| Informational | RC6-S6: placeholder-shaped baseline literals are reserved from generated placeholder names | **Closed by PR #332** | [PR #332](https://github.com/wa-pis/agent-paranoid-android/pull/332), merge `e448b8f` |
| None | OpenAI per-call metadata ownership and bounded metadata fields | **No issue found** | Concurrent success/error tests and static review |
| None | Trino profiles, cumulative ceiling, startup ordering, and doctor status | **No issue found** | Focused tests and static review of the RC6 diff |
| N/A | Immutable RC6 tag, public artifacts, approval URL, and final release gates | **Pending; release-blocking** | `docs/rc6-acceptance-checklist.md` |

## PR #335 exact-tree follow-up

The independent follow-up reviewed PR #335 from
`33ba64ea1e49658c500ee737fb5c4fd3a9693729` to
`17d45656d24769c5f5560878bab6049f2bf91517`. The signed GitHub merge commit
`5b3ad7f9ae54d8cb23bafe2a7d0b5734e45dc56e` has tree
`08f0f095d18dc728e9b6d3e4d71333f025985ce5`, identical to the reviewed PR
head, so the finding dispositions apply to that exact merge tree.

- Reviewer: **codex-security-reviewer-rc6**
- Review date: **2026-08-08 UTC**
- Scan ID: **0ba29f2e-47fe-4baa-af7a-4b4a64cbe348**
- Diff snapshot: **codex-security-snapshot/v1:sha256:8ed139457a66f93559547b6e46f75cafc7d42a32be7312b89c51ae723481d321**
- Focused checks: **63 passed** in `tests/test_advisor.py` and
  `tests/test_openai_provider.py`; no live OpenAI or Trino access

Reviewed diff and supporting boundary files:

```text
src/test_data_agent/advisor.py
tests/test_advisor.py
src/test_data_agent/agent_advising.py
src/test_data_agent/providers/openai.py
src/test_data_agent/cli_agent.py
src/test_data_agent/cli.py
tests/test_openai_provider.py
```

The canonical RC6-S1 through RC6-S4 rows above contain this scan's
dispositions. The scan produced one reportable Low finding, mapped to existing
RC6-S3, and one security-suppressed but acceptance-relevant mismatch, mapped to
existing RC6-S2; no new RC6 finding identifier was created. PR #335 is approved
for RC6-S1 only. Trino trusted-local/shared-hardened behavior was unchanged and
showed no new regression. Approval of the exact merge commit remains blocked
pending the residual RC6-S2/S3 remediation and another exact-commit review.

## PR #336 S2/S3 closure verification

PR #336 closed the two residual OpenAI error-boundary findings. The behavior
was reverified on current main commit
`6a4f20816464f28083a98d9f5004269437131906` with synthetic failures only; no
live OpenAI call was made.

- RC6-S2: provider and structured-validation failures use fixed local text and
  retain neither `__cause__` nor `__context__`.
- RC6-S3: both `OpenAIError` and ordinary `RuntimeError` constructor failures
  become the same fixed local `ValueError` without retained exception chains.
- Focused command: `pytest tests/test_openai_provider.py -k
  'does_not_retain_initialization_error or does_not_leak_provider_error_text or
  records_usage_for_invalid_structured_output' -q`
- Result: **6 passed, 30 deselected**.

## Current-tree critical review

The follow-up repository-wide review covered the current RC6 worktree at
`17d45656d24769c5f5560878bab6049f2bf91517` plus the uncommitted RC6 planning
files. It used static source tracing and synthetic local reproductions only;
no production data, live Trino/OpenAI service, network state, or external
repository settings were used.

- Scan ID: **66c3aa7c-5012-44bb-8ba0-e53f8ffb9135**
- Completed: **2026-08-08T21:31:57Z**
- Coverage: **566 repository files; 11 reportable findings; 2 high, 8 medium,
  1 low; partial because external settings and deployment-specific races were
  not observable**
- Report: completed Codex Security scan; final immutable artifacts are stored
  in the scan workbench and are not release approval by themselves.

| Severity | Current-tree finding | Disposition |
| --- | --- | --- |
| High | Raw common categorical profile values can reach the external advisor | **Closed by PR #337**; current-main synthetic regression verifies common names and address-like values are replaced with deterministic field-scoped labels |
| High | Provider formulas can inject arbitrary constants into generated rows | **Open; RC6 release-blocking** |
| Medium | Sensitive numeric Trino extrema/percentiles can reveal source values | **Closed by PR #338**; query, masking, safety, persistence, and generation regressions verify only coarse numeric shape survives |
| Medium | Generator MCP stdio has no pre-parse raw-frame/final-response budget | **Open; RC6 release-blocking** |
| Medium | JSON structural limits run after full parsing/materialization | **Open; RC6 release-blocking** |
| Medium | Pull requests control the classifier that can skip required checks | **Open; RC6 release-blocking** |
| Medium | Release publication is bound to tag/version, not approved commit identity | **Open; RC6 release-blocking** |
| Medium | RC6 acceptance evidence is not enforced by the release workflow | **Open; RC6 release-blocking** |
| Medium | CSV output does not neutralize spreadsheet formula markers | **Open; RC6 required hardening** |
| Medium | Formula/validation errors can reflect provider-controlled text | **Open; RC6 required hardening** |
| Low | Public workflow API accepts an unsafe profile artifact name | **Open; RC6 required hardening** |

### RC6-S7 closure verification

[PR #337](https://github.com/wa-pis/agent-paranoid-android/pull/337), merge
`1a7d1ff`, replaces every string categorical value in advisor profiles and
baseline specs with a deterministic field-scoped synthetic label before the
request is fingerprinted or serialized. The behavior was reverified on current
main commit `a8a4fe4cae807de7d5fe1af59074999e72c3469c` using synthetic fixtures only;
no live OpenAI call was made.

- Focused command: `pytest tests/test_advisor.py -k
  'categorical or category_placeholder or persisted_review' -q`
- Result: **7 passed, 23 deselected**.
- Covered values include a common person name, an address-like string,
  baseline-only categories, placeholder collisions, persisted review rebuilds,
  and repeated deterministic construction.

### RC6-S8 closure verification

[PR #338](https://github.com/wa-pis/agent-paranoid-android/pull/338), merge
`89fb0cf`, removes exact extrema and percentiles from sensitive numeric Trino
profiling at the query and masking boundaries. Profiles, inferred specs, MCP
planning persistence, and generated values retain only coarse sign and decimal
order through `numeric_shape`. Generation follows the original source order of
magnitude without preserving singleton values or artificially increasing the
order.

The behavior was reverified on current main commit
`4978783d6ffd4782057934462a24f6dcbd8534f7` with synthetic fixtures only; no
live Trino access was used.

- Focused command: `pytest tests/test_safety.py tests/test_trino_masking.py
  tests/test_trino_query_builders.py tests/test_mcp_generator_server.py -q`
- Result: **66 passed**.

## Additional RC6 closure findings

The review also identified deployment-conditional or lower-confidence risks.
They are now mandatory RC6 closure items rather than a deferred RC7 backlog.
Their lower confidence changes the evidence required, not the release scope.

| Severity | Finding | Disposition |
| --- | --- | --- |
| Medium | Active MCP request registry and shared Trino concurrency have no global admission cap or complete cancellation/disconnect teardown | **Open; RC6 release-blocking** |
| Medium | Trino driver failures and catalog/schema enumeration can expose backend-controlled error or metadata text | **Open; RC6 release-blocking** |
| Medium | Explicit opt-in `run_safe_select` can return unrecognized raw names, addresses, or other sensitive strings | **Open; RC6 release-blocking** |
| Medium | Semantic providers are not uniformly bounded, deterministic for a seed, or restricted to synthetic identity output | **Open; RC6 release-blocking** |
| Medium | Filesystem publication and CLI overwrite paths are vulnerable to symlink/TOCTOU races without descriptor or inode revalidation | **Open; RC6 release-blocking** |
| Low | Single-entity publication has no explicit completion/read-validation contract and bundle publication can replace sibling artifacts without approval | **Open; RC6 required hardening** |
| Low | CLI and log output can emit unescaped provider-controlled metadata, paths, or errors | **Open; RC6 required hardening** |
| High | Deployed branch/tag protection, required checks, and PyPI Trusted Publisher settings were not observable in the repository scan | **Open; RC6 external-evidence gate** |

These findings require focused synthetic regressions, implementation review on
the exact RC6 commit, and external configuration evidence where the property
cannot be established from repository contents alone.

## Review Conclusion

**Blocked.** PR #335 closes RC6-S1, PR #333 closes RC6-S4, PRs #334 and #336
close RC6-S2 and RC6-S3, PR #337 closes RC6-S7, and PR #338 closes RC6-S8. Do
not tag or promote RC6 until RC6-S9 through RC6-S20 and their synthetic
regressions are closed
or explicitly approved, an independent reviewer approves the exact fixed
commit, and the immutable tag, public artifacts, final gates, external
configuration evidence, and verifiable approval link are recorded. The
follow-up scan of `5b3ad7f` is a blocking review, not release approval.
