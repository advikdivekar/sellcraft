# SellCraft AI

*One product photo. A few facts. A complete marketing kit.*

Small-seller marketing studio: upload a product photo, enter a few verified facts, pick a platform / tone / style / goal, and get platform-specific listing copy plus a video-ad brief. Copy is written by an **open-weight model (Gemma) running locally through Ollama**, so product data never leaves your machine. See [`plan.md`](plan.md) for the full design.

**Status:** Phase 1 (form → Gemma copy → editable results) is working. Video (FFmpeg animated-photo ad), ElevenLabs voiceover and Sentry tracing are next.

## What it makes
From up to **5 photos** and a few facts: platform-specific copy, **studio-style product photos** (background removed, re-lit, designed backdrop, shadow/reflection), and a **10-second vertical video ad** built from those photos with multi-shot camera moves and text. Photos are read by the model to pre-fill the form (marked "From photo: check it"); you can add anything it can't see. One tap shares the video + caption from your phone, downloads everything as a zip, or sends a **draft** product to Shopify.

**Honesty:** the video is image processing (background removal + FFmpeg animation), *not* AI-generated footage, and the UI says so. Nothing is posted anywhere without you tapping a button; Shopify products are created as drafts.

## What runs where
| Part | Where | Notes |
|---|---|---|
| Copy + photo reading | Local (Ollama, Gemma 3) | Open weights, no per-use cost. Check Gemma's terms before commercial use. |
| Background removal | Local (rembg / U2-Net, ONNX on CPU) | Downloads a 44 MB model on first use |
| Video + photos | Local (FFmpeg, Pillow) | |
| Voiceover | ElevenLabs (cloud, optional, not built yet) | Script would be sent to ElevenLabs |
| Shopify publish | Your Shopify store (optional) | Token stays on the backend |

## Why it's fast
- Copy is split into 5-6 small JSON generations that run **in parallel** (Ollama `OLLAMA_NUM_PARALLEL`), and finished parts appear on screen immediately.
- Studio photos + video render **at the same time** as the copy is written; they only meet at the end.
- Prompts are trimmed per part (each parallel call re-reads its prompt), and a smaller model reads the photos.
- Only failed parts are re-run, and risky claims are caught by a deterministic check, not a second model pass.

Set Ollama up for it (macOS/Homebrew; re-run after a reboot):
```bash
launchctl setenv OLLAMA_NUM_PARALLEL 4 && launchctl setenv OLLAMA_KEEP_ALIVE 1h && brew services restart ollama
```
Measured on an M-series Mac (18 GB): 12B copy ~45-60 s end to end (was ~90-145 s as one call), 4B ~15-20 s; photo scan ~7 s with 4B.

## Shopify (optional, free)
1. Create a free dev store at partners.shopify.com (or use your own store).
2. In the store admin: Settings > Apps and sales channels > Develop apps > Create an app. Grant Admin API scopes `write_products` and `write_files`, install it, and copy the Admin API access token (`shpat_...`).
3. In `backend/.env` set `SHOPIFY_STORE_DOMAIN=your-store.myshopify.com` and `SHOPIFY_ADMIN_TOKEN=...`, restart the backend.
4. On a finished kit, tap **Send to Shopify as draft**. Not yet verified against a live store: tell me if Shopify rejects anything.

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
scripts/dev-phone.sh                # production build (use for demos); --dev for hot reload; DEMO_MODE=true to skip Ollama
```
It starts the backend, the frontend and a Cloudflare quick tunnel, then prints an `https://…trycloudflare.com` URL and a QR code. Scan it with the iPhone camera. HTTPS gives Safari the secure context it needs for camera capture, clipboard and share, and the tunnel works even when the Wi-Fi blocks device-to-device traffic (or on cellular). Code changes hot-reload. Anyone with the link can use the app while it runs; stop with Ctrl+C.

## Tests
`cd backend && .venv/bin/python -m pytest` (mocked LLM, no live services needed).

## Layout
`backend/` FastAPI + SQLite + Ollama provider · `frontend/` Next.js (App Router, Tailwind) · `plan.md` design and roadmap.

## Secrets
Keys live only in `backend/.env` (gitignored). Never commit them.
