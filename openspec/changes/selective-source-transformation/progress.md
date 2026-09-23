# Implementation Progress

## Authority And Target

- User authorized implementation, signed commits/push, sequential PR merges
  after CI/CD and independent review, and 1.6.0rc1 publication. No stable release.
- GitHub CLI checked: authenticated; repository ADMIN access. Homebrew git
  required because system git invokes unaccepted Xcode license.
- Branch: codex/1-6-identifier-domains, based on main 4d6310a.
- Heartbeat automation active every five minutes; no duplicate/overlapping work.
- Use Caveman and Ponytail. Read this file first; do not rerun unchanged gates.

## Current Slice: Client Finding 19

- Added deterministic directory access-time regression tests. Baseline: 2 fail,
  9 pass. Shared publish_directory/replace_path compared complete stat objects.
- Fix compares directory identity; regular files retain identity, ctime_ns and
  size checks. Absent/present transitions remain checked. No overwrite expansion.
- Focused tests: 90 passed across path policy, I/O workflows/commands, workspace.
- Ruff passed; full production mypy passed (109 files).
- Path-swap tests cover source/destination directory and symlink replacements.
- Signed commits ed4a672 (plan) and 2569c3a (fix) pushed; PR #516 opened:
  https://github.com/wa-pis/agent-paranoid-android/pull/516
- PR #516 merged as 4d6310ad3ccae5abad8dec39e59dc2b17e52791d after green
  CI, Security, Containers, Documentation and independent AI review.
- Documentation inventory initially rejected the new active proposal; updated
  its explicit inventory and checks for the unfinished transformation plan.
- Documentation tests: 49 passed; Ruff and strict OpenSpec validation passed.
- 2026-09-24 heartbeat: current PR head c3f1308; documentation CI passed.
  CI/Security/Containers queued behind earlier runs; do not restart or push
  progress-only commits while those checks are pending.
- User explicitly authorized separate AI-reviewer subagents for PRs and final
  RC/release SHA reviews; automation updated. Stable remains unauthorized.
- Independent read-only reviewer Nietzsche (01a0cff7-6e28-7c72-8bb0-4a54f99bebfe)
  completed PR #516 exact c3f130896c0485b95c792dc8936affa5d0836d8e against
  d89dc4dd573c4e764cddd8eb1e053eb78aa42acb: no blocking findings; 71 checks
  passed. AI review, not human approval. Evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/516#issuecomment-5802473268
- Next defect confirmed on unpatched generator with fictional data: two distinct
  identifier fields produce equal row-wise values for both integer and string
  types (three rows, seed 7). synthetic_identifier ignores field identity;
  integer identifiers also ignore entity identity. No generator change yet.
- Repro explicitly uses PYTHONPATH=src (entity items). An initial standalone
  probe resolved the installed package instead and failed privacy validation
  for the longer fictional_items entity name; that run is not candidate proof.
  Pytest already sets pythonpath=[src, .], so prior pytest results are unaffected.

## Remaining Decisions And Work

### Local Publication Replay (2026-09-24)

- PR #516 c3f1308: CI Python 3.11–3.14, wheel checks, Security and container
  validation passed; independent review still pending. No merge performed.
- Built candidate wheel from c3f1308 using uv build --wheel --no-build-isolation;
  version intentionally remains 1.5.0 until release preparation. Installed with
  --no-deps into /private/tmp/apa-client-acceptance.xrueHB/candidate, reusing the
  development interpreter dependencies. This is not a clean dependency acceptance.
- Verified import resolves to that installed candidate path via PYTHONPATH.
- Reviewed original probe_output_contract.py before extracting it into isolated
  replay/baseline-replay directories below the same temporary root. No product
  monkeypatches. Replaced missing spec with identical fictional deal/id/amount
  fixtures, ten rows. Original script itself unchanged.
- Original probe: installed comparison package and candidate each ran 40 fresh CLI
  processes. Both: absent/empty/empty-overwrite 8 successes each; filled and
  filled-overwrite 8 exit-2 rejections each. Timing-dependent defect did not
  reproduce in this nondeterministic replay; deterministic unit regression is
  the before/after evidence, not these identical original-probe results.
- Metadata verification found the pre-existing installed package is 1.4.0,
  NOT 1.5.0. The script's hard-coded 1.5.0 banner is misleading. Therefore the
  comparison run is diagnostic only; required affected-baseline 1.5.0 replay
  remains pending in a separately installed target. Do not call it accepted.
- Candidate wheel SHA256: 77a15df3854f2f18b1917f21169fd8d65d10ad34037774754513cf849b1f96a3.
  Original probe SHA256: 33dafc8ac55f4e0cb230e399aa206da2bc2fd2fbe2c22270cb37171208399f71.
- Supplementary candidate checks explicitly asserted exit code, CSV shape and
  ten rows for successes; rejections preserve old.csv and create no deal.csv.
  All five cases passed, subprocess timeout 30 seconds. The original probe's
  artifact-only success accounting remains insufficient on its own.
- No private client data tested. Full installed-candidate acceptance pending.

- Transformation runtime not implemented. Safety-policy exception must be scoped
  explicitly and independently reviewed with tests; existing generation stays
  source-free. Do not silently allow sensitive preservation.
- Client script replay and all other findings: see client-acceptance.md; not
  yet completed. Missing private inputs are unverified, never passed.
- Profile/inline YAML/CSV mapping, wizard, agent parity, Decimal and source
  adapters remain pending. Latest voice decisions recorded in plan/tasks/design.
- Shared mapping required within a linked dataset; independent runs may differ.
  Explicit shared mapping across separate runs is opt-in, not a universal mandate.
- External script/API substitution is unapproved future TODO. Future integration
  feedback has not arrived; do not invent it.
- Finish full documentation reconciliation and installed candidate/client tests,
  independent exact-SHA review, release gates and public acceptance before closing.

## Next Action

Identifier-domain fix now local, not committed: sorted entity/field domains,
disjoint integer residue classes, synthetic-prefixed string encoding. No new
dependency or privacy bypass. Two baseline regression failures reproduced;
127 focused tests now pass (domains, generation contracts, pipeline, dataset
spec, safety), including negative/zero/positive seeds, reordered fields/entities
and declared FKs. Mypy passed for the changed generator. Changelog and relational
contract document fixture compatibility and lack of cross-spec mapping stability.

Next: independent review of a signed identifier-domain commit, focused docs/lint
checks and PR. Complete installed 1.5.0 baseline replay separately. Broader
transformation remains unfinished.
