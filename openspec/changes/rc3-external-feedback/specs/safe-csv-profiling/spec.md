## ADDED Requirements

### Requirement: RC3 feedback contract
The CLI SHALL expose profile-parquet for bounded safe metadata profiling and subsequent infer-spec. Source rows SHALL not be retained.

#### Scenario: Deterministic enforcement
- **WHEN** the corresponding CLI or direct service is invoked
- **THEN** the contract is enforced before publication and tested with fictional inputs
