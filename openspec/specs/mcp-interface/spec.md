# MCP Interface Specification

## Purpose

Define compatibility and safety guarantees for generator and Trino MCP tool
discovery surfaces.

## Requirements

### Requirement: MCP Discovery Schemas Are Stable

Generator and Trino MCP servers SHALL maintain reviewed contracts for default
tool names and input/output schemas.

#### Scenario: A tool schema changes

- **GIVEN** checked-in MCP discovery fixtures
- **WHEN** a tool name, input schema, or output schema changes
- **THEN** contract verification fails until compatibility is reviewed
- **AND** unrestricted raw SQL remains absent from the default Trino tools

### Requirement: MCP Permission Documentation Matches Runtime Authority

Public MCP documentation SHALL inventory every console-registered tool and
describe its local reads, writes, database/network access, disclosure and review
requirements. It SHALL distinguish client call/confirmation policy, operating
system grants, administrator application configuration, database grants and
human workflow approval. This documentation clarifies existing authority; it
SHALL NOT grant new access or activate gated transformation extensions.

#### Scenario: An operator connects a local client

- **GIVEN** an installed generator or Trino console server
- **WHEN** the operator follows the connection and permission references
- **THEN** stdio startup requires no inbound MCP port or invented OAuth scopes
- **AND** the tool inventory distinguishes base, runtime-owned and opt-in tools
- **AND** filesystem rights include separate audit/authentication and owned
  temporary-storage locations where applicable

#### Scenario: An operator restricts database profiling

- **GIVEN** a restricted database identity and application allowlists
- **WHEN** the operator selects Trino tools
- **THEN** documentation explains that database grants are independently required
- **AND** column selectors are not described as a universal per-tool ACL
- **AND** optional row-returning work is separated from aggregate-only profiling

#### Scenario: A client enables a writing tool

- **GIVEN** synthetic generation and transformation tool permission tables
- **WHEN** the client operator chooses an allow/confirm policy
- **THEN** direct generation is distinguished from the review-first plan workflow
- **AND** calling synthetic approval still requires actual human spec review
- **AND** preservation requires a separate matching local controlling-terminal
  receipt that MCP cannot issue
