# Operational Readiness Delta

## Added Requirements

### Requirement: MCP Doctor Capability Smoke

Doctor SHALL verify the required MCP capability by constructing the real local
generator transport and registering a tool through the installed SDK.

#### Scenario: MCP capability is healthy

- **GIVEN** the MCP extra is required and importable
- **WHEN** doctor runs without `--skip-smoke`
- **THEN** it constructs the generator `FastMCP` transport
- **AND** an audited local probe appears in the public tool listing
- **AND** no server, port, client, tool invocation, or external service is used

#### Scenario: MCP capability fails

- **GIVEN** transport construction or tool registration raises an exception
- **WHEN** doctor reports the failure
- **THEN** doctor exits unsuccessfully with exact extra reinstall guidance
- **AND** exception text, audit secrets, and internal details are not exposed
