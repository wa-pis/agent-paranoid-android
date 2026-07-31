# Design: agent-input-detection

`detect_agent_source_type` resolves the source and applies narrow rules:

- a regular `.csv` file is a single CSV source;
- a directory with at least one regular `.csv` file is a CSV-folder source;
- a `.json` file is parsed through `load_profile_or_spec` and accepted only
  when it validates as safe profile metadata.

DatasetSpec JSON/YAML, unsupported paths, and empty folders produce actionable
errors. Supplying `--source-type` bypasses detection but not the existing
source validation and safety checks.
