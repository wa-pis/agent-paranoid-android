# Tasks: dependency-compatibility-contract

- [x] Inventory runtime and optional dependencies that affect parsing,
  generation, serialization, SQL policy, or validation.
- [x] Define minimum supported and latest tested profiles for each supported
  Python/extra combination.
- [x] Add CI jobs or matrix profiles for the minimum and latest compatible
  dependency sets.
- [x] Add contract tests for deterministic generation, validation, YAML/JSON
  parsing, Parquet, SQL policy, and Trino client construction where applicable.
- [x] Add normalized dependency evidence to the generation manifest without
  exposing rows, PII, secrets, or provider payloads.
- [x] Document same-environment, same-version, and cross-version guarantees.
- [x] Add upper major bounds only where the compatibility evidence justifies
  them, with release notes for any narrowed range.
- [ ] Add release checks for manifest completeness and unreviewed dependency
  drift.
- [ ] Run the full supported-version, package, security, and documentation
  gates.
