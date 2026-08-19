#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export TRINO_EXAMPLE_USE_QUERY=true
exec "$ROOT/run.sh" "$@"
