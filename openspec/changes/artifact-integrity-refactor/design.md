# Design

Hash bytes incrementally while the bounded CSV reader feeds the parser.
Verification uses the same existing digest framing. Agent planning bypasses
cache reads for this operation and may still publish its fresh metadata cache.

The checkpoint records the manifest digest, which in turn binds the dataset,
spec and validation artifacts. The manifest is written before the checkpoint
in both generation engines. The checkpoint is trusted workspace metadata.
Recovery also revalidates the rows using the applicable legacy or streaming
validator. SQL recovery uses the existing bounded INSERT reader.

Parquet admission charges per-file metadata estimates against the remaining
dataset budget before opening the row iterator. Existing decoded-batch checks
also apply.
