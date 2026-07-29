# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Agent Review Has A Detailed Metadata Checklist

The agent workflow SHALL expose a read-only detailed review report for the
current effective `DatasetSpec` before approval.

#### Scenario: A pending workspace is reviewed

- **GIVEN** a valid awaiting-approval workspace
- **WHEN** detailed review runs
- **THEN** field, entity, relationship, privacy, and fingerprint metadata is
  reported
- **AND** distribution values, source values, and dataset rows are excluded
- **AND** human output is bounded and escapes untrusted names
- **AND** JSON output is versioned and marks generation as not performed
- **AND** a concurrent spec edit fails instead of producing a stale report
- **AND** no workspace file is modified
