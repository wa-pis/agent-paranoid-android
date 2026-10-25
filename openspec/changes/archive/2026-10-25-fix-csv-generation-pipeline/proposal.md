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
- Exclude only negative fixed-point amounts with a nonzero fractional part from
  the permissive phone heuristic. Normalize bounded integral decimal/exponent
  spellings for phone/card detection, and omit ranges for every sensitive field.
  Preserve explicit name checks and single-secret detection.
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

## Container acceptance prerequisite

PR container scanning found release-blocking PCRE2 vulnerabilities inherited
from the pinned Python Bookworm base. All three runtime targets install the
fixed Debian package `libpcre2-8-0=10.42-1+deb12u1` and verify its version at
build time. Trivy remains enabled without exclusions. APT indexes are removed
in the same layer. Container CI must build, smoke-test and scan this change
before acceptance; no published image or release is changed by this PR.
