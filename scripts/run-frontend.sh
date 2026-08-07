#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/wangxinyu/Downloads/开发规范包_V2"
cd "$ROOT/frontend"
exec npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
