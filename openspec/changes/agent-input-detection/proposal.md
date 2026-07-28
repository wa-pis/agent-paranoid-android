# Change Proposal: agent-input-detection

## Why

The common `agent-plan` path requires users and AI clients to repeat an input
type that is usually obvious from the path.

## What Changes

- Detect CSV files, CSV folders, and validated safe-profile JSON inputs.
- Keep `--source-type` as an explicit override.
- Recognize DatasetSpec inputs and route users to the existing `generate`
  workflow instead of treating a spec as profile metadata.

## Safety

JSON detection uses the existing bounded, validating profile/spec loader.
Unknown, malformed, empty, and contradictory inputs fail closed.
