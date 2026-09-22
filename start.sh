#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
: "${NPM_REGISTRY:=https://registry.npmjs.org/}"

echo "[algo-study] 一键启动 AlgoStudy"
echo "[algo-study] 项目目录：$ROOT_DIR"
echo "[algo-study] npm registry：$NPM_REGISTRY"

if [[ -x "$ROOT_DIR/scripts/fix-npm-registry.sh" ]]; then
  "$ROOT_DIR/scripts/fix-npm-registry.sh" "$NPM_REGISTRY" || true
fi

BACKEND_PORT="${BACKEND_PORT:-8000}" FRONTEND_PORT="${FRONTEND_PORT:-5173}" NPM_REGISTRY="$NPM_REGISTRY" "$ROOT_DIR/scripts/deploy-local.sh"
