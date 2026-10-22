# Documentation Versions

The default site contains maintained guidance for the latest publicly verified
stable package. Its banner identifies the package version and documentation
revision. Documentation corrections do not inherit the package's exact-SHA review.

Open the [stable version selector](https://wa-pis.github.io/agent-paranoid-android/versions/stable/) to choose an available
guide. **mike** maintains the selector, version directories and stable alias on
GitHub Pages. Older package guides retain their own rendered content and search
index; they are not rebuilt automatically with today's prose.

A version guide records both its package source and documentation revision. It
may include later reviewed corrections; it is not claimed to be unchanged
release-era documentation. An older release without a guide remains represented
by its [release evidence](release-evidence.md), not a fabricated snapshot.

Development documentation appears under `versions/next/`, with a visible label.
It preserves the stable default and cannot advance it merely because `main`
changed. History and RC evidence remain in [History And Maintenance](history.md)
and stay out of default user search.

Package versions (for example `1.6.0`) and `DatasetSpec` schema versions (currently
`1.1`) are distinct. Consult [DatasetSpec compatibility](concepts/dataset-spec-compatibility.md)
before changing a saved specification. See [Downloads](downloads.md) for portable
copies and [Publishing Documentation](development/documentation.md) for updates.
