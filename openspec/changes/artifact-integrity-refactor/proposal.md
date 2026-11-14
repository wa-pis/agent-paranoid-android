# Bind reviewed sources and published artifacts

Bind CSV planning and full-row reuse checks to the bytes read. Bind legacy and
scalable completion checkpoints to their manifest. Check shared Parquet
expanded-byte and cell limits before decoding a file.

Previously completed results remain readable. Interrupted workspaces without a
manifest-bound checkpoint must be replanned. CSV digest framing is unchanged.
