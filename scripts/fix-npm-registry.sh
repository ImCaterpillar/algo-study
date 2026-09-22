#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
REGISTRY="${1:-${NPM_REGISTRY:-https://registry.npmjs.org/}}"

if ! command -v npm >/dev/null 2>&1; then
  echo "未检测到 npm。请先安装 Node.js。" >&2
  exit 1
fi

npm config set registry "$REGISTRY"
printf 'registry=%s\nfund=false\naudit=true\n' "$REGISTRY" > "$FRONTEND_DIR/.npmrc"

if [[ -f "$FRONTEND_DIR/package-lock.json" ]]; then
  python - "$FRONTEND_DIR/package-lock.json" "$REGISTRY" <<'PY'
from pathlib import Path
import re
import sys
path = Path(sys.argv[1])
registry = sys.argv[2]
text = path.read_text(encoding='utf-8')
text = text.replace('https://packages.applied-caas-gateway1.internal.api.openai.org/artifactory/api/npm/npm-public/', registry)
text = re.sub(r'https://[^"\s]+/artifactory/api/npm/npm-public/', registry, text)
path.write_text(text, encoding='utf-8')
PY
fi

echo "npm registry 已设置为：$REGISTRY"
echo "已修复 frontend/.npmrc 和 frontend/package-lock.json。"
echo "现在可以运行：cd frontend && npm install --registry $REGISTRY"
