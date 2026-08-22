# Release Process

Use this process before merging release candidates or creating tags.

## Preflight

1. Review `openspec/project.md` and the affected capability specs.
2. Confirm the change belongs in the MVP or has an OpenSpec proposal under
   `openspec/changes/`.
3. Update README examples, user-facing docs, and `CHANGELOG.md` for visible
   behavior changes. Follow the [changelog policy](changelog-policy.md); do not
   turn release notes into an internal engineering log.
4. Regenerate `schemas/dataset_spec.schema.json` when `DatasetSpec` changes:

```bash
python3 scripts/export_dataset_schema.py
```

## Checks

Run the executable release gate:

```bash
scripts/check_release.sh
```

The gate runs direct Python privacy checks plus direct PostgreSQL and Trino
service-boundary tests before the full coverage suite, so transport-level tests
cannot mask a bypass in the underlying application API.

The script runs linting, strict type checks for the full production package,
compilation, coverage tests, DatasetSpec schema freshness, and the README
quickstart smoke flow. The smoke flow verifies the generated manifest reports
`synthetic: true`, `source_rows_copied: false`, a valid validation report, the
expected seed, and expected row counts.

### Pre-RC Coverage Evidence

The unit, property, and contract suite passed locally on 2026-08-01 against
`origin/main` commit `3862753` with:

```bash
uv run --no-sync pytest \
  --cov=test_data_agent \
  --cov-report=term-missing \
  --cov-fail-under=85
```

Result: 518 passed, 2 live-Trino integration tests skipped, and 87.94% total
coverage. This establishes the configured pre-RC coverage gate; it does not
replace the required rerun against the exact release-candidate commit or the
published artifact checks.

CI and tagged releases also build the wheel and install it in an isolated
environment. That smoke check verifies package version metadata, the PEP 561
`py.typed` marker, console entry points, and `test-data-agent doctor
--skip-smoke` before release attestations are created.

For a candidate containing GigaChat, the release matrix additionally requires
isolated base, `gigachat`, and `all` wheel checks on Python 3.11 through 3.14,
`doctor --require-extra gigachat`, dependency/license verification, and the
fake-SDK provider suite with no credentials or network access. A live provider
call is optional manual evidence and must use only the fictional fixture.

## RC6 To Stable Promotion

The active RC6 baseline is the exact commit named by the annotated
`v1.0.0rc6` tag after the public-package, documentation, container,
attestation, signature, integration, invocation-hardening, and
clean-environment acceptance checks have all passed. RC5 remains historical
release evidence and is superseded for stable promotion. Record the RC6 tag
commit and acceptance evidence before opening the stable release pull request.
The accepted baseline, artifact hashes, public profile checks, and container
digests are recorded in the
[RC6 published release evidence](release-evidence-1.0.0rc6.md).
Stable `v1.0.0` was subsequently published from exact commit
`eb4ef2a5d111ef31390f0a204068369e3f934a3b`; its signed tag, artifact hashes,
image digests, and post-publish checks are recorded in the
[stable published release evidence](release-evidence-1.0.0.md).

The post-1.0 GigaChat adapter changes runtime behavior, dependencies,
packaging, public CLI selection, and an external security boundary. It must be
accepted in a new minor release candidate; it cannot be folded into a
documentation-only `1.0.0` promotion. Version selection, tagging, and
publication remain separate explicit release work. Candidate `v1.1.0rc1` was
published from exact commit `5f95ccfd3774a6d16a4a5c77d1460a8cebf5eca1`;
its signed tag, artifact hashes, image digests, and post-publish checks are
recorded in the
[1.1.0rc1 published release evidence](release-evidence-1.1.0rc1.md).

The subsequent CLI automation and artifact-integrity work changes runtime
behavior, adds the public `completion` command and core success JSON contract,
and extends documented process codes. It therefore requires `1.1.0rc2` before
stable `1.1.0`. The implementation PR may prepare tests, OpenSpec, changelog,
and acceptance steps, but it must not create the tag or publish artifacts.
Exact-commit RC2 acceptance must repeat the core/doctor JSON, malformed-input,
missing-extra entrypoint, Ctrl+C cleanup, suffix/overwrite rollback,
80-column help, four-shell completion, full package, and isolated-wheel gates.
Candidate `v1.1.0rc2` targets accepted commit
`9ff776b8fc59ed8037f7dc5aa23d124a61eb6a90`. Its signed multi-platform
container images were published, but Python publication failed closed before a
GitHub Release or PyPI upload because a macOS-derived sdist digest did not
match the Linux release build. The protected tag remains immutable. Stable
`1.1.0` therefore promotes the same accepted runtime through a version- and
documentation-only diff with Linux-derived artifact digests. Exact outcomes
and published container digests are recorded in the
[1.1.0rc2 partial release evidence](release-evidence-1.1.0rc2.md).

Stable `v1.1.0` was subsequently published from exact commit
`a536629c209878754c4250ef21a47f69e4c01cae`. Its signed tag, independent
exact-commit approval, package hashes, signed image digests, and successful
post-publish checks are recorded in the
[1.1.0 published release evidence](release-evidence-1.1.0.md).

The post-1.1 portable-provenance and security-boundary changes first shipped as
`1.2.0rc1`. Its package and container publication succeeded, but post-publish
acceptance failed because the verifier did not stage the portable bundle at the
path recorded in `SHA256SUMS`. That published candidate remains immutable and
is superseded by `1.2.0rc2`, which contains only the verifier correction and
release identity changes. RC2 completed public acceptance; its immutable
results are recorded in the
[1.2.0rc2 published release evidence](release-evidence-1.2.0rc2.md). Future
candidates must still pass the complete release gate and independent approval
before tagging, then verify the downloaded portable `*.sigstore.json` bundle
against both Python distributions before acceptance.

Stable `1.2.0` promotes that accepted RC2 runtime through the permitted
version- and documentation-only diff. No application runtime, public API,
dependency, workflow, container, or security-boundary change belongs in the
promotion. The signed tag, reviewed promotion, package hashes, signed image
digests, and successful post-publish checks are recorded in the
[1.2.0 published release evidence](release-evidence-1.2.0.md).

The database-source ergonomics implemented after `1.2.0` add credential-free
JDBC-style endpoint syntax, table-qualified column wildcards, and one bounded
aggregate-only SQL query-source workflow. These change runtime behavior,
public CLI/Python contracts, and database security boundaries, so they are
assigned to `1.3.0rc1`. The candidate completed exact-commit review, the
component/JDBC/wildcard/query installed-wheel matrices for PostgreSQL and
Trino, and public artifact verification. Its immutable results are recorded in
the [1.3.0rc1 published release evidence](release-evidence-1.3.0rc1.md).

Stable `1.3.0` promotes that accepted RC1 runtime through the permitted
version- and documentation-only diff. No application runtime, public API,
dependency, workflow, container, or security-boundary change belongs in the
promotion. The signed tag, reviewed promotion, package hashes, signed image
digests, and successful post-publish checks are recorded in the
[1.3.0 published release evidence](release-evidence-1.3.0.md).

Patch candidate `1.3.1rc1` packaged the post-`1.3.0` documentation and package
discovery cleanup together with audited build-tool and pinned workflow-action
maintenance. Its release failed closed before GitHub Release or PyPI
publication because artifact digests generated on macOS differed from the
Ubuntu release build; container publication was canceled before push. The
immutable failed tag is superseded by `1.3.1rc2`, which adds a no-publish Ubuntu
artifact preflight and otherwise retains the same application runtime, public
APIs, dependencies, and security boundaries. RC2 completed exact-commit gates,
independent review, GitHub and PyPI publication, multi-platform signed container
publication, and public-artifact verification. Its immutable results are
recorded in the
[1.3.1rc2 published release evidence](release-evidence-1.3.1rc2.md).

Stable `1.3.1` promotes that accepted RC2 tree through the permitted version-
and documentation-only diff. It introduces no application runtime, public API,
dependency, packaging, workflow, container, or security-boundary change.

Review the stable promotion directly against the accepted candidate:

```bash
git diff --name-status v1.3.1rc2 HEAD
git diff v1.3.1rc2 HEAD
```

A new release candidate is required only when a change affects runtime
behavior, public APIs, dependencies, packaging, security boundaries,
container behavior, or published artifact integrity. Documentation,
changelog, review evidence, checklist reconciliation, release notes, and
version-only promotion changes do not require a new release candidate when the
accepted runtime tree remains unchanged.

The stable promotion diff may contain only these reviewed release changes:

- `pyproject.toml`: the project version and release-status classifiers only;
  dependencies, build settings, entry points, and extras remain unchanged;
- `src/test_data_agent/version.py`: `__version__` only;
- `uv.lock`: the root `agent-paranoid-android` version only, with the resolved
  dependency graph and hashes unchanged;
- `CHANGELOG.md`: add the stable promotion entry, date, and links while
  retaining prerelease history and introducing no new behavior claim;
- release-facing version references, release evidence, roadmap status, and
  OpenSpec completion or archive metadata. These documentation files may
  describe only behavior already accepted in the selected candidate.

Release-validation assertions that only replace a hard-coded candidate
version with the active package version are generated release metadata for
this purpose. They may be normalized during promotion, but no test scenario,
fixture, runtime assertion, safety assertion, or product coverage may change.

File membership alone is not approval: every changed hunk must match one of
those categories. All other changes require a new release candidate. In
particular, any executable production, runtime or safety test, schema, fixture,
dependency, build, workflow, or container change means the candidate is not
the accepted stable source tree. Stop the promotion, make the change in a newly
numbered release candidate, and complete that candidate's acceptance before
trying stable promotion again.

Before any candidate or stable publication, the release workflow must validate
the machine-readable RC acceptance manifest. It must bind the tag to the
reviewed commit digest, require closed release-blocking findings and recorded
approval, and match the published artifact digests. A version-matching tag or
unchecked Markdown checklist is not sufficient evidence.

The manifest is the complete JSON message of the signed annotated tag. Schema
version `1` requires exact `release`, `findings`, `approvals`, `gates`, and
`artifacts` objects. Findings RC6-S1-S4 and RC6-S7-S20 must be `closed` or
explicitly `approved` with HTTPS evidence; every approval and the CI,
Containers, Documentation, and Security gate result must identify the reviewed
commit and an HTTPS evidence URL. `artifacts` contains the exact wheel and
sdist basenames with lowercase SHA-256 digests.

Before recording candidate digests, run the no-publish Ubuntu artifact
preflight for the exact reviewed commit:

```bash
gh workflow run release-preflight.yml \
  --ref main \
  --field commit=<reviewed-main-commit>
gh run download <preflight-run-id> \
  --name release-preflight-<reviewed-main-commit> \
  --dir /tmp/release-preflight
```

The preflight has read-only repository permissions, runs the full release gate,
sets `SOURCE_DATE_EPOCH` from the reviewed commit timestamp, and uploads the
wheel, source distribution, and `ARTIFACT_SHA256` as temporary workflow
artifacts. It cannot create a tag, release, attestation, package, or container.
Copy those Ubuntu-derived digests into the signed acceptance manifest. The
tag-triggered build uses the same runner, checkout depth and tags, Python, uv,
lockfile, release gate, build command, and epoch and fails before attestation or
publication if either digest is different.

Run every final release gate, including `scripts/check_release.sh` and
`mkdocs build --strict`, on the exact stable release commit. Merge only after
the required pipeline is green and conflict-free. Create the stable tag only
from the verified merge commit in `main`; tagging and post-publish checks are
separate explicit steps.

If a `main` push event does not create an expected gate run, dispatch CI,
Containers, Documentation, and Security manually with `--ref main` while the
reviewed commit is still the exact `main` tip. Manual container dispatch runs
validation only; image publication remains restricted to accepted signed
version tags. Record all four exact-commit run URLs in the acceptance manifest.

## Version And Tag

1. Bump `pyproject.toml` and `src/test_data_agent/version.py` together.
2. Review every `Unreleased` entry using the
   [changelog policy](changelog-policy.md), then move the classified categories
   to the new version.
3. Commit the release preparation.
4. Tag the commit after `scripts/check_release.sh` passes.

Merging a release pull request does not publish a package. After the full
security review and independent approval, set the repository variable
`RELEASE_ACCEPTED_COMMIT` to that exact immutable commit. Publication starts
only after a matching tag signed by a key in `.github/release-signers` is
pushed:

```bash
git tag -s vX.Y.Z -F /path/to/acceptance-manifest.json <verified-main-commit>
git push origin vX.Y.Z
```

Release, container, and PyPI workflows fail before building or publishing when
the tag is unsigned, its signer is not allowed, or its target and checked-out
source differ from `RELEASE_ACCEPTED_COMMIT`. They also fail when the signed
manifest is missing, stale, incomplete, or disagrees with the built wheel and
sdist. The tag triggers
`.github/workflows/release.yml`, which creates the GitHub Release and then
dispatches the dedicated PyPI Trusted Publishing workflow. It also triggers
`.github/workflows/containers.yml`, which independently validates and publishes
the three GHCR images.

Keep compatibility changes explicit. Breaking `DatasetSpec`, CLI, artifact, or
Python API changes require a migration guide and a versioned changelog entry.

## Container Publication

Container images are never pushed from pull requests or ordinary branch
builds. A matching version tag publishes separate CLI, generator MCP, and Trino
MCP images for `linux/amd64` and `linux/arm64`.

The workflow attaches BuildKit SBOM and maximal provenance attestations,
creates a GitHub provenance attestation for each manifest digest, and signs the
same digest with keyless Cosign using GitHub OIDC. It does not use a registry
password or signing key. After the first publication, confirm all three GHCR
packages are public and linked to this repository.

For Python distributions, `release.yml` also exports the signed GitHub build
attestation as one `agent-paranoid-android-<version>.sigstore.json` release
asset covering the wheel and source distribution. Before the GitHub Release is
created, both files are verified against that local bundle, the release tag,
and the exact `release.yml` signer identity. The bundle is included in
`SHA256SUMS`; the GitHub attestation API record remains available as a second
verification path.

## Post-Publish Verification

After a GitHub Release, PyPI version, documentation site, and all three GHCR
images are public, run the `Verify Published Release` workflow with the exact
release tag. The workflow checks out the immutable annotated tag and records
its commit, then:

- verifies GitHub Release checksums and tag-bound attestations, including the
  downloaded portable Sigstore bundle without relying on the attestation API;
- compares the public PyPI hashes with the GitHub Release distributions;
- installs the hash-pinned wheel from public PyPI and runs `doctor` plus the
  bundled synthetic demo;
- uses only that installed wheel's synthetic fixture to run agent planning,
  metadata-only review, exact-fingerprint approval, validation, and signed
  audit-log verification;
- confirms the public documentation names the same package version; and
- resolves each GHCR tag to an immutable multi-platform digest, verifies its
  SBOM, GitHub provenance attestation, and keyless Cosign signature, then pulls
  and runs the published image under the hardened health-check settings.

Keep the successful workflow run URL and emitted image digests in the release
evidence. This is a post-publish gate and never creates or mutates a release.

Users can verify either distribution from the downloaded release assets:

```bash
gh attestation verify agent_paranoid_android-<version>-py3-none-any.whl \
  --bundle agent-paranoid-android-<version>.sigstore.json \
  --repo wa-pis/agent-paranoid-android \
  --signer-workflow wa-pis/agent-paranoid-android/.github/workflows/release.yml \
  --source-ref refs/tags/v<version> \
  --deny-self-hosted-runners
```

## PyPI Trusted Publishing

After creating a GitHub Release, `.github/workflows/release.yml` explicitly
invokes `.github/workflows/publish-pypi.yml`. The called workflow downloads the
release wheel and sdist, validates their embedded distribution name and
version, verifies that both were attested by `release.yml` for the selected tag,
and publishes with short-lived GitHub OIDC credentials. The public-index smoke
test installs runtime dependencies from the hash-locked `uv.lock` export and
installs the exact PyPI wheel by its verified SHA-256 digest. The workflow does
not use a PyPI API token and does not build or execute repository code in the
OIDC-enabled publish job.

Configure the pending or project Trusted Publisher with these exact values:

- PyPI project: `agent-paranoid-android`
- GitHub owner: `wa-pis`
- GitHub repository: `agent-paranoid-android`
- Workflow filename: `publish-pypi.yml`
- Environment: `pypi`

The manual dispatch input exists only for recovering a published GitHub
Release that predates the workflow. Duplicate PyPI versions fail loudly;
`skip-existing` is intentionally disabled.

## Public Release Readiness

Before making the repository public or announcing a public release, complete
the [Public Release Checklist](public_release_checklist.md). In particular:

1. Confirm `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, issue templates, pull
   request template, and Dependabot configuration are present.
2. Confirm author and committer emails are public-safe.
3. Run a secret scan over the working tree and reachable Git history.
4. Build and smoke-test the installed wheel:

```bash
uv build --no-build-isolation
uv run --isolated --no-project --with ./dist/*.whl \
  python scripts/check_installed_package.py
uv run --isolated --no-project --with ./dist/*.whl \
  test-data-agent doctor --skip-smoke
```

5. Enable GitHub security settings after publication: secret scanning,
   Dependabot alerts, Dependabot security updates, private vulnerability
   reporting, required CI and dependency-review checks, and active branch/tag
   rulesets.
6. Confirm the `pypi` GitHub environment and matching PyPI Trusted Publisher
   use the exact workflow identity documented above.
