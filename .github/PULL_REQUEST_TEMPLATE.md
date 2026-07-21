## Summary

-

## Safety Checklist

- [ ] The change does not copy source rows into generated output.
- [ ] The change does not expose raw PII, secrets, or production data.
- [ ] Trino-facing changes keep SQL read-only, allowlisted, and bounded.
- [ ] Generated data remains reproducible when a seed is supplied.
- [ ] New fixtures, examples, logs, and docs use synthetic data only.

## Validation

- [ ] `python3 -m ruff check src tests scripts`
- [ ] `python3 -m compileall -q src tests scripts`
- [ ] `python3 -m pytest`
- [ ] `scripts/check_release.sh`

Explain any unchecked item:

-
