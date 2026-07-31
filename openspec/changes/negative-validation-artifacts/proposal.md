# Change: negative-validation-artifacts

## Why

Controlled invalid generation currently reports business-rule failures without
distinguishing selected negative cases from unplanned generator failures.

## What Changes

- Track expected validator failures by rule during controlled invalid
  generation.
- Compare expected and observed counts in the bounded business-validation
  report.
- Publish only aggregate counts in the generation manifest.

## Safety

The metadata contains rule indexes and counts only. It does not contain row
values, source values, PII, or production data.
