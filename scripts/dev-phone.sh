#!/usr/bin/env bash
# Start backend + frontend + an HTTPS tunnel so the app opens on your phone over ANY network
# (works on cellular, venue Wi-Fi that blocks device-to-device traffic, and gives the
# secure context iOS needs for camera capture, clipboard and share).
# Usage: scripts/dev-phone.sh          production build (fast on phones; use this for demos)
#        scripts/dev-phone.sh --dev    hot reload (dev bundles are heavy over a tunnel and can stall on phones)
#        DEMO_MODE=true scripts/dev-phone.sh   run without Ollama
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="${TMPDIR:-/tmp}/sellcraft-dev"; mkdir -p "$LOG"
PIDS=()
cleanup() { for p in "${PIDS[@]:-}"; do kill "$p" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM

command -v cloudflared >/dev/null || { echo "Install it first: brew install cloudflared"; exit 1; }

MODE="${1:-prod}"
# The tunnel makes the app reachable from the internet, so require a random access code (carried in the QR link).
ACCESS_CODE="$(openssl rand -hex 4)"; export ACCESS_CODE
echo "$ACCESS_CODE" > "$LOG/access_code"
RELOAD=""; [ "$MODE" = "--dev" ] && RELOAD="--reload"
(cd "$ROOT/backend" && exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 $RELOAD) >"$LOG/api.log" 2>&1 &
PIDS+=($!)
if [ "$MODE" = "--dev" ]; then
  (cd "$ROOT/frontend" && exec npm run dev -- -H 127.0.0.1) >"$LOG/web.log" 2>&1 &
else
  echo "Building production frontend..."
  (cd "$ROOT/frontend" && npm run build) >"$LOG/build.log" 2>&1 || { echo "Build failed. See $LOG/build.log"; exit 1; }
  (cd "$ROOT/frontend" && exec npm run start -- -H 127.0.0.1) >"$LOG/web.log" 2>&1 &
fi
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

LINK="$URL/#k=$ACCESS_CODE"
echo; echo "Open on your phone:  $LINK"; echo "(access code: $ACCESS_CODE)"; echo
command -v qrencode >/dev/null && qrencode -t ANSIUTF8 "$LINK"
echo; echo "The link only works with the access code. Ctrl+C to stop. Logs: $LOG"
wait
