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
        regions = ("north", "south", "east", "west")
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

Provider output is treated as untrusted. The generator rejects recognizable
PII or secrets, wrong field types, non-finite numbers, invalid date/time
strings, and oversized strings. Providers are not called for identifiers,
sensitive fields, or fields whose names or semantic types are conservatively
classified as sensitive. Returning `None` delegates that field to built-in
generation.

Providers should be deterministic for the same request. They must generate new
synthetic values and must not load production rows or call systems that return
real customer data.
