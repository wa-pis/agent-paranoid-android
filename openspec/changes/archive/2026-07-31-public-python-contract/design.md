# Design: public-python-contract

## Approach

Add a deterministic `public-python-api.json` fixture containing the sorted
names from `test_data_agent.__all__`. Generate it through the existing public
contract fixture pipeline and validate that every name remains importable.

## Failure Modes

- An accidental export removal changes the fixture comparison.
- A stale `__all__` entry fails the resolution assertion.
- Intentional API evolution requires explicit fixture review and compatibility
  documentation.

## Alternatives

Runtime signature snapshots were deferred because annotations and Pydantic
schemas already have dedicated contracts, while signature serialization would
add unstable implementation detail.
