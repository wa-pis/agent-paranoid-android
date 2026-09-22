# Repair CSV profile-to-generation round trips

## Why

CSV inference truncates distinct evidence after 1,000 values, treats repeated
string ID fields as unique generators, and can classify decimal amounts as
phones. Generated IDs on long entity names fail post-solve privacy validation.
Reviewed local categories and timestamps with spaced offsets lose information.

## What changes

- Align generated identifier and sensitive-string prefixes with validation.
- Track at most 100,000 SHA-256 distinct fingerprints per column independently
  of the 1,000 raw-value frequency budget. At the cap report a conservative
  lower bound that cannot certify uniqueness.
- Use categorical evidence for repeated bounded string ID fields.
- Exclude plain decimal amounts from the permissive phone content heuristic;
  preserve explicit name checks, integer PII checks, and single-secret detection.
- Match the short `cc` name marker as a token, avoiding `ccy` false positives.
- Preserve explicitly reviewed CSV string enums only after existing local
  category safety validation; default profiles still use synthetic labels.
- Parse timestamps with whitespace before UTC offsets without losing time.

## Compatibility and scope

Profile/spec schema remains 1.0. Generated string IDs change prefix. Existing
distribution prefix fields remain accepted; arbitrary prefix execution and
general declassification are not introduced. Integer-only amounts remain
subject to conservative PII detection. Monthly date granularity is deferred.
Treat these privacy-adjacent changes as release-candidate work.
