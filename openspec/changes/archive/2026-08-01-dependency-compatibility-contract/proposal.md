# Change Proposal: dependency-compatibility-contract

## Summary

Define and test the dependency compatibility policy for libraries that can
change parsing, generated values, serialization, or validation semantics. The
policy must distinguish minimum supported versions, latest tested versions,
and versions that are intentionally unsupported.

Record the dependency identities that affect a generated artifact so a user
can understand reproducibility without being promised cross-version byte
identity that has not been verified.

## Motivation

The package currently has mostly lower bounds while behavior depends on Faker,
Pydantic, YAML parsing, Parquet, SQL parsing, and the Trino client. A dependency
upgrade can change generated values or validation behavior without a source
change. The release contract needs evidence before adding upper bounds or
claiming compatibility.

## Scope

In scope:

- Inventory Faker, Pydantic, PyYAML, PyArrow, sqlglot, and Trino client support.
- Test minimum supported and latest compatible dependency profiles in CI.
- Define when a major upper bound is justified by evidence.
- Record relevant package versions and fingerprints in generation manifests.
- Document same-environment, same-version, and cross-version guarantees.
- Add release checks that detect unsupported or untested dependency drift.

Out of scope:

- Arbitrary exact pins or upper bounds added without compatibility evidence.
- A promise of cross-version byte-for-byte reproducibility.
- Changing generation semantics solely to accommodate one dependency release.
- Adding optional dependencies to the base installation.

## Safety Impact

- Dependency identities become part of reproducibility and validation evidence.
- Unsafe parser behavior or changed SQL policy must fail the relevant tests
  before release.
- Manifest additions remain metadata-only and must not contain source rows,
  raw PII, credentials, or provider payloads.

## Compatibility

- Existing manifest readers must accept additive dependency evidence.
- A narrowed supported version range requires a migration or release note.
- Existing CLI, Python, MCP, output, and safety contracts remain unchanged
  unless a dependency incompatibility is explicitly documented and versioned.
