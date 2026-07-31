# Public Python API Specification

## Purpose

Define compatibility guarantees for the supported names exported from the
top-level `test_data_agent` package.

## Requirements

### Requirement: Top-Level Python Exports Are Stable

The package SHALL maintain a reviewed contract for supported names exported
from `test_data_agent`.

#### Scenario: An export changes

- **GIVEN** the checked-in top-level Python API fixture
- **WHEN** a supported export is added, removed, or renamed
- **THEN** contract verification fails until the compatibility impact is
  reviewed
- **AND** every contracted name resolves from the installed package
