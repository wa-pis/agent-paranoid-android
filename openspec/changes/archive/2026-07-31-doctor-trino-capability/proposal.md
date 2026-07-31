# Change: doctor-trino-capability

## Why

Importing the Trino client and SQL parser does not prove that an installed
wheel can validate the project's safe query shape or construct a client with
the supported API.

## What Changes

- Validate one bounded, allowlisted, non-sensitive Trino query locally.
- Construct and close a DBAPI client without opening a cursor or executing SQL.
- Redact failures and provide exact Trino-extra reinstall guidance.
- Run the smoke from the isolated Trino wheel profile in CI.

## Impact

`doctor --require-extra trino` performs an in-process parser and client check
unless `--skip-smoke` is supplied. It does not read credentials or contact a
Trino coordinator.
