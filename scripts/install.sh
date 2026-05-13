#!/usr/bin/env bash
set -euo pipefail

PACKAGE="${PACKAGE:-@company/agent-harness}"

if ! command -v node >/dev/null 2>&1; then
  echo "node is required to install ${PACKAGE}" >&2
  exit 1
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required to install ${PACKAGE}" >&2
  exit 1
fi

npx "${PACKAGE}" setup "$@"
