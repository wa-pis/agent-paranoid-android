#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "==> Lint"
python3 -m ruff check src tests scripts

echo "==> Compile"
python3 -m compileall -q src tests scripts

echo "==> Tests with coverage"
python3 -m pytest --cov=test_data_agent --cov-report=term-missing --cov-fail-under=85

echo "==> DatasetSpec schema freshness"
python3 scripts/export_dataset_schema.py "$TMP_DIR/dataset_spec.schema.json"
python3 - "$TMP_DIR/dataset_spec.schema.json" schemas/dataset_spec.schema.json <<'PY'
import pathlib
import sys

generated = pathlib.Path(sys.argv[1]).read_text()
checked_in = pathlib.Path(sys.argv[2]).read_text()
if generated != checked_in:
    raise SystemExit("checked-in DatasetSpec schema is stale; run scripts/export_dataset_schema.py")
PY

echo "==> Quickstart smoke"
python3 -m test_data_agent.cli generate-from-example tests/fixtures/example_dataset \
  --count 25 \
  --seed 12345 \
  --format csv \
  --output "$TMP_DIR/generated"

python3 - "$TMP_DIR/generated/generation_manifest.json" "$TMP_DIR/generated/validation_report.json" <<'PY'
import json
import pathlib
import sys

manifest = json.loads(pathlib.Path(sys.argv[1]).read_text())
report = json.loads(pathlib.Path(sys.argv[2]).read_text())

checks = {
    "synthetic flag": manifest.get("synthetic") is True,
    "source-row flag": manifest.get("source_rows_copied") is False,
    "validation flag": manifest.get("validation_valid") is True,
    "seed": manifest.get("seed") == 12345,
    "row counts": manifest.get("row_counts") == {"customers": 25, "orders": 25},
    "validation report": report.get("valid") is True,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit(f"quickstart smoke failed: {', '.join(failed)}")
PY

echo "Release checks passed."
