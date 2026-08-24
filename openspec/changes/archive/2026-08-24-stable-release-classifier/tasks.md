# Tasks: stable-release-classifier

- [x] Set `Development Status :: 5 - Production/Stable` for the next stable
  release while retaining `Development Status :: 4 - Beta` for prereleases.
- [x] Add release-artifact coverage that validates the maturity classifier in
  both wheel and source-distribution metadata against the PEP 440 version.
- [x] Ensure stable promotion checks fail if a release candidate classifier is
  retained.
- [x] Add a concise changelog entry to the release that publishes the corrected
  metadata.
- [x] Run the focused release-artifact tests and the full release gate for the
  release commit.
