## ADDED Requirements

### Requirement: Cumulative Parquet admission

#### Scenario: Parquet inputs exceed a shared dataset limit

- **WHEN** metadata for the next Parquet file exceeds the remaining cell or expanded-byte budget
- **THEN** the file SHALL be rejected before its row iterator is decoded
- **AND** prior CSV and JSON cells SHALL count toward the same cell budget
