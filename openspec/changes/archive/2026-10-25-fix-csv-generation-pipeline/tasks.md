## Implementation
- [x] Reproduce six failing CSV pipeline cases with synthetic fixtures.
- [x] Align generated identifier prefix with privacy validation.
- [x] Bound fingerprint-based distinct tracking and test duplicate/cap cases.
- [x] Preserve repeated string ID categories.
- [x] Narrow decimal phone and cc/ccy name false positives.
- [x] Preserve validated opt-in CSV enums and reject sensitive opt-ins.
- [x] Preserve timestamps with spaced offsets.
- [x] Complete regression, lint and type checks.
- [x] Review and release the privacy-adjacent changes as a release candidate.

## Final evidence reconciliation — 2026-10-25

The changed CSV/privacy scope is included in the completed 52-file security diff review plus exact-main supplemental acceptance recorded in PR #655. Candidate v1.7.0rc1 published from 64b7c8c3bbb0174fd7e159c4dfb42312045a1716 after all exact-main gates and Ubuntu preflight; all 12 public acceptance jobs passed in 40173739663.

[1.7.0rc1 release evidence](../../../../docs/release-evidence-1.7.0rc1.md) records exact source, hashes and actual workflow identities. Earlier pending checkpoints retain their original historical meaning.
