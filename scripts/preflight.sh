#!/usr/bin/env bash
# Thin wrapper around scripts/preflight_live_budget.py
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python "$ROOT/scripts/preflight_live_budget.py" "$@"
