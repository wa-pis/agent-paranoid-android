#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export POSTGRES_EXAMPLE_USE_QUERY=true
exec "$ROOT/run.sh" "$@"
