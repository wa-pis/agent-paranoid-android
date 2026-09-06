# Generation Contract Review Evidence

## Immutable Initial Review

Codex Security scan `acfeb740-1d63-4221-a117-2484009a9429` reviewed all eight
changed production files in `fb5bcabc5099145df7376dd3ef174cecfdd38218` through
`967964e82baf001b6f3a8a13e1af0c616aa04a05`. A separate architecture worker
mapped the repository boundaries; a separate discovery worker reviewed privacy,
publication, and schema controls. The parent reviewed generation and remaining
validators. No live service or production data was used.

The completed immutable scan reported one low-severity privacy regression: CSV
numeric-string decoding had also been enabled at the mandatory generation gate.
Independent full-revision comparison and direct bundle reproduction confirmed
the bypass on synthetic input. That reviewed revision is not the accepted
release source.

## Correction And Regression Coverage

Generation and post-business-rule validation now retain strict string privacy
classification. Numeric decoding is enabled only by standalone revalidation.
Regression tests cover integer/float formula strings in all five generation
modes with privacy reporting disabled, as well as numeric CSV round-trip.

Two additional correctness findings from the parent review were corrected:
nullable one-to-one CSV empty strings are excluded from duplicate counting, and
an active aggregate cannot silently use a rejected or absent relationship.

RC1, RC2 and stable subsequently completed exact-commit independent review,
all required gates, Ubuntu preflight hashes, signed publication and public
verification. Final stable approval is recorded in
[acceptance #497](https://github.com/wa-pis/agent-paranoid-android/issues/497);
[stable evidence](../../../../docs/release-evidence-1.3.2.md) records immutable
artifact identities.
