#!/usr/bin/env bash
# 在「你自己的」Cursor 终端里运行；与后端分两个终端。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"
echo "Starting frontend on http://localhost:5173  (Ctrl+C 停止)"
echo "API 经 Vite 代理到 http://127.0.0.1:8010"
exec npm run dev
