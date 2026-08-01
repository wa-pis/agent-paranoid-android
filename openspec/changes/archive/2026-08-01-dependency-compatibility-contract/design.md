# Design: dependency-compatibility-contract

## Approach

Create a small compatibility matrix with minimum and latest tested profiles for
the base package and each optional integration. Keep the lockfile and CI
profiles authoritative for evidence, while package metadata expresses only the
range the project is prepared to support.

Capture normalized dependency versions in the existing reproducibility
evidence. Keep the generator algorithm, spec digest, rules digest, locale,
Python identity, serializer, and output fingerprints alongside dependency
versions so differences can be diagnosed rather than hidden.

## Data And Contracts

- Compatibility policy document: tested minimum, latest tested, support status,
  and behavior-change notes for each relevant dependency.
- CI: isolated minimum and latest-compatible profiles for base, Parquet, Trino,
  and other supported optional extras.
- Manifest: additive fields or a normalized dependency map containing at least
  generator version, Python version, Faker, Pydantic, PyYAML, PyArrow when used,
  sqlglot when used, Trino client when used, locale, seed, spec digest, and
  rules digest.
- Release checks: verify the declared policy matches the tested profiles and
  reject unreviewed major drift.

## Failure Modes

- A missing or unrecordable dependency identity fails manifest generation or
  the relevant release gate.
- A minimum/latest profile fails the same contract tests before its version is
  declared supported.
- A dependency upgrade changes logical output or validation semantics; the
  compatibility matrix records the change and requires a package release or
  explicit support decision.

## Alternatives

### Add broad upper bounds immediately

Rejected. Bounds without tested evidence hide rather than solve compatibility
uncertainty.

### Promise cross-version reproducibility

Rejected. The project should promise only guarantees proven by the matrix and
recorded artifacts.

### Record only the package version

Rejected. It is insufficient to explain changes caused by runtime or optional
dependency versions.
