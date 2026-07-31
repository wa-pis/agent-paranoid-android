# Public Contract Fixtures

These fixtures freeze representative, row-free public JSON contracts:

- CLI agent planning;
- MCP planning and generation responses;
- `DatasetSpec`;
- advisor exchange;
- generation manifest metadata.

They contain only synthetic or safe metadata. Generated rows, raw PII,
credentials, secrets, temporary paths, random plan IDs, and package-version
churn are excluded or normalized.

After an intentional compatible or breaking contract change, review the diff
and regenerate the fixtures:

```bash
python3 scripts/update_contract_fixtures.py
```

An unexpected fixture diff is a compatibility failure, not an automatic
snapshot update.

`contract-catalog.json` assigns a contract version and change rule to every
other fixture:

- `additive_only` permits optional, backward-compatible additions; removal,
  rename, narrowing, required fields, and semantic changes are breaking.
- `schema_versioned` requires the serialized contract's version and migration
  policy to change when compatibility is broken.

Every public fixture must be registered. The contract test rejects an
unversioned fixture or a stale catalog entry.
