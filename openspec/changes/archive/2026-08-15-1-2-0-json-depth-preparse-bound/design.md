# Design: 1-2-0-json-depth-preparse-bound

## Approach

Add one helper beside the existing bounded YAML loader. It scans JSON text once,
counts opening object and array delimiters outside strings, and rejects depth
above `TEST_DATA_AGENT_MAX_JSON_DEPTH` before calling `json.loads`.

Use the helper at the three shared local JSON boundaries:

- generated dataset validation input;
- JSON DatasetProfile/DatasetSpec adapters; and
- safe profile-cache loading.

## Parser Boundary

The scanner tracks JSON string and escape state so braces and brackets inside
string literals do not affect depth. It intentionally does not validate JSON
grammar; malformed input within budget continues to fail in `json.loads` with
the existing diagnostics.

## Failure Modes

- Excessive depth raises `InputLimitError` before parser invocation.
- Malformed JSON within the limit follows the standard JSON decoding path.
- Profile-cache callers continue treating invalid cache content as a cache miss.
- No importer returns a partially materialized value.

## Alternatives

A streaming parser could combine grammar validation and depth enforcement, but
would add a runtime dependency for bounded local files. A small linear scan is
sufficient for this boundary and keeps standard JSON semantics authoritative.
