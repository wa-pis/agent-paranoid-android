## ADDED Requirements

### Requirement: RC3 feedback contract
Dataset generation SHALL reject unimplemented edge/load_test modes before publication. DatasetSpec folder generation SHALL reject overwrite explicitly; negative/mixed publication SHALL remain labelled by validation status.

#### Scenario: Deterministic enforcement
- **WHEN** the corresponding CLI or direct service is invoked
- **THEN** the contract is enforced before publication and tested with fictional inputs
