# Design

Use the shared `apply_dataset_mode_options` guard so bundle, CSV/profile and agent
planning paths agree. A nonzero invalid ratio is incompatible with valid/edge/
load_test. Explain both recoveries: omit the ratio or choose mixed/negative.
Keep an explicit zero ratio compatible. Do not include the caller-supplied mode
string in the message; direct Python callers may supply arbitrary strings.

Keep existing distinctions: load_test multiplies omitted per-entity counts but
explicit --count is exact; formula assign and check have different purposes;
numeric sampling bounds are not automatically row invariants. Show an explicit
field rule/constraint when bounds must hold after a formula. Document that exact
replay needs the same ordered spec, algorithm version and environment, while
identifier domain ordering is a narrower separate guarantee.

Use the complete reference added in #630 instead of duplicating it. Its model
coverage, decimal and embedded/external rules tests already cover several obsolete
claims. Retain fixed safe field context in errors without printing expressions.
