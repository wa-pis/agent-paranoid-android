#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="${1:-$ROOT/out}"
PORT="${POSTGRES_EXAMPLE_PORT:-55432}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/apa-postgres-example.XXXXXX")"
DATA="$WORK/data"
LOG="$WORK/postgres.log"

if [[ -e "$OUTPUT" ]]; then
  echo "Output already exists: $OUTPUT" >&2
  exit 2
fi

for command in initdb pg_ctl psql; do
  if ! command -v "$command" >/dev/null; then
    echo "Required command is unavailable: $command" >&2
    exit 2
  fi
done

if [[ -n "${TDA_PYTHON:-}" ]]; then
  CLI=("$TDA_PYTHON" -m test_data_agent.cli)
  PYTHON="$TDA_PYTHON"
else
  CLI=(test-data-agent)
  PYTHON=python3
fi

cleanup() {
  pg_ctl -D "$DATA" -m fast -w stop >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

initdb -D "$DATA" --no-locale --encoding=UTF8 --auth=trust >/dev/null
pg_ctl -D "$DATA" -l "$LOG" -o "-p $PORT -h 127.0.0.1" -w start >/dev/null

psql -h 127.0.0.1 -p "$PORT" -d postgres -v ON_ERROR_STOP=1 \
  -c 'CREATE DATABASE apa_source;' \
  -c 'CREATE DATABASE apa_target;' \
  -c 'CREATE ROLE apa_reader LOGIN;' >/dev/null
psql -h 127.0.0.1 -p "$PORT" -d apa_source -v ON_ERROR_STOP=1 \
  -f "$ROOT/source.sql" >/dev/null

if psql -h 127.0.0.1 -p "$PORT" -U apa_reader -d apa_source \
  -v ON_ERROR_STOP=1 \
  -c "INSERT INTO public.customers VALUES (99, 'active', '2026-08-11');" \
  >/dev/null 2>&1; then
  echo "Read-only profiling role unexpectedly accepted INSERT" >&2
  exit 1
fi

mkdir -p "$OUTPUT"
export POSTGRES_SOURCE_ID=warehouse
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT="$PORT"
export POSTGRES_DATABASE=apa_source
export POSTGRES_USER=apa_reader
export POSTGRES_SSLMODE=disable
export POSTGRES_ALLOW_INSECURE=true
export POSTGRES_ALLOWED_SCHEMAS=public
export POSTGRES_ALLOWED_TABLES=public.customers,public.orders
export POSTGRES_ALLOWED_COLUMNS=public.customers.customer_id,public.customers.status,public.customers.joined_on,public.orders.order_id,public.orders.customer_id,public.orders.state,public.orders.amount,public.orders.expedited
export POSTGRES_MAX_TABLES=2
export POSTGRES_MAX_COLUMNS=8
export POSTGRES_MAX_STATEMENTS=100
export POSTGRES_MAX_RESULT_ROWS=500
export POSTGRES_MAX_RESULT_CELLS=5000
export POSTGRES_MAX_SECONDS=30

"${CLI[@]}" profile-postgres \
  --local-category warehouse.public.orders.state \
  --output "$OUTPUT/profile.json"
"${CLI[@]}" infer-spec "$OUTPUT/profile.json" \
  --output "$OUTPUT/dataset_spec.yaml"
"${CLI[@]}" generate "$OUTPUT/dataset_spec.yaml" \
  --seed 12345 --output "$OUTPUT/generated"
"${CLI[@]}" validate "$OUTPUT/dataset_spec.yaml" "$OUTPUT/generated"
"${CLI[@]}" export-postgres-sql "$OUTPUT/dataset_spec.yaml" \
  --seed 12345 --output "$OUTPUT/generated.sql"
"${CLI[@]}" export-postgres-sql "$OUTPUT/dataset_spec.yaml" \
  --seed 12345 --output "$OUTPUT/generated-second.sql"
cmp "$OUTPUT/generated.sql" "$OUTPUT/generated-second.sql"

"$PYTHON" - "$OUTPUT/profile.json" <<'PY'
import json
import sys

profile = json.load(open(sys.argv[1], encoding="utf-8"))
entities = {entity["name"]: entity for entity in profile["entities"]}
orders = {field["name"]: field for field in entities["warehouse.public.orders"]["fields"]}
customers = {field["name"]: field for field in entities["warehouse.public.customers"]["fields"]}
values = {item["value"] for item in orders["state"]["distribution"]["categories"]}
assert values == {"new", "paid", "shipped"}
assert customers["status"]["distribution"] == {}
PY

psql -h 127.0.0.1 -p "$PORT" -d apa_target -v ON_ERROR_STOP=1 \
  -f "$OUTPUT/generated.sql" >/dev/null

COUNTS="$(psql -h 127.0.0.1 -p "$PORT" -d apa_target -At -v ON_ERROR_STOP=1 \
  -c 'SELECT (SELECT count(*) FROM "warehouse.public.customers"), (SELECT count(*) FROM "warehouse.public.orders"), (SELECT count(*) FROM "warehouse.public.orders" o LEFT JOIN "warehouse.public.customers" c ON c.customer_id = o.customer_id WHERE c.customer_id IS NULL);')"
if [[ "$COUNTS" != "3|4|0" ]]; then
  echo "Unexpected target counts or foreign-key coverage: $COUNTS" >&2
  exit 1
fi

POLICY="$(psql -h 127.0.0.1 -p "$PORT" -d apa_target -At -v ON_ERROR_STOP=1 \
  -c "SELECT bool_and(state = ANY (ARRAY['new','paid','shipped'])) FROM \"warehouse.public.orders\";" \
  -c "SELECT bool_and(status LIKE 'syn_%') FROM \"warehouse.public.customers\";")"
if [[ "$POLICY" != $'t\nt' ]]; then
  echo "Selective local-value policy check failed" >&2
  exit 1
fi

echo "Disposable PostgreSQL example complete: $OUTPUT"
echo "Target rows: customers=3, orders=4; foreign-key violations=0"
