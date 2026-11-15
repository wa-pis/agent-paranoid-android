## ADDED Requirements

### Requirement: Cumulative Parquet admission

The local dataset reader SHALL check each Parquet file against the remaining
shared cell and expanded-byte budgets before decoding rows. Cells already
read from CSV and JSON SHALL count toward the shared cell budget.

#### Scenario: Parquet inputs exceed a shared dataset limit

- **WHEN** metadata for the next Parquet file exceeds the remaining cell or expanded-byte budget
- **THEN** the file SHALL be rejected before its row iterator is decoded
- **AND** prior CSV and JSON cells SHALL count toward the same cell budget
