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

"${CLI[@]}" profile-csv "$ROOT/customers.csv" \
  --table customers \
  --output "$OUTPUT/profile.json"

"${CLI[@]}" infer-spec "$OUTPUT/profile.json" \
  --count 25 \
  --output "$OUTPUT/dataset_spec.yaml"

"${CLI[@]}" generate "$OUTPUT/dataset_spec.yaml" \
  --seed 12345 \
  --format csv \
  --output "$OUTPUT/generated"

"${CLI[@]}" validate "$OUTPUT/dataset_spec.yaml" "$OUTPUT/generated" \
  --output "$OUTPUT/revalidation_report.json"

echo "CSV quickstart complete: $OUTPUT"
