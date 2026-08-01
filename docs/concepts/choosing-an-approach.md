# Choose An Approach

Agent Paranoid Android is for teams that need deterministic test datasets from
bounded CSV or Trino-derived evidence without copying source rows. Its primary
interfaces are the CLI and Python library. MCP, Trino access, and AI providers
are optional integrations around the same review and validation boundaries.

## Quick Comparison

| Need | Best starting point | Why |
| --- | --- | --- |
| A safe, repeatable dataset from profiled structure and reviewed rules | Agent Paranoid Android | Profiles bounded evidence, generates fresh values, validates executable rules, and records a seed and manifest. |
| A few hand-authored values or one simple object factory | Faker or an application fixture factory | Less setup when you already know every field and do not need profiling, review artifacts, or dataset validation. |
| Application-native fixtures coupled to ORM models and lifecycle hooks | A framework fixture factory | Better fit when model constructors and database callbacks are the contract being tested. |
| Production-like statistical fidelity with formal privacy targets | A specialist statistical synthesizer plus a privacy evaluation | This project does not certify anonymity, differential privacy, or resistance to every re-identification attack. |
| A masked or reduced copy of production | A governed masking/subsetting system | Use only when policy permits retaining real rows; this project deliberately generates fresh rows instead. |

## Choose This Project When

- source access must stay read-only and metadata-focused;
- generated rows must be reproducible from an explicit seed;
- foreign keys, temporal order, formulas, and business rules must be executable
  and independently validated;
- humans must approve inferred specifications before generation;
- CSV, JSON, SQL, or Parquet output needs an evidence manifest.

Start with the offline installed demo:

```bash
test-data-agent demo --output out/demo
```

## Choose Something Else When

Use a simpler factory when manually defining every field is cheaper than
profiling and review. Use a specialist privacy system when you need a measured
privacy guarantee. Use governed masking only when retaining source rows is an
explicit requirement and is allowed by your data policy.

No approach removes the need to review sensitive identifiers, rare free text,
quasi-identifiers, and organization-specific privacy requirements.
