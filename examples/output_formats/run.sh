#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="${1:-$ROOT/out}"

if [[ -e "$OUTPUT" ]]; then
  echo "Output already exists: $OUTPUT" >&2
  exit 2
fi

if [[ -n "${TDA_PYTHON:-}" ]]; then
  CLI=("$TDA_PYTHON" -m test_data_agent.cli)
else
  CLI=(test-data-agent)
fi

for format in csv json sql parquet; do
  "${CLI[@]}" generate "$ROOT/dataset_spec.yaml" \
    --seed 271828 \
    --format "$format" \
    --output "$OUTPUT/$format"
done

"${CLI[@]}" export-postgres-sql "$ROOT/dataset_spec.yaml" \
  --seed 271828 \
  --output "$OUTPUT/postgres.sql"

echo "Output-format example complete: $OUTPUT"
