# Dataset validation consistency

## Requirements

- Equivalent declared boolean/integer values in memory, JSON and CSV MUST yield
  the same conditional validation result without modifying caller data.
- String fields MUST retain string identity, including leading zeroes.
- Composite scalar-field inputs and malformed rows MUST fail enabled validation
  sections without leaking their contents or raising an unhandled exception.
- Integer formulas, comparisons and sum/count aggregates MUST preserve integers
  above 2**53. Explicit numeric tolerance MUST retain its meaning.
- Formula and aggregate dependencies MUST execute in dependency order, independent
  of their declaration order. Cycles and conflicting writers MUST fail before
  output publication. Rejected constraints MUST NOT participate.
- Conditional/temporal repairs MUST run after their calculated inputs and before
  calculations consuming repaired fields. Multiple repairs retain their existing
  temporal-then-conditional priority and declaration order within each kind.
  Static repair cycles MUST also fail, including potentially convergent cycles;
  the implementation does not search for a fixed point.
- Optional report settings MUST NOT disable generation privacy/type/invariant
  enforcement or alter controlled negative-generation semantics.
