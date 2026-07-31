# Design: artifact-bundle-contract

## Approach

Extend the existing deterministic contract fixture workflow with:

- `artifact-layout.json`, containing sorted relative filenames only;
- `validation-report.json`, validated through `DatasetValidationReport`.

## Failure Modes

- Added, removed, or renamed artifacts change the layout fixture.
- Validation schema drift changes the report fixture or typed validation.
- Dataset contents must never enter these contract fixtures.

## Alternatives

Checksums were rejected because they would couple the contract to generated
row serialization instead of the public artifact interface.
