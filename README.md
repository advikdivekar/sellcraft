# SellCraft AI

*One product photo. A few facts. A complete marketing kit.*

Small-seller marketing studio: upload a product photo, enter a few verified facts, pick a platform / tone / style / goal, and get platform-specific listing copy plus a video-ad brief. Copy is written by an **open-weight model (Gemma) running locally through Ollama**, so product data never leaves your machine. See [`plan.md`](plan.md) for the full design.

**Status:** Phase 1 (form → Gemma copy → editable results) is working. Video (FFmpeg animated-photo ad), ElevenLabs voiceover and Sentry tracing are next.

## What runs where
| Part | Where | Notes |
|---|---|---|
| Copy generation | Local (Ollama + Gemma) | Open weights, no per-use cost. Check Gemma's terms before commercial use. |
| Video | Local FFmpeg (next phase) | Will be labelled "animated-photo ad", not AI-generated footage |
| Voiceover | ElevenLabs (cloud, optional) | Script is sent to ElevenLabs. Key stays on the backend. |

## Run it
Prereqs: Python 3.12, Node 20+, [Ollama](https://ollama.com), ffmpeg.

```bash
# 1. model
ollama pull gemma3:4b          # or gemma3:12b if you have the RAM

# 2. backend
cd backend
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt   # or python3.12 -m venv + pip
cp ../.env.example .env        # then edit
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. frontend (new terminal)
cd frontend && npm install && npm run dev -- -H 0.0.0.0
# open http://localhost:3000
```
No Ollama yet? Set `DEMO_MODE=true` in `backend/.env`. The UI then shows a visible **Demo Mode** label; output is deterministic sample text, not a model response.

### Open it on your phone (any network, HTTPS)
```bash
brew install cloudflared qrencode   # once
scripts/dev-phone.sh                # add DEMO_MODE=true to run without Ollama
```
It starts the backend, the frontend and a Cloudflare quick tunnel, then prints an `https://…trycloudflare.com` URL and a QR code. Scan it with the iPhone camera. HTTPS gives Safari the secure context it needs for camera capture, clipboard and share, and the tunnel works even when the Wi-Fi blocks device-to-device traffic (or on cellular). Code changes hot-reload. Anyone with the link can use the app while it runs; stop with Ctrl+C.

## Tests
`cd backend && .venv/bin/python -m pytest` (mocked LLM, no live services needed).

## Layout
`backend/` FastAPI + SQLite + Ollama provider · `frontend/` Next.js (App Router, Tailwind) · `plan.md` design and roadmap.

## Secrets
Keys live only in `backend/.env` (gitignored). Never commit them.
