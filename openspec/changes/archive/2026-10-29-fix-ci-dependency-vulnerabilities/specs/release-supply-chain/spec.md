## ADDED Requirements

### Requirement: Audit Tool Dependency Security Maintenance

The reviewed lock SHALL select MessagePack1.2.3 or newer for audit-tool caching,
with distribution hashes. Security maintenance SHALL retain hash-checked audit
and license gates without adding audit-tool dependencies to runtime images.

#### Scenario: Audit dependency has a published correction

- **GIVEN** CI flags the locked MessagePack inventory
- **WHEN** the corrected lock is validated
- **THEN** the hash-checked dependency audit and license checks pass
- **AND** ordinary CLI/Python/MCP contracts remain unchanged
