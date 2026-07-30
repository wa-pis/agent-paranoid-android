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
