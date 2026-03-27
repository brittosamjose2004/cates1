#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/brittosamjose2004/cates.git"
APP_DIR="$HOME/app"
PORT="8000"

echo "[INFO] Host: $(hostname) User: $(whoami)"

if [ ! -d "$APP_DIR/.git" ]; then
  echo "[INFO] Cloning repository to $APP_DIR"
  rm -rf "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

echo "[INFO] Syncing main branch"
git fetch origin
git checkout main
git reset --hard origin/main

echo "[INFO] Stopping old app/processes"
if command -v pm2 >/dev/null 2>&1; then
  pm2 delete all || true
fi
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl stop cates.service 2>/dev/null || true
  sudo systemctl stop caties.service 2>/dev/null || true
  sudo systemctl stop uvicorn.service 2>/dev/null || true
fi
pkill -f "uvicorn backend.api.main:app" || true
pkill -f "python -m uvicorn" || true
fuser -k "${PORT}/tcp" 2>/dev/null || true

echo "[INFO] Setting up environment"
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
if [ -f backend/requirements.txt ]; then
  pip install -r backend/requirements.txt
fi

echo "[INFO] Starting app from main"
nohup "$APP_DIR/venv/bin/python" -m uvicorn backend.api.main:app --host 0.0.0.0 --port "$PORT" > "$APP_DIR/uvicorn.log" 2>&1 &
sleep 5

echo "[INFO] Verifying deployment"
HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}/docs" || true)
echo "[INFO] /docs HTTP code: ${HTTP_CODE}"

if [ "$HTTP_CODE" = "200" ]; then
  echo "[SUCCESS] Azure deployment from main completed"
else
  echo "[WARN] Health check failed, tailing logs"
  tail -n 100 "$APP_DIR/uvicorn.log" || true
fi

echo "[INFO] Active listeners on ${PORT}:"
ss -ltnp | grep ":${PORT}" || true
