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
| High | Provider formulas can inject arbitrary constants into generated rows | **Closed by PR #343**; provider constraints reject unsafe constants, references, target types, and sensitive targets, while post-solve privacy/type validation runs before publication |
| Medium | Sensitive numeric Trino extrema/percentiles can reveal source values | **Closed by PR #338**; query, masking, safety, persistence, and generation regressions verify only coarse numeric shape survives |
| Medium | Generator MCP stdio has no pre-parse raw-frame/final-response budget | **Closed by the focused RC6-S10 change**; generator MCP uses the shared bounded stdio writer with a fresh request budget, reserved terminal-error bytes, and focused transport wiring regressions |
| Medium | JSON structural limits run after full parsing/materialization | **Closed by the focused RC6-S10 change**; the raw-byte preflight bounds depth, nodes/containers, and scalar bytes before JSON or MCP model materialization, including escaped-scalar regressions |
| Medium | Pull requests control the classifier that can skip required checks | **Closed by the focused RC6-S12 classifier change**; CI, Security, and Containers extract and execute the classifier from the trusted PR base commit, and control-path changes fail into the heavy-check set |
| Medium | Release publication is bound to tag/version, not approved commit identity | **Closed by the focused RC6-S12 release-identity change**; release, container, and PyPI workflows verify an allowed SSH signature and exact externally accepted commit before build or publication |
| Medium | RC6 acceptance evidence is not enforced by the release workflow | **Closed by the focused RC6-S12 acceptance-manifest change**; the signed tag carries strict JSON evidence for the exact source, findings, approvals, gates, and wheel/sdist digests, and every publication path fails closed on missing or stale evidence |
| Medium | CSV output does not neutralize spreadsheet formula markers | **Closed by the focused RC6-S11 change**; the central CSV writer prefixes dangerous string cells and headers while preserving numeric values, with synthetic marker regressions |
| Medium | Formula/validation errors can reflect provider-controlled text | **Closed by the focused RC6-S11 change**; solver, business-rule, and constraint diagnostics use exact fixed reasons with detached nested exceptions and value-redaction regressions |
| Low | Public workflow API accepts an unsafe profile artifact name | **Closed by the focused RC6-S11 change**; public generation artifacts validate the profile name as one safe component before creating directories or files |

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

### RC6-S9 closure verification

[PR #343](https://github.com/wa-pis/agent-paranoid-android/pull/343), merge
`3f4d1ec`, validates advisor-proposed constraints before persistence and runs
privacy/type validation after constraint solving. String constants, unknown or
incompatible references, sensitive targets, and provider-driven field-type
changes fail closed before publication.

The behavior was reverified on current main commit
`043365ac3c4e9b5eb25ce691d348ec3cda08cd2b` with synthetic fixtures only.

- Focused command: `pytest tests/test_advisor.py tests/test_constraint_solver.py -q`
- Result: **46 passed**.

## Additional RC6 closure findings

The review also identified deployment-conditional or lower-confidence risks.
They are now mandatory RC6 closure items rather than a deferred RC7 backlog.
Their lower confidence changes the evidence required, not the release scope.

| Severity | Finding | Disposition |
| --- | --- | --- |
| Medium | Active MCP request registry and shared Trino concurrency have no global admission cap or complete cancellation/disconnect teardown | **Closed**; the transport admits at most 32 active requests, emits a fixed bounded capacity error, and clears state on teardown, while the client admits at most 8 shared Trino operations and releases its slot in `finally` |
| Medium | Trino driver failures and catalog/schema enumeration can expose backend-controlled error or metadata text | **Closed**; backend failures become the fixed detached `Trino request failed` error, while catalog/schema discovery returns only configured allowlist members with positional filtering regressions |
| Medium | Explicit opt-in `run_safe_select` can return unrecognized raw names, addresses, or other sensitive strings | **Closed**; the separate row-return policy masks every string and retains existing sensitive-name/value masking for non-strings, with regressions for heuristic false negatives |
| Medium | Semantic providers are not uniformly bounded, deterministic for a seed, or restricted to synthetic identity output | **Closed**; synchronous calls run in an isolated daemon thread with a fixed deadline, same-request replay must match, string values require the `synthetic_` namespace, and post-solve privacy/type checks remain mandatory |
| Medium | Filesystem publication and CLI overwrite paths are vulnerable to symlink/TOCTOU races without descriptor or inode revalidation | **Closed by the focused RC6-S17 change**; one descriptor-relative no-follow policy revalidates source and destination inode identity before atomic file/folder replacement and cleanup |
| Low | Single-entity publication has no explicit completion/read-validation contract and bundle publication can replace sibling artifacts without approval | **Closed by the focused RC6-S18 change**; manifest publication is last, readers verify every recorded artifact hash, and any staged-name collision requires explicit overwrite approval |
| Low | CLI and log output can emit unescaped provider-controlled metadata, paths, or errors | **Closed by the focused RC6-S19 change**; shared presentation helpers bound and escape human-facing diagnostics, while canonical audit JSON remains one bounded physical record per event |
| High | Deployed branch/tag protection, required checks, and PyPI Trusted Publisher settings were not observable in the repository scan | **Closed by RC6-S20 external evidence**; active GitHub rulesets, required checks, the deployed `pypi` environment, and public PyPI provenance for both RC5 distributions are linked below |

These findings require focused synthetic regressions, implementation review on
the exact RC6 commit, and external configuration evidence where the property
cannot be established from repository contents alone.

### RC6-S17 closure verification

The focused RC6-S17 change routes bounded text, Parquet, cache, workspace, and
folder publication through one standard-library path policy. Every path
component is opened relative to a no-follow directory descriptor; destination
and staging inode identity is checked again immediately before replacement or
cleanup. Symlinked leaves and parents fail closed, and a replaced cleanup target
is preserved rather than traversed or removed.

- Focused command: `pytest tests/test_io_path_policy.py
  tests/test_io_workflows.py tests/test_workspace_store.py
  tests/test_io_commands.py tests/test_csv_profiler.py tests/test_agent.py
  tests/test_demo.py -q`
- Result: **114 passed**.

### RC6-S18 closure verification

The focused RC6-S18 change publishes `generation_manifest.json` only after the
other single-entity artifacts, verifies every manifest-recorded SHA-256 before
reporting or validating a completed bundle, and rejects any staged-name
collision unless the caller explicitly approves replacement. Catchable
interruptions continue to restore replaced siblings without following
symlinks.

- Focused command: `pytest tests/test_io_workflows.py tests/test_cli.py
  tests/test_mcp_generator_server.py -q`
- Result: **117 passed**.

### RC6-S19 closure verification

The focused RC6-S19 change routes untrusted human-facing errors, paths,
metadata, assumptions, warnings, and row-count labels through one bounded
escaping helper. CLI JSON errors retain their structured contract while
bounding text before serialization. Audit events already use bounded canonical
JSON; the new regression verifies that control characters cannot create a
physical record or terminal-line boundary.

- Focused command: `pytest tests/test_cli_presenter.py
  tests/test_cli_parser_contract.py tests/test_audit.py
  tests/test_io_commands.py tests/test_cli.py -q`
- Result: **107 passed**.

### RC6-S12 trusted-classifier verification

The focused classifier change keeps the existing required check names and
documentation-only optimization, but no longer executes classifier code from
the pull request tree. CI, Security, and Containers extract the classifier from
the immutable pull-request base SHA (or the accepted push SHA), then use it to
classify the fetched base-to-head diff. Classifier, workflow, dependency,
build, release, and configuration paths remain non-documentation changes and
therefore force all heavy checks.

- Focused command: `pytest tests/test_ci_change_scope.py -q`
- Result: **4 passed**.

### RC6-S12 release-identity verification

The focused release-identity change verifies the annotated tag with Git's SSH
signature support and the committed public signer policy. Release, container,
and PyPI entry points extract the verifier from the externally accepted commit,
require the tag target and checked-out source to equal that exact SHA, and run
the check before any build, attestation, signing, or publication step. Deployed
tag immutability remains open under RC6-S20 and is not claimed by this change.

- Focused command: `pytest tests/test_release_identity.py
  tests/test_release_artifacts.py tests/test_containers.py
  tests/test_ci_change_scope.py -q`
- Result: **37 passed**.
- Full gate: `scripts/check_release.sh` completed with **895 passed**, **3
  skipped** integration tests, and **89.55%** coverage; `mkdocs build --strict`
  also passed.

### RC6-S12 acceptance-manifest verification

The focused acceptance-manifest change uses the already required SSH-signed
annotated tag as the immutable envelope for strict schema-versioned JSON. The
validator requires the exact reviewed commit, complete RC6 finding
dispositions, attributable approval URLs, exact-commit CI/Containers/
Documentation/Security results, and expected wheel/sdist SHA-256 digests.
Release, container, and PyPI workflows load the validator from the accepted
commit before setup or build; release and PyPI also compare the actual
distributions before attestation or publication.

- Focused command: `pytest tests/test_release_acceptance.py
  tests/test_release_identity.py tests/test_release_artifacts.py
  tests/test_containers.py -q`
- Result: **35 passed**.

### RC6-S12 hash-pinned profile disposition

The reported pre-release enforcement gap does not reproduce on exact commit
`40b0410f2efe0d49bdded7dc2bf59d59e1cf48bc`. The published-release workflow
derives the package hash from the single GitHub Release wheel, matches the
public PyPI files to that release, exports hash-locked runtime dependencies
from the reviewed lockfile, and installs the exact package under
`--require-hashes`. Its seven-profile matrix covers base, Parquet, MCP, Trino,
MCP+Trino, OpenAI, and all extras. The upgrade path separately pins the public
`0.12.0` wheel and the verified candidate wheel.

- Focused command: `pytest tests/test_release_artifacts.py -q`
- Result: **22 passed**.
- Disposition: **closed for pre-release implementation**. The seven public
  installs and upgrade remain unchecked in `docs/rc6-acceptance-checklist.md`
  until an explicitly approved RC6 publication provides external URLs and
  digests; no public artifact evidence is claimed here.

### RC6-S20 external release-policy evidence

The following external settings and provenance were read on 2026-08-09 against
exact current-main commit `a82e6fb2f549a057f98b0da70881a8fa1d4f1787`.
They are deployed receipts, not conclusions inferred from workflow source.

- [Main branch ruleset](https://github.com/wa-pis/agent-paranoid-android/rules/19376395)
  `19376395` is active for the default branch with no bypass actors and reports
  `current_user_can_bypass: never`. It requires signed commits, pull requests,
  resolved review threads, a strict up-to-date branch, and these GitHub Actions
  checks: Python 3.11, Python 3.12, Wheel smoke, Trino integration, CodeQL,
  Secret history scan, and Dependency review.
- [Release tag ruleset](https://github.com/wa-pis/agent-paranoid-android/rules/19637531)
  `19637531` is active for `refs/tags/v*.*.*`, has no bypass actors, reports
  `current_user_can_bypass: never`, and blocks deletion, non-fast-forward
  changes, and updates.
- The deployed [`pypi` GitHub environment](https://github.com/wa-pis/agent-paranoid-android/deployments/activity_log?environments_filter=pypi)
  uses custom deployment policies for branch `main` and tag `v*`; the exact
  settings are available from the [environment API](https://api.github.com/repos/wa-pis/agent-paranoid-android/environments/pypi)
  and [deployment-policy API](https://api.github.com/repos/wa-pis/agent-paranoid-android/environments/pypi/deployment-branch-policies).
- Public PyPI provenance for the RC5
  [wheel](https://pypi.org/integrity/agent-paranoid-android/1.0.0rc5/agent_paranoid_android-1.0.0rc5-py3-none-any.whl/provenance)
  and [sdist](https://pypi.org/integrity/agent-paranoid-android/1.0.0rc5/agent_paranoid_android-1.0.0rc5.tar.gz/provenance)
  independently identifies publisher kind `GitHub`, repository
  `wa-pis/agent-paranoid-android`, workflow `publish-pypi.yml`, and environment
  `pypi`. The PyPI SHA-256 digests are
  `f4f04d23b70f9d9d7997f5f4ecfdac1207007f07ff30ec7f1e9155c4be841cbc`
  for the wheel and
  `4001fea17f4d6312cec635152072e731c0b9df2b76a97b9b1ef94a4010309a79`
  for the sdist.

The GitHub environment currently reports `can_admins_bypass: true`; repository
administrators therefore remain in the release trust base, and this evidence
does not claim otherwise. The branch and release-tag rulesets themselves have
no bypass actors. **Disposition: RC6-S20 closed.** RC6 publication still
requires the final exact-commit acceptance manifest and explicit user approval.

## 2026-08-09 Repository-Wide Review Remediation

Repository-wide scan `484dfa30-85d2-4059-b39b-2c52c9d0f5ed` completed on
immutable commit `2c714a6d4df75a1faab422055593fc50a2061a03`. Its exact
`v1.0.0rc5..2c714a6d4df75a1faab422055593fc50a2061a03` diff is bound by
`codex-security-snapshot/v1:sha256:1deb01578cde84b077d74d0845a417ab78dcc7c1d0e401b066dd6fc9c07f3740`.
The scan reported 14 findings: four medium and ten low, with no high or
critical findings.

| Finding | Severity | Disposition |
| --- | --- | --- |
| FS-01: rare source categories can be generated verbatim | Medium | **Closed by the focused FS-01 change**; CSV-folder profiling now replaces source text categories with collision-safe rank labels after local rule inference and before cache, spec, or generation use. Matching conditional predicates are rewritten consistently, legacy caches fail closed, and numeric magnitude semantics are unchanged. |
| AG-01/FS-02: raw constraint literals can cross the advisor boundary | Medium | **Closed by the focused AG-01/FS-02 change**; `equals`, `not_equals`, and `in_values` strings use the same field-scoped replacements in provider-bound profiles and baseline specs, unrepresented strings fail closed, and persisted reviews restore and rebuild the exact request. |
| AG-03: non-string categories bypass advisor sanitization | Medium | **Closed by the focused AG-03 change**; every JSON scalar category and matching constraint literal uses a type-distinct field-scoped label in both request models, persisted review reconstruction is exact, and ordinary numeric bounds are unchanged. |
| MT-01: nested Trino values bypass safe-select masking | Medium | **Closed by the focused MT-01 change**; bounded nested maps, lists, and tuples apply the same string and sensitive-value policy before the opt-in response, while excessive depth or value count fails closed. |

- Focused command: `pytest tests/test_domain_agnostic_pipeline.py -q`
- Result: **18 passed** using synthetic fixtures only.
- Focused command: `pytest tests/test_advisor.py tests/test_constraint_solver.py -q`
- Result: **51 passed** using synthetic fixtures only; generated conditional
  rules remain executable after replacement.
- Focused command: `pytest tests/test_advisor.py -q`
- Result: **43 passed** using synthetic fixtures only; integer, float, boolean,
  and null categories are absent from provider-bound models.
- Focused command: `pytest tests/test_trino_masking.py -q`
- Result: **19 passed** using synthetic fixtures only; no nested string marker
  survives and excessive composite depth is rejected.

The remaining findings retain their canonical scan dispositions and continue
to block RC6 until they are fixed or explicitly accepted in committed evidence.

## Review Conclusion

**Blocked.** Focused implementation and evidence close RC6-S1 through RC6-S4
and RC6-S7 through RC6-S20. Do not tag or promote RC6 until a full
repository-wide review is clean, an independent reviewer approves the exact
fixed commit, and the immutable tag, final gates, and verifiable approval link
are recorded. Public artifact acceptance remains pending until an explicitly
approved publication. The follow-up scan of `5b3ad7f` is a blocking historical
review, not release approval.
