#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
NPM_REGISTRY="${NPM_REGISTRY:-https://registry.npmjs.org/}"

usage() {
  cat <<'USAGE'
AlgoStudy 本地一键运行脚本（不依赖 Docker）

用法：
  ./scripts/deploy-local.sh

可选环境变量：
  BACKEND_PORT=8000 FRONTEND_PORT=5173 ./scripts/deploy-local.sh
  NPM_REGISTRY=https://registry.npmmirror.com ./scripts/deploy-local.sh

启动后访问：
  http://127.0.0.1:5173
  http://127.0.0.1:8000/health
  http://127.0.0.1:8000/docs
USAGE
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

generate_secret() {
  if command_exists python3; then
    python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
  else
    python - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
  fi
}

ensure_backend_env() {
  if [[ ! -f "$BACKEND_DIR/.env" ]]; then
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  fi
  if grep -q '^SECRET_KEY=replace-with-a-long-random-secret' "$BACKEND_DIR/.env" || grep -q '^SECRET_KEY=dev-secret-key-change-me' "$BACKEND_DIR/.env"; then
    local secret
    secret="$(generate_secret)"
    sed -i.bak "s|^SECRET_KEY=.*|SECRET_KEY=${secret}|" "$BACKEND_DIR/.env"
    rm -f "$BACKEND_DIR/.env.bak"
  fi

  local cors_origins="http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}"
  if grep -q '^CORS_ORIGINS=' "$BACKEND_DIR/.env"; then
    sed -i.bak "s|^CORS_ORIGINS=.*|CORS_ORIGINS=${cors_origins}|" "$BACKEND_DIR/.env"
    rm -f "$BACKEND_DIR/.env.bak"
  else
    printf '\nCORS_ORIGINS=%s\n' "$cors_origins" >> "$BACKEND_DIR/.env"
  fi
}

ensure_frontend_env() {
  if [[ ! -f "$FRONTEND_DIR/.env" ]]; then
    cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"
  fi
  if grep -q '^VITE_API_BASE_URL=' "$FRONTEND_DIR/.env"; then
    sed -i.bak "s|^VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://${BACKEND_HOST}:${BACKEND_PORT}/api|" "$FRONTEND_DIR/.env"
    rm -f "$FRONTEND_DIR/.env.bak"
  else
    printf '\nVITE_API_BASE_URL=http://%s:%s/api\n' "$BACKEND_HOST" "$BACKEND_PORT" >> "$FRONTEND_DIR/.env"
  fi
}

wait_for_backend() {
  local url="http://${BACKEND_HOST}:${BACKEND_PORT}/health"
  echo "正在等待后端启动：${url}"
  for _ in $(seq 1 60); do
    if command_exists curl && curl -fsS "$url" >/dev/null 2>&1; then
      echo "后端已就绪。"
      return 0
    fi
    if command_exists python3 && python3 - "$url" >/dev/null 2>&1 <<'PY'
import sys
import urllib.request
try:
    urllib.request.urlopen(sys.argv[1], timeout=2).read()
except Exception:
    raise SystemExit(1)
PY
    then
      echo "后端已就绪。"
      return 0
    fi
    sleep 1
  done
  echo "后端健康检查失败。" >&2
  return 1
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if ! command_exists python3 && ! command_exists python; then
  echo "未检测到 Python。" >&2
  exit 1
fi
if ! command_exists npm; then
  echo "未检测到 npm。请先安装 Node.js。" >&2
  exit 1
fi

PYTHON_BIN="$(command -v python3 || command -v python)"
ensure_backend_env
ensure_frontend_env

if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
  "$PYTHON_BIN" -m venv "$BACKEND_DIR/.venv"
fi

# shellcheck disable=SC1091
source "$BACKEND_DIR/.venv/bin/activate"
pip install -r "$BACKEND_DIR/requirements.txt"

deactivate

cd "$FRONTEND_DIR"
npm config set registry "$NPM_REGISTRY"
npm install --registry="$NPM_REGISTRY"

cleanup() {
  echo
  echo "正在停止本地服务..."
  if [[ -n "${BACKEND_PID:-}" ]]; then kill "$BACKEND_PID" >/dev/null 2>&1 || true; fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then kill "$FRONTEND_PID" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT INT TERM

cd "$BACKEND_DIR"
"$BACKEND_DIR/.venv/bin/uvicorn" app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" &
BACKEND_PID=$!

wait_for_backend

cat <<MSG

AlgoStudy 本地服务已启动：
  前端：http://127.0.0.1:${FRONTEND_PORT}
  后端：http://${BACKEND_HOST}:${BACKEND_PORT}
  API 文档：http://${BACKEND_HOST}:${BACKEND_PORT}/docs

按 Ctrl+C 停止前后端。
MSG

cd "$FRONTEND_DIR"
VITE_API_BASE_URL="http://${BACKEND_HOST}:${BACKEND_PORT}/api" npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

wait "$FRONTEND_PID"
