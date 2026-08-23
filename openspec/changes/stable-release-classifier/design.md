# Design: stable-release-classifier

Treat the maturity classifier as release identity metadata derived from the
version phase:

- a PEP 440 prerelease uses `Development Status :: 4 - Beta`;
- a stable release uses `Development Status :: 5 - Production/Stable`.

Extend the existing built-distribution metadata checks to inspect both the
wheel and source distribution. The release gate must fail when either artifact
has a classifier inconsistent with its version. This keeps the correction in
the existing release-validation path and does not add runtime code.

The already published `1.3.1` artifacts remain immutable. The source metadata,
test, and changelog correction ships with the next normally scheduled release.
