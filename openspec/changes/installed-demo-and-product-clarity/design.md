# Design: installed-demo-and-product-clarity

## Approach

Implement the command as a thin CLI adapter over the existing application
workflow. Load the fixture with `importlib.resources`, copy neither fixture
rows nor fixture files into the generated dataset, and pass an explicit seed
through profiling, spec inference, generation, and validation.

Stage all demo artifacts in a temporary folder beneath the requested output
parent. Publish the folder only after generation and validation succeed. Use
the existing bounded output and path checks so an existing destination,
unwritable parent, interruption, or disk failure leaves no successful-looking
partial result.

## Data And Contracts

- CLI: `test-data-agent demo --output PATH`, with help and structured errors
  consistent with existing commands.
- Package resources: a small synthetic fixture included in the base wheel.
- Output: generated rows, profile/spec metadata, validation report, generation
  manifest, and a concise stderr/stdout summary.
- Manifest: explicit seed, row counts, validation status, package/runtime
  evidence, `synthetic: true`, and `source_rows_copied: false`.
- README: one command, representative synthetic rows, preserved semantics, and
  explicit privacy/reproducibility limits.

## Failure Modes

- Existing output path: fail before writing unless overwrite is explicitly
  added to the contract.
- Missing or malformed packaged resource: fail clearly and leave no output.
- Generation, validation, or serialization failure: remove staged artifacts
  and return a non-zero CLI result.
- Unwritable output parent: report the path error without leaking fixture
  contents.
- Repeated invocation with the same seed and package/environment: produce the
  same logical and, where supported, byte-identical demo artifacts.

## Alternatives

### Keep using `tests/` fixtures

Rejected. It makes the installed package workflow depend on the source
repository and encourages users to treat test fixtures as product resources.

### Add a network-backed demo

Rejected. The first workflow must be offline, reproducible, and safe in
restricted environments.

### Add a separate demo generator

Rejected. A second path could drift from the safety and validation behavior of
the supported product workflow.
