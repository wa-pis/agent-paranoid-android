# Design

Prepare a non-mutating schema-directed view at the combined validation boundary.
Convert only declared boolean, integer and float strings. Preserve string fields
and the existing empty/null convention. Reject unsafe shapes before downstream
set, aggregate and privacy operations, including when schema reporting is off.

Keep shared arithmetic in rules/expressions.py. Compare integers before float
conversion; preserve explicit tolerance and integer sum/count. Retain floating
point semantics for float fields and averages.

Extend the existing TopologicalSorter-based ordering to formula/aggregate writers
and their field inputs. Conditional and temporal repairs participate so a repaired
field is ready before its aggregate/formula consumers. When a field has a calculation
and repairs, apply the calculation first, then temporal and conditional repairs;
multiple repairs of one kind retain declaration order. This is a single acyclic
pass, not an iterative solver. Preserve rejected-constraint handling and final
invariant validation. Reject conflicting calculations and cycles before publication.
