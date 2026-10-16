# Evidence and decisions

- RC4 folder overwrite, edge/load support and mode choices are implemented. Verify incorrect mode diagnostics when saved invalid_ratio conflicts with an explicit mode override; CSV help still hides choices behind MODE.
- Negative floor(log10(abs(x))) is the correct magnitude below one. Clamping or dropping small values is not a fix. Add coarse prevalence metadata without source values.
- Decimal metadata is already extracted by legacy declared-type parsing and Parquet; validate Trino raw-type propagation specifically. Automatic exact extrema inference remains prohibited; provide reviewed synthetic ranges with explicit recovery guidance.
- Privacy defaults intentionally reject ambiguous decimal phone/card/secret-looking values. A narrow explicit numeric_measure semantic, vetoed by sensitive identity/name/policy, allows synthetic high-scale amounts without granting source-row access.
- Formula assignment and validation both exist; arbitrary formulas cannot be judged for business intent. Separate check-only mode and report assignment counts rather than claiming semantic correctness.
- Distribution limits are generation parameters historically; new post-rule checks must cover changed numeric values without falsely asserting the source distribution was preserved.
- Exact decimal native constraints/rounding, EAV reshaping, unrestricted JOINs, raw dictionary names and automatic sensitivity declassification are not silently enabled by feedback.
