# Tasks
- [x] A1: Locate existing runtime authentication configuration and distinguish the historical absence claim from current main.
- [x] A2: Enumerate every connection factory/caller and verify existing auth modes, secret references and validation boundaries.
- [ ] A3: Obtain version/configuration evidence for the external failure; implement only a separately reproduced gap without changing unauthenticated defaults.
- [x] A4: Test missing credentials, unsupported modes, URL credentials, HTTP overrides, certificate failures and sanitized 401/403 handling.
- [x] A5: Place secret canaries in fake errors/config and assert absence from logs, repr, JSON, audit, profiles and MCP/CLI responses.
- [x] A6: Re-run allowlist, read-only, invocation budget and optional-dependency tests.
- [ ] A7: Update database-source-configuration/MCP contracts, .env example without credentials, guides and release candidate evidence.
- [x] A8: Leave live authenticated acceptance explicitly pending unless separately authorized and available.

A3 evidence: the user tentatively identified version 1.6.0; the selected auth
method is unavailable. The historical 401 remains unconfirmed. A separately
reproduced untyped-driver exception-context gap is fixed and covered by tests.
A7 candidate evidence and documentation are prepared; full PR CI remains pending.
