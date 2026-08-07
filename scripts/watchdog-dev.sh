#!/usr/bin/env bash
# 看门狗：后端 8010 + 前端 5173 掉线自动拉起（独立进程，不依赖 Cursor Agent）
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/.output/logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
WATCH_LOG="$LOG_DIR/watchdog.log"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$WATCH_LOG"; }

backend_up() { curl -sf -m 2 "http://127.0.0.1:8010/api/health" >/dev/null 2>&1; }
frontend_up() { curl -sf -m 2 "http://127.0.0.1:5173/" >/dev/null 2>&1; }

start_backend() {
  if backend_up; then return 0; fi
  # 清端口占用
  for pid in $(lsof -nP -t -iTCP:8010 -sTCP:LISTEN 2>/dev/null || true); do kill -9 "$pid" 2>/dev/null || true; done
  log "starting backend :8010"
  (
    cd "$ROOT" || exit 1
    # shellcheck disable=SC1091
    source .venv/bin/activate
    cd backend || exit 1
    PYTHONPATH=.. exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8010
  ) >>"$BACKEND_LOG" 2>&1 &
  disown 2>/dev/null || true
}

start_frontend() {
  if frontend_up; then return 0; fi
  for pid in $(lsof -nP -t -iTCP:5173 -sTCP:LISTEN 2>/dev/null || true); do kill -9 "$pid" 2>/dev/null || true; done
  log "starting frontend :5173"
  (
    cd "$ROOT/frontend" || exit 1
    exec npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
  ) >>"$FRONTEND_LOG" 2>&1 &
  disown 2>/dev/null || true
}

log "watchdog started root=$ROOT"
while true; do
  backend_up || start_backend
  frontend_up || start_frontend
  sleep 4
done
