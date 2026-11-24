# CSV-folder distinct counts

## Requirements

### Requirement: Complete Folder Distinct Counts

A completed CSV-folder profile SHALL count all distinct normalized non-null
values within the existing input and work budgets, without a separate 10,000-value
ceiling. Its `unique_ratio_kind` SHALL be `exact`, with the existing six-decimal
ratio representation.

#### Scenario: A column exceeds the former ceiling

- **GIVEN** a permitted CSV folder has more than 10,000 unique column values
- **WHEN** profiling completes
- **THEN** the full distinct count contributes to uniqueness and identifier-pool
  inference, including duplicates occurring beyond the former ceiling.

### Requirement: Resource And Disclosure Boundaries

Existing input-byte, row, cell, sample and deadline budgets SHALL remain enforced.
Distinct tracking SHALL retain internal fingerprints rather than source values;
those fingerprints SHALL NOT appear in profile artifacts, caches or responses.
Budget exhaustion SHALL fail without publishing partial trusted evidence.

### Requirement: Cache And Legacy Compatibility

Cache format 5 SHALL invalidate older folder caches and recompute their counts.
Existing `lower_bound` profiles SHALL remain readable and SHALL NOT acquire exact
or key-candidate status without reprofiling. Generation-count limits, database
limits and single-file CSV profiling SHALL remain unchanged.
