#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POSTGRES_EXAMPLE_USE_WILDCARD=true exec "$ROOT/run.sh" "$@"
