#!/usr/bin/env bash
# Start backend + frontend + an HTTPS tunnel so the app opens on your phone over ANY network
# (works on cellular, venue Wi-Fi that blocks device-to-device traffic, and gives the
# secure context iOS needs for camera capture, clipboard and share).
# Usage: scripts/dev-phone.sh        (set DEMO_MODE=true to run without Ollama)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="${TMPDIR:-/tmp}/sellcraft-dev"; mkdir -p "$LOG"
PIDS=()
cleanup() { for p in "${PIDS[@]:-}"; do kill "$p" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM

command -v cloudflared >/dev/null || { echo "Install it first: brew install cloudflared"; exit 1; }

(cd "$ROOT/backend" && exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload) >"$LOG/api.log" 2>&1 &
PIDS+=($!)
(cd "$ROOT/frontend" && exec npm run dev -- -H 127.0.0.1) >"$LOG/web.log" 2>&1 &
PIDS+=($!)

echo "Waiting for the app..."
for _ in $(seq 1 60); do
  curl -fs http://127.0.0.1:3000/api/health >/dev/null 2>&1 && break; sleep 1
done
curl -fs http://127.0.0.1:3000/api/health >/dev/null || { echo "App didn't start. See $LOG/*.log"; exit 1; }

cloudflared tunnel --url http://127.0.0.1:3000 --no-autoupdate >"$LOG/tunnel.log" 2>&1 &
PIDS+=($!)
URL=""
for _ in $(seq 1 40); do
  URL="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG/tunnel.log" | head -1 || true)"
  [ -n "$URL" ] && break; sleep 1
done
[ -n "$URL" ] || { echo "No tunnel URL. See $LOG/tunnel.log"; exit 1; }

echo; echo "Open on your phone:  $URL"; echo
command -v qrencode >/dev/null && qrencode -t ANSIUTF8 "$URL"
echo; echo "Anyone with this link can reach the app while it runs. Ctrl+C to stop. Logs: $LOG"
wait
