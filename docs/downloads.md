# Downloads

English · [Русский](ru/downloads.md)

Published builds provide:

- <a href="handbook.pdf">PDF handbook</a>: read, print or share the user guide.
- <a href="handbook.html">Standalone HTML handbook</a>: one file with embedded assets and
  internal chapter links; detailed references link to the matching version online.
- <a href="handbook.md.zip">Markdown source ZIP</a>: the documentation source tree, including
  reference and historical pages with their original provenance.
- <a href="site.zip">Offline site ZIP</a>: the complete selected documentation version.
  Extract it and run `python3 -m http.server` to use browser search locally.

<a href="../handbook/">Read or print the combined handbook</a>. The handbook follows the
user navigation; history, roadmap and documentation administration are excluded.
It is assembled by MkDocs' print-site plugin rather than a separate book renderer.

Every download is bound to package version/source and documentation revision.
The <a href="documentation.json">export manifest</a> records handbook chapters and artifact
hashes. Documentation corrections are distinct from package release review.
Exporting docs does not export datasets, profiles, credentials or approvals.

Download files appear only after the complete build. A plain local preview has
the combined print page; use the [full build](development/documentation.md) for
PDF, standalone HTML and ZIP files.
