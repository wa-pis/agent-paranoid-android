# Tasks

- [x] Inventory supported source acquisition and output adapters; publish transition matrix.
- [x] Add source × output regression coverage with all field types and complete reviewed specifications.
- [x] Close SQL reload, typed/null business-rule and multi-entity profile gaps.
- [x] Verify distribution/settings/mode/rule parity, privacy, budgets and legacy compatibility.
- [x] Update documentation, schemas/contracts and run strict OpenSpec plus full project gates.


## Evidence

- `tests/test_source_output_matrix.py`: 200 source × output × mode combinations
  plus four multi-entity profile output cases. Each reviewed specification
  contains all seven field types, native constraints and embedded rules.
- Full `scripts/check_release.sh`: 3670 passed, 23 skipped, 91.26% coverage;
  lint, types, licenses/dependency policy, operational budgets, schema freshness
  and quickstart passed. Only fictional fixtures were used.
- Subsequent expanded exact aggregate/output regressions:
  `tests/test_universal_business_rules.py`, 43 passed (including nine additional
  output cases; no runtime changes after the full gate).
- Minimum compatibility: Python 3.11, Pydantic 2.7, PyArrow 15, SQLGlot 30 and
  minimum provider SDKs: 414 passed across both provider suites, specification,
  business rules, source/output matrix and scalar artifact suites. Provider
  transports are fictional; no provider calls or live database access occurred.
- Documentation/contract tests: 54 passed; strict MkDocs build passed.
- Targeted strict OpenSpec validation passed. Whole-repository strict validation
  additionally exposed two existing missing-scenario examples; the validation
  requirement and change template now contain explicit scenarios.

Compatibility fix: replace unsupported `Field(exclude_if=...)` with bounded
per-model serializers, retaining absent-optional-field fingerprints and making
provider JSON schemas serializable on the declared minimum Pydantic.

CSV manifests and Parquet field metadata explicitly mark new scalar encodings;
legacy unmarked inputs keep their prior interpretation. Direct consumers need
these markers for logical round trips. This work does not authorize a release,
source retention, database access or transformation activation.
