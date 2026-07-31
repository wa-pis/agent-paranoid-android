# Change: dependency-license-gate

## Why

Locked dependencies are audited for vulnerabilities, but their declared
licenses are not checked against an explicit release policy.

## What Changes

- Inspect installed package metadata without adding a scanner dependency.
- Allow only an explicit set of permissive, MPL 2.0, and PSF licenses.
- Fail closed when metadata is unknown, proprietary, or outside the policy.
- Cover application, optional, development, and documentation environments.

## Impact

Dependency metadata changes can now block CI and release checks. Runtime package
contents and public behavior remain unchanged.
