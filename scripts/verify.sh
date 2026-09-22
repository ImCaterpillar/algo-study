#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_PYTHON="${PYTHON_BIN:-python}"
NPM_REGISTRY="${NPM_REGISTRY:-https://registry.npmjs.org/}"
SKIP_INSTALL="${SKIP_INSTALL:-false}"

cd "$ROOT_DIR"
if grep -R "applied-caas\|internal.api.openai\|artifactory" -n frontend/package-lock.json frontend/.npmrc .npmrc 2>/dev/null; then
  echo "发现内部 npm registry 残留，请运行 scripts/fix-npm-registry.ps1 或重新生成 package-lock.json。" >&2
  exit 1
fi

if [[ -x "$ROOT_DIR/backend/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/backend/.venv/bin/python"
elif [[ -x "$ROOT_DIR/backend/.venv/Scripts/python.exe" ]]; then
  PYTHON_BIN="$ROOT_DIR/backend/.venv/Scripts/python.exe"
else
  "$BASE_PYTHON" -m venv "$ROOT_DIR/backend/.venv"
  if [[ -x "$ROOT_DIR/backend/.venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT_DIR/backend/.venv/bin/python"
  else
    PYTHON_BIN="$ROOT_DIR/backend/.venv/Scripts/python.exe"
  fi
fi

if [[ "$SKIP_INSTALL" != "true" ]]; then
  "$PYTHON_BIN" -m pip install -r "$ROOT_DIR/backend/requirements.txt" -r "$ROOT_DIR/backend/requirements-dev.txt"
fi

cd "$ROOT_DIR/backend"
"$PYTHON_BIN" -m compileall -q app
"$PYTHON_BIN" smoke_test.py
"$PYTHON_BIN" regression_test.py

cd "$ROOT_DIR/frontend"
npm config set registry "$NPM_REGISTRY"
if [[ ! -d node_modules || "$SKIP_INSTALL" != "true" ]]; then
  npm ci --registry="$NPM_REGISTRY"
fi
npm audit --omit=dev --registry="$NPM_REGISTRY"
npm run build
