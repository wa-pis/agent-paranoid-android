# Manual Release Runbook

This is the copy-and-paste path for publishing a release without an AI
assistant. It uses the repository's existing checks and GitHub workflows. AI
review is not required, but the release still requires an independent human
approval recorded at an HTTPS URL and bound to the exact release commit.

Do not move, replace, or delete a tag after it has been pushed. If a published
tag fails, fix the problem in a new version or release candidate.

Create a new release candidate when runtime behavior, public APIs,
dependencies, packaging, security boundaries, containers, or published
artifact integrity change. A stable promotion from an accepted candidate may
contain only the version, changelog, documentation, acceptance evidence, and
generated release metadata allowed by [the release policy](release.md).

## 1. Prerequisites

Run these commands from a clean checkout:

```bash
export VERSION="X.Y.Z"
export TAG="v${VERSION}"
export PREVIOUS_TAG="vPREVIOUS_VERSION"

gh auth status
git config --get gpg.format
git config --get user.signingkey
git fetch origin main --tags
git switch main
git pull --ff-only origin main
git status --short
```

`gpg.format` must be `ssh`. The configured signing key must match an entry in
`.github/release-signers`. Stop if the worktree is not clean or if the version
already exists on GitHub or PyPI.

```bash
git ls-remote --tags origin "refs/tags/${TAG}"
python3 -m pip index versions agent-paranoid-android
```

The first command must print nothing for the new tag.

## 2. Prepare The Release Pull Request

Create a focused branch:

```bash
git switch -c "codex/release-${VERSION}"
```

Update the version and release-facing documentation. At minimum, inspect:

- `pyproject.toml`;
- `src/test_data_agent/version.py`;
- the root package version in `uv.lock`;
- `CHANGELOG.md`;
- README and release-facing documentation;
- hard-coded stable-version assertions in `tests/test_documentation.py`.

Regenerate and check the lockfile, then run the complete local gates:

```bash
uv lock
uv lock --check
scripts/check_release.sh
uv run mkdocs build --strict
```

Review the exact changes, stage only the intended files, and create a signed
conventional commit:

```bash
git status --short
git diff
git add -p
git diff --cached
git commit -S -m "chore(release): prepare ${VERSION}"
git push -u origin "codex/release-${VERSION}"
gh pr create --base main --head "codex/release-${VERSION}" --title "chore(release): prepare ${VERSION}" --body "Prepare ${VERSION}; no tag or publication is performed by this PR."
```

Add any intended untracked file by its exact path before committing. Do not use
`git add .`.

Wait for all required checks and the independent human review. Merge only when
the PR is clean, mergeable, approved, and green:

```bash
gh pr checks --watch
```

## 3. Pin The Exact Main Commit

After the PR is merged:

```bash
git switch main
git pull --ff-only origin main
export COMMIT="$(git rev-parse HEAD)"
test -z "$(git status --porcelain)"
printf '%s\n' "${COMMIT}"
gh run list --commit "${COMMIT}" --limit 20
```

Record successful exact-commit URLs for these four gates:

- CI;
- Containers;
- Documentation;
- Security.

Set them as shell variables for later use:

```bash
export CI_URL="https://github.com/wa-pis/agent-paranoid-android/actions/runs/REPLACE_ME"
export CONTAINERS_URL="https://github.com/wa-pis/agent-paranoid-android/actions/runs/REPLACE_ME"
export DOCS_URL="https://github.com/wa-pis/agent-paranoid-android/actions/runs/REPLACE_ME"
export SECURITY_URL="https://github.com/wa-pis/agent-paranoid-android/actions/runs/REPLACE_ME"
```

The independent reviewer must review this exact commit, state that no
release-blocking defect remains, and record the conclusion in a GitHub issue,
PR comment, or other stable HTTPS location. Save that URL:

```bash
export APPROVAL_URL="https://github.com/wa-pis/agent-paranoid-android/issues/REPLACE_ME"
```

## 4. Build Reproducible Ubuntu Artifacts

Run the no-publish preflight against the exact commit:

```bash
gh workflow run release-preflight.yml --ref main --field "commit=${COMMIT}"
gh run list --workflow release-preflight.yml --commit "${COMMIT}" --limit 5
export PREFLIGHT_RUN="REPLACE_WITH_RUN_ID"
gh run watch "${PREFLIGHT_RUN}" --exit-status
export PREFLIGHT_DIR="$(mktemp -d)"
gh run download "${PREFLIGHT_RUN}" --name "release-preflight-${COMMIT}" --dir "${PREFLIGHT_DIR}"
cat "${PREFLIGHT_DIR}/ARTIFACT_SHA256"
shasum -a 256 "${PREFLIGHT_DIR}"/*.whl "${PREFLIGHT_DIR}"/*.tar.gz
```

The two locally calculated hashes must match `ARTIFACT_SHA256`.

## 5. Prepare The Acceptance Manifest

Start from the previous signed manifest and edit a temporary copy:

```bash
export MANIFEST="$(mktemp "${TMPDIR:-/tmp}/${TAG#v}-acceptance.XXXXXX")"
git cat-file tag "${PREVIOUS_TAG}" | awk '/^{/{copy=1} /^-----BEGIN SSH SIGNATURE-----/{copy=0} copy' > "${MANIFEST}"
${EDITOR:-vi} "${MANIFEST}"
python3 -m json.tool "${MANIFEST}"
```

Keep the schema intact and update every release-specific field:

- `release.tag` to `${TAG}`;
- `release.reviewed_commit` to `${COMMIT}`;
- each approval's reviewer, `reviewed_commit`, and URL;
- every gate's commit and exact successful run URL;
- wheel and sdist basenames and SHA-256 values from the Ubuntu preflight;
- finding evidence only when its disposition or evidence changed.

The manifest must contain exactly the keys accepted by
`scripts/check_release_acceptance.py`. Do not put prose before or after the
JSON.

## 6. Create And Verify The Local Tag

Confirm the remote tag is still absent, then create a signed annotated tag:

```bash
test -z "$(git ls-remote --tags origin "refs/tags/${TAG}")"
git tag -s "${TAG}" -F "${MANIFEST}" "${COMMIT}"
python3 scripts/check_release_tag.py "${TAG}"
python3 scripts/check_release_identity.py "${TAG}" "${COMMIT}" .github/release-signers
python3 scripts/check_release_acceptance.py "${TAG}" "${COMMIT}" "${PREFLIGHT_DIR}"
git -c gpg.ssh.allowedSignersFile=.github/release-signers verify-tag "${TAG}"
```

If a check fails and the tag has not been pushed, delete only the local tag,
fix the manifest, and repeat this section:

```bash
git tag -d "${TAG}"
```

Never run that command after the tag exists on the remote.

## 7. Authorize And Publish

Bind publication to the exact accepted commit and read the value back:

```bash
gh variable set RELEASE_ACCEPTED_COMMIT --body "${COMMIT}"
test "$(gh variable get RELEASE_ACCEPTED_COMMIT)" = "${COMMIT}"
git push origin "${TAG}"
```

The tag starts the GitHub Release and Containers workflows. The Release
workflow dispatches PyPI Trusted Publishing after the GitHub assets are
created. Find the run IDs and wait for all three workflows:

```bash
gh run list --commit "${COMMIT}" --limit 20
gh run watch REPLACE_WITH_RELEASE_RUN_ID --exit-status
gh run watch REPLACE_WITH_CONTAINERS_RUN_ID --exit-status
gh run watch REPLACE_WITH_PYPI_RUN_ID --exit-status
```

Confirm that the GitHub Release is stable and that PyPI is public:

```bash
gh release view "${TAG}" --json tagName,url,isDraft,isPrerelease,publishedAt,assets
python3 -m pip index versions agent-paranoid-android
```

## 8. Verify The Public Release

Run the repository's read-only post-publish verifier:

```bash
gh workflow run verify-published-release.yml --ref main --field "tag=${TAG}"
gh run list --workflow verify-published-release.yml --limit 5
gh run watch REPLACE_WITH_VERIFY_RUN_ID --exit-status
```

Optionally repeat a small clean-install smoke locally:

```bash
export SMOKE_DIR="$(mktemp -d)"
python3 -m venv "${SMOKE_DIR}/venv"
"${SMOKE_DIR}/venv/bin/python" -m pip install --no-cache-dir "agent-paranoid-android[postgres]==${VERSION}"
"${SMOKE_DIR}/venv/bin/test-data-agent" --version
"${SMOKE_DIR}/venv/bin/test-data-agent" doctor
"${SMOKE_DIR}/venv/bin/test-data-agent" demo --output "${SMOKE_DIR}/demo"
```

Record the final workflow URLs, wheel and sdist hashes, and immutable GHCR
digests in the release evidence issue or release evidence document.

## Recovery Rules

- A pushed tag is immutable. Never move, replace, or delete it.
- If a tag-triggered build fails before publication, fix the defect in a new
  version or release candidate.
- If the GitHub Release exists but PyPI dispatch failed before uploading, rerun
  the existing artifacts with:

  ```bash
  gh workflow run publish-pypi.yml --ref main --field "tag=${TAG}"
  ```

- If public verification fails, do not rebuild or mutate published artifacts.
  Investigate the evidence and release a new version when code or artifacts
  must change.
- Do not use `--admin`, bypass required checks, or publish with a local PyPI
  token. This repository publishes through GitHub OIDC Trusted Publishing.
