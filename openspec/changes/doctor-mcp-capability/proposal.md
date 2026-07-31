# Change: doctor-mcp-capability

## Why

Importing the MCP SDK does not prove that the installed package can construct
its generator transport and register tools through the current SDK API.

## What Changes

- Construct the real generator `FastMCP` transport locally.
- Register one audited probe tool and verify the public tool listing.
- Redact failures and provide exact MCP-extra reinstall guidance.
- Run the smoke from the isolated MCP wheel profile in CI.

## Impact

`doctor --require-extra mcp` performs an in-process transport check unless
`--skip-smoke` is supplied. It does not start a server or contact a client.
