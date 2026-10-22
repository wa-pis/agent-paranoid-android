# CLI Workflows

## Offline Demo

```bash
test-data-agent demo --output out/demo
```

The destination must not exist. The command uses a bundled fictional fixture,
seed `20260801`, and no network or optional integration.

## One CSV

```bash
test-data-agent generate-from-csv data/customers.csv \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

For explanation and review steps, use [First CSV Dataset](../getting-started/first-csv.md).

## Related CSV Tables

```bash
test-data-agent generate-from-example data/example_dataset \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/generated
```

See [Related Tables](../getting-started/related-tables.md) for relationship and
business-rule guidance.

## Reviewed DatasetSpec

For unequal table sizes, set counts while preparing the specification:

```bash
test-data-agent infer-spec out/profile.json --output out/dataset_spec.yaml \
  --count 100 \
  --entity-count warehouse.crm.customers=30 \
  --entity-count warehouse.public.orders=200 \
  --max-total-rows 230
```

Use exact entity names from the profile. Repeat `--entity-count ENTITY=COUNT`
for different entities; duplicate or unknown names and nonpositive counts reject.
An entity-specific count takes precedence over `--count`; other entities use
`--count`, or their profiled row count (at least one) when it is omitted.
This does not scale counts by a factor or infer relationships.

`--max-total-rows` is an optional inference-time ceiling on the resolved sum.
Oversized plans reject before field inference or spec publication. The ceiling
is not persisted as a generation setting: review the saved counts, then generate
without overriding them. A later `generate --count` or `load_test` multiplier
changes the requested volume and requires a new size review. Existing generation
row, byte and work limits still apply. Neither option changes DatasetSpec schema
1.1 or source access.

`infer-spec` expects a profiling-command artifact, not an existing DatasetSpec.
JSON keys `schema_version`, `privacy_rules`, `privacy_settings`,
`generation_settings` and `validation_settings` select spec parsing even if
profile fields are also present. Use the original profiling artifact for
inference, or pass a reviewed spec directly to `generate`. Do not delete privacy
settings to force a mixed JSON document to be interpreted as a profile.

```bash
test-data-agent generate dataset_spec.yaml \
  --seed 12345 \
  --format csv \
  --output out/generated
```

For a reviewed DatasetSpec, omitted `--mode` and `--invalid-ratio` retain its
saved settings. Explicit options override the effective spec, generated rows,
saved output spec and manifest together. A nonzero ratio requires `mixed` or
`negative`; specify `--invalid-ratio 0` when explicitly changing a saved mixed
spec to `valid`. Profile and direct-CSV generation still default to `valid/0`.

For previously reviewed safe profile metadata, use `--profile`:

```bash
test-data-agent generate --profile profile.json \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

`generate` accepts exactly one of a `DatasetSpec` path or `--profile`. Spec
generation writes a dataset folder. Single-table profile generation writes one
data file and requires `--count` and `--seed`. Multi-table profile generation
writes the complete output folder. All sources share the
[source/output matrix](source-output-matrix.md).

## Database Sources

Database workflows require mandatory physical-source allowlists and resource
budgets. Connection components and credential-free JDBC-style endpoint input
are environment configuration, never command-line secrets. Qualified column
wildcards expand only against allowlisted metadata and never become a
projection star. Reviewed query files use `profile-query`; query rows, SQL text,
literals, endpoints, and backend messages are excluded from the profile.
Direct non-sensitive date/timestamp query outputs include observed min/max
bounds when the aggregate source supplies valid endpoints. Derived expressions,
sensitive source/output names and all-null fields do not claim them.

`infer-spec` rejects query profiles marked with unsupported expression
dependencies; `profile-query` itself remains available. Reprofile old SQL
profiles without dependency metadata. Direct column aliases remain supported;
there is no automatic SQL-to-formula translation.

Follow the source-specific walkthrough instead of assembling commands from this
reference:

- [PostgreSQL Workflow](../how-to/postgresql.md)
- [Trino Workflow](../how-to/trino.md)

## Review-First Agent Flow

```bash
test-data-agent agent-plan data/example_dataset \
  --workspace out/agent \
  --count 25 \
  --seed 12345 \
  --format csv

test-data-agent agent-review out/agent
REVIEWED_SPEC_SHA256=replace-with-current-hash-from-review
test-data-agent agent-approve out/agent \
  --reviewed-spec-sha256 "$REVIEWED_SPEC_SHA256"
```

`agent-plan` stops before generation. Review `dataset_spec.yaml`, record the
current fingerprint from `agent-review`, and approve exactly that fingerprint.
Optional provider advice changes the spec and therefore requires another review:

```bash
test-data-agent agent-advise out/agent --provider openai
# Or explicitly select the experimental adapter:
test-data-agent agent-advise out/agent --provider gigachat
test-data-agent agent-review out/agent
```

OpenAI remains the default provider; GigaChat is an explicit experimental
choice. Providers receive safe metadata, cannot approve, and cannot generate.
See [Connect An AI Client](../ai_integration.md) for provider-neutral exchange
and trust-channel guidance.

## Generation Options

| Option | Meaning |
| --- | --- |
| `--count N` | Number of generated rows per entity or an override |
| `--seed N` | Non-negative deterministic seed |
| `--format csv\|json\|sql\|parquet` | Output format |
| `--mode valid\|mixed\|negative\|edge\|load_test` | Generation mode |
| `--invalid-ratio R` | Invalid share from `0` to `1` for applicable modes |
| `--business-rules PATH` | Reviewed YAML or JSON rule file |
| `--output PATH` | Output file or new output directory |
| `--overwrite` | Replace a complete DatasetSpec output folder, or the same valid manifest-owned single-entity file bundle |

Parquet output from a reviewed specification uses declared integer, float,
boolean, string, date and timestamp Arrow types, including nullable fields.
Timestamp offsets are preserved when one consistent offset is available.
Wide integer identifiers, mixed timestamp offsets and explicitly requested
malformed negative cells use marked scalar encodings where native Arrow types
cannot retain their logical values. The bundle reader restores them for validation;
negative datasets remain invalid. Ordinary incompatible typed values still fail
before publication. See the [output representations](source-output-matrix.md#output-representations-and-revalidation). A reviewed `DatasetSpec` version `1.1` may declare a
`decimal` field with a required `decimal_range` distribution containing
`precision` (1–38), `scale` (0–precision), and exact plain-text `min`/`max`
bounds. Generation uses seeded base-ten integer units; CSV/JSON render decimal
text, PostgreSQL SQL uses `NUMERIC(p,s)`, and Parquet uses `decimal128(p,s)`.
CSV is not self-describing: the generated directory's `dataset_spec.yaml`
records the DECIMAL precision, scale and nullability. The manifest declares the
reversible CSV null/text encoding: null is `\N`, while an empty cell is empty text.
Keep both companions when reusing the export; the manifest binds the specification
by fingerprint. Legacy unmarked CSV keeps its previous interpretation.
Version `1.0` remains readable but cannot declare `decimal`. Parquet and
declared PostgreSQL/query `numeric(p,s)` profiles retain only schema precision
and scale; they do not infer a runnable exact range. Reviewed ordinary DECIMAL
formulas and aggregates use bounded exact arithmetic with one HALF_UP rounding
at the declared target scale. See the [rule contract](../rc4-external-feedback.md#business-rules-across-interfaces). Ordinary generation never preserves
source rows. The separately selected transformation candidate has its own
[saved-profile contract](cli.md#closed-common-profile-workflow-candidate), exact
typed mappings and local approval boundary; its common public registration is
not enabled by these generation commands. Bare SQL `numeric`
without `(p,s)` still uses approximate FLOAT semantics, not exact evidence.
Sensitive DECIMAL ranges remain rejected before generation; explicit numeric
measure semantics retain sensitive-name, flag and classification vetoes.

DatasetSpec folder generation requires a new or empty destination unless
`--overwrite` is set. With that flag it replaces the complete folder, including
obsolete files, after generation and validation finish. Staging and a backup
support rollback on publication failure; this is not a concurrent-reader atomic
exchange. Symlinks and folders containing the input spec or rule file are refused.
`generate-from-example` still requires a new or empty destination.

Single-entity output suffixes must match the selected format. Its separate
file-bundle overwrite requires matching ownership, manifest, format and sibling
files. These checks do not impose manifest ownership on complete-folder replacement.

## Profiling Options

| Option | Meaning |
| --- | --- |
| `--table NAME` | Override the inferred entity name for one CSV |
| `--cache-dir PATH` | Safe profile cache location |
| `--no-cache` | Force fresh folder profiling |
| `--rule-sample-rows N` | Bound row-level relationship and rule mining |
| `--local-category ENTITY.FIELD` | Retain one reviewed bounded non-sensitive local enum or constant; repeatable and default-off |

The local-category selector does not bypass sensitive-name, content,
cardinality, value-length, destination, or resource checks. Exact approved
values remain local and are replaced before external-provider requests.

See [generation modes and folder replacement](generation-modes.md) for the
post-RC3 edge boundaries, load multiplier and complete-folder overwrite contract.
