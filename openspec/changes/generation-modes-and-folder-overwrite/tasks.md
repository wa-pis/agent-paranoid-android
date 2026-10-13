# Tasks

- [x] Implement typed load multiplication and exact-count override.
- [x] Implement valid edge values without changing identifier/privacy behavior.
- [x] Implement folder replacement with rollback and no-follow checks.
- [x] Verify tests, public contracts, schema and full release gate.
- [x] Complete local implementation review and document remaining limits.

Final exact-main release gate: 3365 passed, 23 skipped. Strict typing, lint,
schema/contract freshness, strict MkDocs and installed-wheel regressions passed.
Independent AI-only exact-main approval, all four hosted gates and fresh Ubuntu
artifact hashes are recorded in [RC4 evidence](../../../docs/release-evidence-1.6.0rc4.md).

- [x] Accept final exact RC4 commit with independent review and remote gates.
- [x] Run Ubuntu preflight, sign acceptance manifest/tag and publish RC4.
- [x] Verify public packages/containers and record evidence.
- [x] Stop automation after successful public acceptance.
