# Synthetic Generation Specification Delta

## MODIFIED Requirements

### Requirement: Reviewable DatasetSpec Contract

Generation and validation SHALL use `DatasetSpec` as the only public
generation specification contract.

#### Scenario: DatasetSpec drives generation

- **GIVEN** a reviewed YAML or JSON `DatasetSpec`
- **WHEN** generation runs
- **THEN** the dataset-oriented generator enforces its privacy, resource, and
  validation settings
- **AND** the effective specification artifact is named `dataset_spec.yaml` or
  `dataset_spec.json`

#### Scenario: Removed specification shape is supplied

- **GIVEN** an input file using the removed top-level `table` or `tables` shape
- **WHEN** generation or validation is requested
- **THEN** the command fails before processing rows
- **AND** the error points to the `0.6.0` migration guide

#### Scenario: Older profile metadata is supplied

- **GIVEN** safe profile metadata with top-level `columns`
- **WHEN** it is used with `--profile` or `infer-spec`
- **THEN** it is normalized into `DatasetProfile`
- **AND** generation proceeds through `DatasetSpec`
