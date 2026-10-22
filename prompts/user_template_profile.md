Generate synthetic test data from an existing safe metadata-only profile.

* profile path: {profile_path}
* fresh agent workspace: {workspace_path}
* requested count: {count}
* output format: {csv/json/parquet}
* mode: {valid/mixed/negative}
* invalid ratio: {invalid_ratio}
* seed: {seed}

Use the installed profile planner without reconnecting to the original source.
Do not assume missing statistics, decimal bounds or derived SQL relationships
are known. If automatic inference is unsupported, explain the gap and prepare
an explicit reviewable specification rather than guessing source evidence.
Show the DatasetSpec and its fingerprint, then stop for my explicit human
approval of that exact version. Generate and validate only after approval.
Return paths and bounded manifest/validation facts;
do not return source or generated rows in chat.
