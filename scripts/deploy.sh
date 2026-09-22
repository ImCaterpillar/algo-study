#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
ENV_EXAMPLE="$ROOT_DIR/.env.deploy.example"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

usage() {
  cat <<'USAGE'
AlgoStudy 一键 Docker 部署脚本

用法：
  ./scripts/deploy.sh                 构建并启动服务
  ./scripts/deploy.sh --build         强制重新构建并启动
  ./scripts/deploy.sh --enable-code-exec  构建代码执行运行时并开启代码执行
  ./scripts/deploy.sh --port 8088     指定前端访问端口
  ./scripts/deploy.sh --npm-registry https://registry.npmmirror.com/  指定前端镜像构建 npm 源
  ./scripts/deploy.sh --status        查看服务状态
  ./scripts/deploy.sh --logs          查看实时日志
  ./scripts/deploy.sh --down          停止服务
  ./scripts/deploy.sh --help          显示帮助

部署完成后访问：
  http://127.0.0.1:8080
  http://127.0.0.1:8080/health
  http://127.0.0.1:8080/docs
USAGE
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

compose() {
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

set_env_value() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i.bak "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
  else
    printf '\n%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

generate_secret() {
  if command_exists python3; then
    python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
  elif command_exists python; then
    python - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
  elif command_exists openssl; then
    openssl rand -base64 48 | tr -d '\n'
    printf '\n'
  else
    printf 'change-this-secret-key-manually-%s\n' "$(date +%s)"
  fi
}

ensure_env_file() {
  if [[ ! -f "$ENV_FILE" ]]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo "已创建 .env 部署配置文件。"
  fi

  local current_secret
  current_secret="$(grep -E '^SECRET_KEY=' "$ENV_FILE" | head -n1 | cut -d= -f2- || true)"
  if [[ -z "$current_secret" || "$current_secret" == "change-me-before-deploy" || "$current_secret" == "dev-secret-key-change-me" ]]; then
    set_env_value "SECRET_KEY" "$(generate_secret)"
    echo "已自动生成 SECRET_KEY。"
  fi
}

wait_for_health() {
  local port="$1"
  local url="http://127.0.0.1:${port}/health"
  echo "正在等待服务健康检查：${url}"
  for _ in $(seq 1 60); do
    if command_exists curl && curl -fsS "$url" >/dev/null 2>&1; then
      echo "服务已就绪。"
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
      echo "服务已就绪。"
      return 0
    fi
    sleep 2
  done

  echo "健康检查未在预期时间内通过，请查看日志：./scripts/deploy.sh --logs" >&2
  return 1
}

ACTION="up"
FORCE_BUILD="false"
ENABLE_CODE_EXEC="false"
CUSTOM_PORT=""
CUSTOM_NPM_REGISTRY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build)
      FORCE_BUILD="true"
      shift
      ;;
    --enable-code-exec)
      ENABLE_CODE_EXEC="true"
      shift
      ;;
    --port)
      CUSTOM_PORT="${2:-}"
      if [[ -z "$CUSTOM_PORT" ]]; then
        echo "--port 需要端口号。" >&2
        exit 1
      fi
      shift 2
      ;;
    --npm-registry)
      CUSTOM_NPM_REGISTRY="${2:-}"
      if [[ -z "$CUSTOM_NPM_REGISTRY" ]]; then
        echo "--npm-registry 需要 registry 地址。" >&2
        exit 1
      fi
      shift 2
      ;;
    --status)
      ACTION="status"
      shift
      ;;
    --logs)
      ACTION="logs"
      shift
      ;;
    --down)
      ACTION="down"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "未知参数：$1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command_exists docker; then
  echo "未检测到 Docker。请先安装 Docker Desktop 或 Docker Engine。" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "未检测到 Docker Compose v2。请升级 Docker，确保支持 'docker compose' 命令。" >&2
  exit 1
fi

ensure_env_file

if [[ -n "$CUSTOM_PORT" ]]; then
  if ! [[ "$CUSTOM_PORT" =~ ^[0-9]+$ ]] || (( CUSTOM_PORT < 1 || CUSTOM_PORT > 65535 )); then
    echo "端口号无效：$CUSTOM_PORT" >&2
    exit 1
  fi
  set_env_value "APP_PORT" "$CUSTOM_PORT"
  set_env_value "CORS_ORIGINS" "http://localhost:${CUSTOM_PORT},http://127.0.0.1:${CUSTOM_PORT}"
fi

if [[ -n "$CUSTOM_NPM_REGISTRY" ]]; then
  set_env_value "NPM_REGISTRY" "$CUSTOM_NPM_REGISTRY"
fi

if [[ "$ENABLE_CODE_EXEC" == "true" ]]; then
  set_env_value "CODE_EXECUTION_ENABLED" "true"
  set_env_value "INSTALL_CODE_RUNNERS" "true"
  echo "已开启代码执行，并将在镜像中安装 Node.js / g++ / JDK 运行时。"
fi

APP_PORT="$(grep -E '^APP_PORT=' "$ENV_FILE" | head -n1 | cut -d= -f2- || echo 8080)"

case "$ACTION" in
  status)
    compose ps
    ;;
  logs)
    compose logs -f --tail=200
    ;;
  down)
    compose down
    echo "服务已停止。数据仍保存在 Docker volume：algo-study_algo_study_data"
    ;;
  up)
    if [[ "$FORCE_BUILD" == "true" || "$ENABLE_CODE_EXEC" == "true" ]]; then
      compose up -d --build
    else
      compose up -d
    fi
    wait_for_health "$APP_PORT"
    cat <<MSG

AlgoStudy 部署完成：
  前端：http://127.0.0.1:${APP_PORT}
  健康检查：http://127.0.0.1:${APP_PORT}/health
  API 文档：http://127.0.0.1:${APP_PORT}/docs

常用命令：
  查看状态：./scripts/deploy.sh --status
  查看日志：./scripts/deploy.sh --logs
  停止服务：./scripts/deploy.sh --down
MSG
    ;;
esac
