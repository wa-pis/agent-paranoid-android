# Change: cross-table-negative-cases

## Why

Controlled negative generation covers field and row rules but leaves
foreign-key and aggregate-formula rules untouched. Negative datasets therefore
cannot exercise important multi-table validation paths.

## What Changes

- Add foreign-key and concrete-field aggregate-formula rules to the bounded
  deterministic invalid-case rotation.
- Generate missing parent keys without changing parent rows.
- Perturb only the configured aggregate field while preserving unrelated row
  values.
- Keep count-style `field: "*"` aggregate rules validation-only because a row
  count mutation would also violate the dataset shape.

## Safety

All injected values are synthetic and derived from already generated rows.
The change does not read source rows, expose PII, or expand database access.
