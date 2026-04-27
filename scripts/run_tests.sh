#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Missing .venv. Please run ./scripts/setup_test_env.sh first."
  exit 1
fi

source .venv/bin/activate
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python scripts/run_tests.py "$@"
