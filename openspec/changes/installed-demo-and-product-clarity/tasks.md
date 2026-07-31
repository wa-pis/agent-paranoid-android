# Tasks: installed-demo-and-product-clarity

- [ ] Add the `demo` CLI parser, dispatcher, and application command.
- [ ] Add a fictional non-sensitive fixture as a base-wheel resource.
- [ ] Reuse the public profile → spec → generate → validate workflow with an
  explicit deterministic seed.
- [ ] Stage and publish demo artifacts atomically; reject existing destinations
  and clean up all failure paths.
- [ ] Add tests for successful execution, repeatability, offline operation,
  missing/unwritable output, existing output, and partial-failure cleanup.
- [ ] Add an isolated-wheel test that runs the installed console entrypoint and
  proves the bundled resource is present without the source checkout.
- [ ] Verify the manifest and validation artifacts independently in tests.
- [ ] Make the demo the first README scenario with a short sample result.
- [ ] Document preserved properties: schema/types, nullability, bounded shape,
  relationships, temporal dependencies, and executable business rules where
  the selected input provides evidence.
- [ ] Document non-guarantees: source-value copying, real PII, statistical
  anonymity, all re-identification attacks, and cross-environment byte identity.
- [ ] Run the package, documentation, lint, typing, and full test gates.
