# Design

Input adapters produce safe DatasetProfile evidence. The reviewed DatasetSpec
is the complete source-independent execution contract; missing source statistics
require explicit review rather than invented observations. Format adapters encode
logical values and must preserve typed/null semantics for repeat validation.
Business rules are applied once in generation and checked without mutation after
reload. SQL artifact reading is a bounded data-only parser for generated INSERT
statements; it never connects to a database or executes SQL.

CSV needs an explicit reversible null/text convention bound in its manifest,
with legacy unmarked CSV behavior preserved. All typed rule operands normalize
through field metadata, not inferred value spelling. Parquet keeps exact native
types for representable fields. Wide INTEGER cells use marked decimal text;
heterogeneous timestamp offsets and malformed negative columns use marked JSON
scalar text. Fixed field metadata declares each codec and the bounded reader
restores logical cells. This is an explicit physical encoding, not a claim that
malformed values satisfy the reviewed field type. Valid generation remains
strict. Single-file bundles record entity/filename mappings in the manifest.
Controlled-negative cases require portable logical violations and explicit
evidence; a physical encoding failure is not successful negative generation.

The executable matrix must distinguish source acquisition tests, complete reviewed
specification tests, output round trips and transport checks. A green matrix must
not be inferred by merely changing a source_type string on an untested profile.
