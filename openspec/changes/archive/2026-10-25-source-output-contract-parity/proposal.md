# Source/output contract parity

## Why
The owner clarified that portability is a complete source × output contract,
not a business-rule feature attached to particular commands. Every supported
source must reach every supported output through one reviewed DatasetSpec.
Field types, distributions, generation/validation/privacy options, relationships
and business rules must retain their meaning across that matrix.

## What changes
- Publish and execute the full matrix for CSV, CSV folders, Parquet, saved JSON
  profiles, PostgreSQL and Trino table/query metadata, and reviewed YAML/JSON specs,
  against CSV, JSON, Parquet and SQL output.
- Keep source profiling/evidence separate from the complete reviewed specification.
- Fix confirmed common-reader/rule representation gaps and multi-entity profiles.
- Exercise every FieldType, settings/modes and rule family across output adapters.

## Boundaries
No new database read authority, SQL execution, source-row reuse, transformation
activation or release is granted. Database matrix tests use fictional aggregate
metadata; existing allowlist/read-only/access tests remain required. Missing
optional packages are installation prerequisites, not different logical semantics.
