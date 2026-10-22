# Change Proposal: feedback-cli-contract-clarity

## Summary
Make generation recovery and reproducibility claims precise without changing
sampling, validation, seed, preservation or output semantics.

## Motivation
Final feedback #25 reproduces an unhelpful mode/ratio error. Older UX observations
also confuse sampling bounds with invariants, scenario probabilities with quotas,
validation with fidelity and explicit load-test counts with multiplication.

## Scope
P2: mode/ratio recovery; ordered-spec seed documentation; bounds-versus-constraints
examples; conditional/EAV rule limitations; verification of current output-path,
formula failure and infer-spec help before changing already-correct behavior.

Out of scope: schema-breaking validation changes, automatic formula repair,
source SQL expression transfer, changing --count or making seed output independent
of spec ordering. Do not add a second business-rule language.

## Safety Impact
Fixed diagnostics must not echo input values, expressions, credentials or driver
errors. Rejections keep exit status, leave caller specs unchanged and publish
no output. Existing privacy and controlled-invalid publication gates remain.

## Compatibility
Only human-readable recovery text changes in the first implementation. CLI
JSON envelope and exit 2 remain stable. Public Python behavior is unchanged apart
from the ValueError message. Document first; separately specify any new invariant.
