# Change: versioned-contract-catalog

## Why

Golden fixtures detect changes but do not currently state which contract
version or compatibility rule applies to each fixture.

## What Changes

- Add a versioned catalog for every public JSON and MCP fixture.
- Classify contracts as additive-only or schema-versioned.
- Fail tests when a fixture is unregistered or the catalog is stale.

## Impact

Runtime behavior and public payloads are unchanged.
