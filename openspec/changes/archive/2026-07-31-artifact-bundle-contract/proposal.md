# Change Proposal: artifact-bundle-contract

## Summary

Freeze the generation bundle layout and validation report with checked-in
golden contracts before 1.0.

## Motivation

The generation manifest is already contracted, but consumers also depend on
stable artifact filenames and the typed validation report.

## Scope

In scope:

- record the current JSON generation bundle filenames;
- record and type-check the validation report;
- require explicit fixture review for future artifact changes.

Out of scope:

- changing generated data, filenames, formats, or validation behavior.

## Safety Impact

Fixtures contain only deterministic synthetic metadata and no dataset rows.

## Compatibility

The current artifact bundle remains unchanged.
