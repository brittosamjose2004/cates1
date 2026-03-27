#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/brittosamjose2004/cates.git"
BRANCH="copilot/osm-location-pipeline"
APP_DIR="$HOME/cates"
PORT="8000"

echo "[INFO] Host: $(hostname) User: $(whoami)"

if [ ! -d "$APP_DIR/.git" ]; then
  echo "[INFO] Cloning repository to $APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

echo "[INFO] Fetching latest code"
git fetch origin

if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  git checkout -B "$BRANCH" "origin/$BRANCH"
  git reset --hard "origin/$BRANCH"
else
  echo "[WARN] Branch $BRANCH not found; falling back to origin/main"
  git checkout -B main origin/main
  git reset --hard origin/main
fi

echo "[INFO] Stopping existing app processes"
if command -v pm2 >/dev/null 2>&1; then
  pm2 list || true
  pm2 delete all || true
fi

if command -v systemctl >/dev/null 2>&1; then
  systemctl stop cates.service 2>/dev/null || true
  systemctl stop caties.service 2>/dev/null || true
  systemctl stop uvicorn.service 2>/dev/null || true
fi

pkill -f "uvicorn backend.api.main:app" || true
pkill -f "python -m uvicorn" || true
fuser -k "${PORT}/tcp" 2>/dev/null || true

echo "[INFO] Preparing Python environment"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
if [ -f backend/requirements.txt ]; then
  pip install -r backend/requirements.txt
fi

echo "[INFO] Starting application on port ${PORT}"
nohup .venv/bin/python -m uvicorn backend.api.main:app --host 0.0.0.0 --port "$PORT" > "$APP_DIR/uvicorn.log" 2>&1 &
sleep 4

echo "[INFO] Running health checks"
if curl -sf "http://127.0.0.1:${PORT}/docs" >/dev/null; then
  echo "[SUCCESS] Deployment complete. FastAPI docs reachable on port ${PORT}."
else
  echo "[WARN] App started but /docs check failed. Tail logs:"
  tail -n 80 "$APP_DIR/uvicorn.log" || true
fi

echo "[INFO] Active process on port ${PORT}:"
ss -ltnp | grep ":${PORT}" || true
