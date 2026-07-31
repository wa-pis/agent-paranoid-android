# Design: mcp-schema-contract

## Approach

Use FastMCP's public `list_tools()` API and retain only stable client-facing
fields: name, description, input schema, and output schema. Sort tools by name
before writing fixtures.

Create the Trino server with safe SELECT explicitly disabled so fixture
generation is independent of the caller environment.

## Failure Modes

- Tool additions, removals, or renames change the fixture.
- Parameter or return annotation drift changes JSON Schema.
- Enabling raw SQL on the default Trino surface fails the explicit assertion.

## Alternatives

FastMCP internal tool-manager state was rejected because it is not a public SDK
contract.
