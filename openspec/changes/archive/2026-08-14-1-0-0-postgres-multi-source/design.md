# Design: 1-0-0-postgres-multi-source

## Approach

Keep the change at the adapter boundary. Source-specific code is responsible
for safe inspection and aggregate profiling; the existing deterministic
`DatasetProfile` → reviewed `DatasetSpec` → generation → validation pipeline
remains responsible for synthesis.

```text
PostgresSource / TrinoSource / local files
          ↓
   SourceProfiler port
          ↓
  DatasetProfile + source map
  + reviewed preserve scopes
          ↓
 agent review / optional AI hypotheses
          ↓
 existing DatasetSpec and deterministic generation
          ↓
 validated records → CSV / JSON / Parquet / PostgreSQL SQL
```

Do not begin with a large generic database framework. A minimal protocol and
source-specific implementations are enough:

```python
class SourceProfiler(Protocol):
    source_type: str

    def profile(self, request: ProfileRequest) -> DatasetProfile:
        ...
```

The public PostgreSQL facade should be typed and testable without a live
database:

```python
@dataclass(frozen=True)
class PostgresSource:
    source_id: str
    connection: PostgresConnectionConfig
    scope: SourceScope


@dataclass(frozen=True)
class PostgresProfileRequest:
    sources: tuple[PostgresSource, ...]
    limits: BundleProfileLimits
    include_relationships: bool = True
    include_distributions: bool = True


def dataset_profile_from_postgres(
    request: PostgresProfileRequest,
    *,
    driver: PostgresDriver,
) -> DatasetProfile:
    ...
```

`PostgresDriver` is injected. The optional runtime extra may use `psycopg`, but
the deterministic profile conversion and query policy must not import or create
the driver at module import time.

## Source Identity And Bundles

Every configured source receives a user-chosen stable `source_id`, such as
`hr`, `payroll`, or `analytics_eu`. A host, DSN, username, or database password
is not an identity and must never be used as one.

Entities in a multi-source profile use a canonical qualified name:

```text
hr.public.employees
payroll.public.salary
analytics_eu.hr.employees
```

The canonical name is used by existing relationship/spec validation. A
versioned source-bundle metadata record retains the mapping from canonical name
to source kind, alias, schema, and table for review and presentation. It must
not retain connection strings, credentials, backend error text, or raw values.

Local declared relationships are marked as declared evidence. Cross-source
relationships are hypotheses unless the source explicitly declares them; they
retain evidence, confidence, and review status. A human must approve them
before they enter the generation spec.

## PostgreSQL Connection And Policy Boundary

`PostgresConnectionConfig` contains validated endpoint and session settings,
while secret material is resolved from an external environment or secret
provider at connect time. The adapter must:

- require an explicit schema allowlist and optional table allowlist;
- reject wildcard or unscoped discovery as a normal production path;
- establish a read-only transaction/session before metadata or aggregate work;
- apply `statement_timeout`, `lock_timeout`, and an invocation deadline;
- close cursors and connections on success, error, cancellation, and timeout;
- use quoted identifiers and internally generated parameterized queries only;
- reject DDL, DML, function calls with side effects, and arbitrary SQL input.

Metadata queries use `pg_catalog`/`information_schema` only where their output
is bounded and allowlisted. Supported CHECK constraints are normalized into the
existing constraint model. Unsupported or ambiguous checks become a bounded
warning/hypothesis; raw expressions are not forwarded to an AI provider or
public error.

## Aggregate Profiling

The first PostgreSQL profiler should cover:

- table row counts;
- column type, nullable, null count/ratio, and approximate distinct count;
- numeric/date/timestamp ranges and bounded shape summaries;
- safe low-cardinality distributions with masking or synthetic categories;
- declared PK/FK metadata and aggregate FK coverage checks;
- explicitly configured temporal or reconciliation checks where the existing
  rule model can represent them.

The profiler must not return rows. It must not use a general-purpose `fetchall`
escape hatch for profiling. Each query consumes the shared invocation budget.
Sensitive numeric fields follow the existing non-reversible Trino policy: exact
extrema or singleton values must not cross the safe profile boundary.

## Selective As-Is Preservation

Reuse the existing typed `LocalCategoryField(entity, field)` authorization
instead of adding a global masking flag. For database sources, `entity` is the
canonical source-qualified entity identity, so authorization resolves to one
source, schema, table, and column. For local files, it retains the existing
entity-and-field scope.

Authorization is necessary but not sufficient. Before retaining values, the
profiler must verify that the field is explicitly classified as a bounded,
non-sensitive business enum or constant and that observed values remain within
configured cardinality and value-length limits. Recognizable PII, secrets,
credentials, identifiers, quasi-identifiers, or free text make the requested
preservation fail closed. Low cardinality alone is not a safe classification.

Successful preservation retains the reviewed scalar values and bounded counts
without retaining source rows or row order. The same exact values may be used
by deterministic local generation, constraints, conditional rules, and local
SQL export. Non-allowlisted fields keep the existing mask, suppress, or
synthetic replacement policy.

Destination policy remains independent of local authorization. External
provider payloads always replace source literals with deterministic labels.
Default MCP responses, logs, errors, and source-bundle metadata never disclose
the values. Provider responses are mapped back only inside the local reviewed
workflow under the existing field-scoped contract.

## PostgreSQL SQL Export

SQL export is a deterministic output adapter after generation and validation;
it is not part of the PostgreSQL source adapter and cannot access a source
connection. Its only row input is the generated dataset. Exact values from an
approved as-is field can therefore appear only after they have entered those
generated records through the reviewed field policy.

The exporter writes one UTF-8 `.sql` file containing deterministic PostgreSQL
DDL and INSERT statements. It quotes schema, table, and column identifiers,
serializes supported scalar values with PostgreSQL-compatible literals,
preserves NULL, and emits tables and relationships in a stable dependency-aware
order. The file is transaction-delimited so successful execution is atomic.

All identifiers, type mappings, relationships, and values are validated before
the destination is replaced. Unsupported or ambiguous types and values fail
closed. The writer uses a sibling temporary file and atomic replacement, and
removes the temporary file after failure or cancellation so a partial SQL file
is never reported as complete.

Normal tests use golden files plus a PostgreSQL parser or parse-only validation
that does not require a live server. An explicitly gated integration test may
execute the file against disposable PostgreSQL, but live access is not required
for the package test suite.

## Trino Coordinator Boundary

A `TrinoSource` represents one coordinator and its allowlisted catalogs and
schemas. Several catalogs behind that coordinator are one connection boundary:

```yaml
sources:
  warehouse:
    type: trino
    coordinator_env: TRINO_WAREHOUSE_DSN
    catalogs: [hr, payroll, crm]
```

Several coordinators are several named sources. The existing Trino client,
query builders, masking, and invocation budgets should be reused rather than
duplicated. A same-coordinator cross-catalog aggregate check is allowed only
when explicitly enabled by policy and still consumes the source and bundle
budgets. Cross-host direct PostgreSQL sources do not receive an implicit join
capability.

## Bundle Budgets And Failure Semantics

Each source has a local budget, and the orchestrator owns one non-resettable
bundle budget shared by all nested profilers:

```python
@dataclass(frozen=True)
class BundleProfileLimits:
    max_sources: int = 10
    max_tables: int = 100
    max_columns: int = 100
    max_statements: int = 150
    max_seconds: float = 120.0
    max_estimated_scan_bytes: int | None = None
```

The implementation may use stricter source-specific limits, but helpers may not
reset the counters. If a requested source, table, or required operation fails,
the bundle fails closed with a fixed local error that identifies only the safe
source alias and local reason. No partial profile is accepted as complete.

## User Workflow

The first stable workflow should be expressible through the Python API and one
documented CLI/configuration path:

```text
configure aliases and allowlists
  → profile PostgreSQL/Trino sources
  → review qualified entities and relationship hypotheses
  → optionally ask AI to rank hypotheses
  → approve the reviewed DatasetSpec
  → generate and validate synthetic output
```

AI and MCP are optional. A deterministic PostgreSQL profile must work without
either of them.

## Failure Modes

- Invalid source alias, schema, table, endpoint, or budget: reject before
  connecting.
- Missing allowlist or read-only session setup failure: fail closed.
- Statement timeout, cancellation, connection loss, or budget exhaustion: close
  resources and publish no complete profile.
- Unsupported CHECK or cross-source relationship: retain only bounded local
  warning/hypothesis metadata; never silently enforce it.
- Source failure in a bundle: return a fixed bounded bundle error and do not
  permit generation from a partial source set.
- AI/provider failure: preserve the deterministic profile and return to human
  review; never grant database access or approval authority.
- Requested as-is field fails classification, content, or bounded-domain
  checks: reject the preservation request without publishing a partial profile.
- SQL identifier, type, or value cannot be represented safely: reject before
  replacing the target and remove the temporary file.

## Alternatives

- **Require Trino for every database:** rejected because it adds infrastructure
  and excludes PostgreSQL-only deployments.
- **Expose arbitrary SQL to a PostgreSQL client:** rejected because read-only
  intent and resource bounds become hard to enforce at the adapter boundary.
- **Build a universal ORM/database abstraction first:** rejected as speculative
  scope; PostgreSQL and the existing Trino boundary cover the stable use cases.
- **Join all sources in the application:** rejected because it would move source
  values across trust boundaries. Cross-source evidence must remain aggregate,
  explicitly configured, or human-reviewed.
- **Add a global no-mask switch:** rejected because destination and field
  classification cannot be reviewed or enforced at that granularity.
- **Dump PostgreSQL source rows as SQL:** rejected because it violates the
  synthetic-only output boundary. SQL is rendered only after deterministic
  generation and validation.
