#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/wangxinyu/Downloads/开发规范包_V2"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
cd backend
export PYTHONPATH=..
exec python -m uvicorn src.main:app --host 127.0.0.1 --port 8010
