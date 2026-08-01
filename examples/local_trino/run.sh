#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="${1:-$ROOT/out}"
PORT="${TRINO_EXAMPLE_PORT:-18080}"
CONTAINER="agent-paranoid-trino-example-$$"
IMAGE="trinodb/trino:483@sha256:db58cc93e593a2706553745f276bb119c9810e69918be56ecde088ba7ccb0534"

if [[ -e "$OUTPUT" ]]; then
  echo "Output already exists: $OUTPUT" >&2
  exit 2
fi

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker run --detach --rm \
  --name "$CONTAINER" \
  --publish "127.0.0.1:$PORT:8080" \
  "$IMAGE" >/dev/null

for _ in $(seq 1 60); do
  if [[ "$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER")" == "healthy" ]]; then
    break
  fi
  sleep 2
done

if [[ "$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER")" != "healthy" ]]; then
  echo "Disposable Trino did not become healthy" >&2
  exit 1
fi

TRINO_HOST=localhost \
TRINO_PORT="$PORT" \
TRINO_USER=synthetic_example \
TRINO_HTTP_SCHEME=http \
TRINO_ALLOW_INSECURE_HTTP=true \
TRINO_ALLOWED_CATALOGS=tpch \
TRINO_ALLOWED_SCHEMAS=tiny \
TRINO_MAX_RESULT_ROWS=100 \
TRINO_QUERY_MAX_EXECUTION_TIME=30s \
TRINO_QUERY_MAX_RUN_TIME=45s \
TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES=64MB \
  python3 "$ROOT/run.py" "$OUTPUT"
