#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

python3 -m venv .venv
source .venv/bin/activate

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pip install -r requirements-dev.txt

echo "Test environment is ready."
echo "Run all tests: ./scripts/run_tests.sh"
echo "Run selected cases: ./scripts/run_tests.sh addexample studentexample"
