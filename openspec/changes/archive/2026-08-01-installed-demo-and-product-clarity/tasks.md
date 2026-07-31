# Tasks: installed-demo-and-product-clarity

- [x] Add the `demo` CLI parser, dispatcher, and application command.
- [x] Add a fictional non-sensitive fixture as a base-wheel resource.
- [x] Reuse the public profile → spec → generate → validate workflow with an
  explicit deterministic seed.
- [x] Stage and publish demo artifacts atomically; reject existing destinations
  and clean up all failure paths.
- [x] Add tests for successful execution, repeatability, offline operation,
  missing/unwritable output, existing output, and partial-failure cleanup.
- [x] Add an isolated-wheel test that runs the installed console entrypoint and
  proves the bundled resource is present without the source checkout.
- [x] Verify the manifest and validation artifacts independently in tests.
- [x] Make the demo the first README scenario with a short sample result.
- [x] Document preserved properties: schema/types, nullability, bounded shape,
  relationships, temporal dependencies, and executable business rules where
  the selected input provides evidence.
- [x] Document non-guarantees: source-value copying, real PII, statistical
  anonymity, all re-identification attacks, and cross-environment byte identity.
- [x] Run the package, documentation, lint, typing, and full test gates.
