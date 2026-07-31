# Change: wheel-python-matrix

## Why

The full test suite covers every supported Python version, but the built wheel
is installed and exercised only on the newest interpreter.

## What Changes

- Build the wheel independently on Python 3.11 through 3.14.
- Install each wheel into an isolated base environment.
- Verify installed metadata, dependency and size budgets, and local doctor.
- Retain the existing full optional-profile wheel smoke and required check.

## Impact

Pull requests gain four compatibility jobs. Runtime behavior and the existing
required `Wheel smoke` check name remain unchanged.
