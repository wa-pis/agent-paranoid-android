# Change: controlled-negative-scenarios

## Why

Negative generation currently breaks only the first applicable field rule for
each table. Datasets with several business rules therefore exercise one
failure repeatedly instead of providing useful, varied negative fixtures.

## What Changes

- Build a bounded list of supported field and row-rule violations per table.
- Distribute selected invalid rows deterministically across those violations.
- Cover required, allowed-value, numeric-bound, conditional, temporal, and
  formula rules.
- Keep valid and edge generation unchanged.
- Defer cross-table negative cases to a separate increment.

## Safety

Generated invalid values remain synthetic and deterministic. The engine does
not read source rows, accept executable expressions beyond the existing
bounded rule contract, or weaken validation.
