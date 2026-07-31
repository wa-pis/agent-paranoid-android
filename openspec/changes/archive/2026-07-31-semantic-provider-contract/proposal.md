# Change Proposal: semantic-provider-contract

## Summary

Add a provider-neutral Python contract for organization-specific synthetic
semantic values.

## Motivation

Organizations need deterministic domain labels and codes without embedding
their vocabularies in the core generator. Provider output must not bypass the
project's privacy boundary.

## Scope

In scope:

- immutable row-free provider requests;
- optional provider use in the Python generation API;
- fail-closed output type, size, PII, and secret validation;
- built-in generation for sensitive and identifier fields.

Out of scope:

- CLI or MCP provider loading;
- provider discovery or dynamic imports;
- access to source rows, profiles, distributions, or credentials.

## Safety Impact

Providers receive metadata only and cannot override sensitive generation.
Their output is untrusted until core validation succeeds.

## Compatibility

Generation without a provider is unchanged.
