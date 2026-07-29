# Change Proposal: provider-neutral-advisor

## Why

The deterministic agent workflow is ready for AI clients, but the package has
no narrow Python contract for model-specific adapters. Integrations would need
to invent their own request shape, trust model output directly, or couple the
core package to one provider SDK.

## What Changes

- Add a provider-neutral `DatasetAdvisor` protocol.
- Build fingerprint-bound requests from safe profile metadata and a baseline
  `DatasetSpec`.
- Validate structured advisor proposals before they reach review artifacts.
- Keep provider SDKs and model execution outside the base package.

## Safety

Advisor input excludes source and generated rows. Profile text is explicitly
marked untrusted. Proposals cannot weaken privacy or operational settings,
change schema identity, bypass approval, or trigger generation.
