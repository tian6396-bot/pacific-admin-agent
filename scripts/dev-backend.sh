#!/usr/bin/env bash
# 在「你自己的」Cursor 终端里运行本脚本，不要让 Agent 后台代启（会被系统清掉）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
cd backend
PORT="${PORT:-8010}"
echo "Starting backend on http://127.0.0.1:${PORT}  (Ctrl+C 停止)"
echo "Health: http://127.0.0.1:${PORT}/api/health"
exec env PYTHONPATH=.. python -m uvicorn src.main:app --reload --host 0.0.0.0 --port "$PORT"
