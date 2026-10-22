# Design: external-feedback-1-6

Treat the final report as the latest reported observation, but independently
verify claims against main. Historical sections that contradict later corrections
are not additional bugs. Distinguish code-confirmed behavior, tested behavior,
external observations and unknowns. Do not label an issue fixed just because
documentation describes a workaround.

Keep intake, focused specifications and first implementation on one isolated
branch. Subsequent runtime changes should be separate focused PRs; each must
update its own tasks, tests, public docs and applicable baseline requirement.

Work order: reproduce and fix the small CLI diagnostic first; investigate numeric
classification without weakening PII protection; verify existing Trino authentication;
then implement bounded relational planning and statistics. Safety gates take
priority over convenience. Do not re-run missing private harnesses or claim live
database acceptance from fake-driver tests.

The numeric report needs semantic review: a negative base-10 exponent is correct
for subunit values. Truncating it to zero or discarding values below one would
lose information. Main already implements optional zero/subunit mass and a
minimum subunit exponent. Verify that behavior and investigate profile provenance
or adapter gaps before proposing duplicate fields.

Documentation is published only after the new workflow has deployed and verified
the public identity and exports. A successful PR build, a package release or an
older Pages deployment does not establish that result.
