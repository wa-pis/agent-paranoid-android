# Current synthetic candidate acceptance

Exact reviewed composition: `268efc9a4f6a7e5fa3e87f21b4fd86be87f7634f`.
Author runtime fixes: `fe69962` and `3d79644`, with four prospective activation patches.
The wheel remains version `1.5.0`; it is not a published 1.6 release artifact.

- Full offline release gate: 3158 passed, 19 skipped, coverage 90.70%; strict documentation build passed.
- Independent whole security scan `e01b29fa-0b22-4589-a82f-cc30343ad322`: complete, zero confirmed findings; all 197 executable files reviewed.
- Wheel SHA256: `430e04051288171e6cc0474f240b135d186f9c5db3145da2f5c4c9ae1ab72396`.
- Installed registered interface acceptance: 7 passed.
- Installed temporal, finance, skill and linked-domain workflows: 8 passed; the initially skipped real installed-baseline check subsequently passed separately.
- Separate base, gigachat and all installation profiles passed on Python 3.11.15, 3.12.13, 3.13.14 and 3.14.2 (12 profiles).
- Four isolated `doctor --require-extra gigachat` checks passed.
- Installed Python 3.14 fake GigaChat SDK suite: 49 passed.
- Installed Python 3.11 local auth and Parquet decimal-profile contracts: 24 passed (0.51s), 2026-10-07. Exact frozen-composition tests loaded through the candidate-only `PYTHONPATH`, with pytest source-path override disabled; no database/provider calls. This renews these local constituents, not remote authentication or final versioned CLI/API acceptance.

All fixtures were synthetic; no database or AI provider calls occurred. Public stable dependency downloads supplied missing installation-cache entries. Tests used installed package code; the first workflow replay reused existing dependencies, while the later package profiles used separate environments.

These results replace neither current versioned client-script acceptance nor policy/documentation reconciliation, exact-main CI, Containers, Documentation and Security, required independent GitHub approval, Ubuntu distribution hashes, signed acceptance manifest/tag, nor public verification. Historical private scale results remain tied to their original artifact.

As of this checkpoint there is no PR for `codex/fix-transformation-review`. On 2026-10-07 the owner explicitly authorized mandatory CI with real test Trino and synthetic data. This supersedes the earlier no-live-DB blocker for that CI job only; production access, other live databases and external AI calls remain prohibited. Independent GitHub approval and the remaining acceptance gates are still required. No approval, tag, publication or final release acceptance is claimed.

2026-10-07 installed unknown-metadata/sensitivity constituent: frozen candidate
`tests/test_source_adapters.py -k parquet` passed11/deselected8 in0.27s on
Python3.11 with candidate-only PYTHONPATH and pytest source-path override
disabled. Covers absent/null statistics, public unknown metrics, neutral-name
sensitive content, oversized cells, conservative native values, deadline and
pre-read row count. Profiling guide matches the unknown/fail-closed contract.
No DB/provider calls; final versioned CLI/API compatibility remains open.

2026-10-07 installed OAuth local opt-in:6passed0.97s on the same frozen
candidate/wheel and Python3.11. Explicit acceptance package root verifies the
subprocess imports installed code; pipe rejection precedes driver/artifact.
Other cases inject fictional terminal/browser callbacks; no browser or network
authentication occurs. Trino how-to links the six-method configuration contract;
strict documentation build passed0.39s after correcting the anchor.

2026-10-07 installed twelve-route replay: fully read unchanged harness
`scripts/accept_transformation_routes.py --public` exited0 with all12routes
and36 CLI negative assertions. Harness SHA256
`b8cf5366a5ec9716066dd83c0fcab1b19f7076b38038ed0da55a1c474f35fb57`;
exact268efc9a/wheel430e0405/Python3.11, candidate-only PYTHONPATH. Exact
decimal/date/null readback, value-free CLI/application-MCP review/execution,
input integrity and cleanup checked. SQL inputs use injected synthetic Arrow
streams; SQL outputs never execute. No DB, SDK-wire12route or scale claim.
Log `/private/tmp/apa-final-current-routes.log`.

2026-10-07 mandatory installed CSV scale:300000rows x50columns passed
(15M cells),174.948s,90150450 output bytes. Explicit512MiB/1800s budgets;
complete ordered readback, input digest, provenance and cleanup assertions.
Exact268efc9a/wheel430e0405/Python3.11; log
`/private/tmp/apa-final-current-scale300k.log`, exit0. Private replacement-only
CSV route, not public/12route scale or peak-memory containment evidence.

2026-10-07 target installed CSV scale:1000000rows x100columns passed
(100M cells),1237.135s,600500900 output bytes, exit0. Explicit1GiB/1800s
budgets; complete ordered readback, provenance, source integrity and cleanup.
Same exact268efc9a/wheel430e0405/Python3.11; log
`/private/tmp/apa-final-current-scale1m.log`. Private CSV replacement route
only; other input/output scale routes and final versioned RC remain open.

2026-10-07 installed Parquet->Parquet300000x50 passed244.925s/15Mcells,
2594621 output bytes, exit0; declared string/non-null schema and every output
cell, source digest, provenance and cleanup checked. Same exact candidate,
wheel and Python3.11;512MiB/1800s; synthetic files only. Log
`/private/tmp/apa-final-current-scale-parquet300k.log`. No cross-route scale claim.

2026-10-07 target installed Parquet->Parquet1Mx100 completed exit0:
100Mcells,17398511 output bytes,1685.927s harness monotonic elapsed, explicit
2GiB/1800s. Full schema/cell readback, provenance, input digest and cleanup
passed. Same exact268efc9a/wheel430e0405/Python3.11. Log
`/private/tmp/apa-final-current-scale-parquet1m.log`. Observed process wall
clock exceeded30minutes while harness monotonic elapsed stayed below1800s;
clock/scheduling discrepancy is unresolved, not evidence of a deadline bypass.
This passes the harness contract only; no hard wall-clock/RSS containment claim.
