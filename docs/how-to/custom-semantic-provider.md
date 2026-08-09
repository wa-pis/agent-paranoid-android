# Build A Semantic Value Provider

Use a semantic provider when an organization needs deterministic synthetic
labels or codes that are not part of the built-in generator. The provider is a
Python API extension point; CLI and MCP generation continue to use built-in
generation.

```python
from test_data_agent.generation import SemanticValueRequest, generate_dataset


class SalesRegionProvider:
    def generate(self, request: SemanticValueRequest) -> str | None:
        if request.semantic_type != "sales_region":
            return None
        regions = (
            "synthetic_north",
            "synthetic_south",
            "synthetic_east",
            "synthetic_west",
        )
        return regions[(request.seed + request.row_index) % len(regions)]


rows = generate_dataset(
    spec,
    seed=123,
    semantic_provider=SalesRegionProvider(),
)
```

The request contains only field metadata, the row index, and the generation
seed. It never contains source rows, profile samples, distributions,
credentials, or previously generated values.

Provider output is treated as untrusted. Each synchronous call is isolated
behind a five-second deadline and replayed immediately with the same immutable
request; timeout, failure, or unequal replay output aborts generation before
publication. String fields must return a value beginning with `synthetic_`, so
names, addresses, and other identity-like strings cannot rely on heuristic
detection. Date/datetime strings and non-string values retain their typed
contracts. The generator also rejects recognizable PII or secrets, wrong field
types, non-finite numbers, invalid date/time strings, and oversized strings.
Providers are not called for identifiers, sensitive fields, or fields whose
names or semantic types are conservatively classified as sensitive. Returning
`None` delegates that field to built-in generation.

Providers must be deterministic for the same request. They must generate new
synthetic values and must not load production rows or call systems that return
real customer data. A timed-out synchronous provider may finish only in its
isolated daemon thread; its late result is discarded and cannot enter the
dataset.
