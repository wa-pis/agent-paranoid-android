# Gate Evidence: application-boundaries-refactor

Date: 2026-08-01

Verified source commit:
`f0b85165ea5d8821ed4ede017f3b6de6038659b8` (merge of PR #223).
No version, tag, release, or publication action was performed.

## Local Gates

- `uv run --no-sync scripts/check_release.sh`: passed lint, mypy for 97
  source files, compile, 97 dependency-license checks, dependency
  compatibility, 18 direct privacy/SQL tests, schema freshness, operational
  budgets, and quickstart smoke.
- Full suite: 669 passed, 3 skipped, 88.79% coverage (85% required).
- `uv build`: built the wheel and source distribution from the verified
  commit.
- Installed base-wheel verification and bundled demo: passed.
- `twine check`: passed for both distributions.
- `mkdocs build --strict`: passed.
- `pip-audit` against the frozen all-extras `uv.lock` export: no known
  vulnerabilities found.
- `openspec validate application-boundaries-refactor --strict`: passed.

Local artifact SHA-256 values:

- wheel: `8d5a0c4b0dff05ad702e3f6609ac5bc00abb04407fdd49ac66b309f05b15371c`
- source distribution:
  `f992c493a51d9f399b0017a2cfaa57e9132adc22b15e60818e4a9dd622121adb`

## Exact-Commit GitHub Gates

All applicable jobs for the verified commit passed:

- [CI run 30715128014](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30715128014):
  Python 3.11-3.14, wheel smoke/compatibility, minimum dependency profiles,
  and Trino integration.
- [Documentation run 30715127993](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30715127993):
  build and deployment checks.
- [Container run 30715127987](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30715127987):
  CLI, generator MCP, and Trino MCP validation on amd64 and arm64; publication
  jobs were correctly skipped for an untagged push.
- [Security run 30715127980](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30715127980):
  CodeQL and full-history secret scanning passed; pull-request-only dependency
  review was correctly skipped on the `main` push.
- [OpenSSF Scorecard run 30715128009](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30715128009):
  passed.
