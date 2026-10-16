# SellCraft AI

*One product photo. A few facts. A complete marketing kit.*

Small-seller marketing studio: upload a product photo, enter a few verified facts, pick a platform / tone / style / goal, and get platform-specific listing copy plus a video-ad brief. Copy is written by an **open-weight model (Gemma) running locally through Ollama**, so product data never leaves your machine. See [`plan.md`](plan.md) for the full design.

**Status:** Working end to end: facts and photos → Gemma copy → studio photos, image deck and a 10-second video → export or Shopify draft. A LoRA fine-tune on Tinker, an independent Gemma judge and Sentry tracing are in; see [`docs/RESULTS.md`](docs/RESULTS.md) for the measured numbers and [`docs/DECISIONS.md`](docs/DECISIONS.md) for why things are the way they are.

## What it makes
From up to **5 photos** and a few facts (the app measures each photo, flags blur/low-res/dark shots, cleans the cut-out, and picks a backdrop that makes your product stand out): platform-specific copy, **studio-style product photos** (background removed, re-lit, designed backdrop, shadow/reflection), and a **10-second vertical video ad** built from those photos with multi-shot camera moves and text. Photos are read by the model to pre-fill the form (marked "From photo: check it"); you can add anything it can't see. One tap shares the video + caption from your phone, downloads everything as a zip, or sends a **draft** product to Shopify.

**Honesty:** the video is image processing (background removal + FFmpeg animation), *not* AI-generated footage, and the UI says so. Nothing is posted anywhere without you tapping a button; Shopify products are created as drafts.

## How your photos are refined
Not just a new background: the product pixels themselves are retouched, deterministically and without a generative model, so labels, logos and shape stay true.
1. Background removed at the photo's **full resolution** (rembg / U2-Net; only the mask is predicted small).
2. Camera noise reduced (strength follows the measured noise), then a small **super-resolution network** (OpenCV FSRCNN, x2) when the product has few pixels.
3. Local contrast recovered only on textured areas (flat colour is left alone), colour cast and exposure fixed on the product only, edge halos removed, sharpening proportional to how soft the photo was.
4. Backdrop chosen from what the photo shows (dark product -> lighter backdrop, warm product + bold style -> cool backdrop).

The refined product feeds everything: the video, the studio photos, a white-background marketplace photo, a transparent PNG, and the **image deck** (hero, benefits, close-up, extra angles, call to action). The benefits slide only ever uses features and benefits you gave or confirmed; with fewer than two it is skipped and the app says why. Photo problems (blur, low resolution, product too small) are reported, not hidden.

## What runs where
| Part | Where | Notes |
|---|---|---|
| Copy + photo reading | Local (Ollama, Gemma 3) | Open weights, no per-use cost. Check Gemma's terms before commercial use. |
| Background removal | Local (rembg / U2-Net, ONNX on CPU) | Downloads a 44 MB model on first use |
| Video + photos | Local (FFmpeg, Pillow) | |
| Shopify publish | Your Shopify store (optional) | Token stays on the backend |

## Open models, and the job each one does
| Model | Job | Where it runs |
|---|---|---|
| **Gemma 3 (4B / 12B)** | Writes the listing copy (default), reads the product photos to pre-fill the form | Local, Ollama |
| **Gemma 3 12B** | Independent judge: reads each kit next to its facts and lists every statement the facts don't support | Local, Ollama |
| **Qwen3.5-4B + LoRA** (`sellcraft-copy-v2`) | Fine-tuned copy writer, trained on Tinker to follow the grounding rules | Tinker sampling today; adapter can be exported |
| Qwen3.5-397B (teacher) | Wrote and revised the training data under the checker's feedback | Tinker |

Gemma is the product's default brain and also its referee. The fine-tune is measured against Gemma on the same 60 held-out kits.

## Measured results
On 60 held-out synthetic fact sets, under one deterministic checker: the fine-tune (Qwen3.5-4B + LoRA, trained on Tinker) writes a kit with no hard violation **88%** of the time (95% CI 78-95%), against 45% for Gemma 3 12B, 23% for Gemma 3 4B and 18% for the untuned Qwen base. An independent Gemma judge (n=30) is more modest: the fine-tune halves the base model's unsupported statements per kit (0.43 to 0.20) and is level with Gemma 4B, but the intervals overlap. Full tables, caveats, cost per 1,000 kits and reproduce commands: [`docs/RESULTS.md`](docs/RESULTS.md).

In the app, the default **Fast** setting (Gemma 3 4B) builds the whole kit (copy, studio photos, deck, video) in about 18 seconds; **Best quality** (Gemma 3 12B) takes about a minute. Pick it under "Writing speed" when creating a kit.

## Observability (Sentry)
Every model call is a `gen_ai.chat` span (model, token counts, tokens/second, latency) under a `gen_ai.invoke_agent` span per job. Every flagged claim (forbidden word, not-in-your-facts, regulated claim) is a Sentry issue tagged with the rule, the model and the prompt version, and the "The copy still made something up" button on a finished kit logs a report against that job.
**Seller text never leaves the machine:** callers pass metadata only, and an allow-list scrubber (`app/tracing.py`) drops everything else before sending. `tests/test_tracing.py` pushes a unique marker through the facts and the model output and fails if it shows up in any outgoing Sentry payload. Set `SENTRY_DSN` in `backend/.env` to turn it on; without it tracing is a no-op.

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

## Connect your store (no `.env` editing)
Open **Connections** in the app (home page, or the Shopify box on a finished kit):
1. Free dev store: partners.shopify.com (or use your own store).
2. Store admin > Settings > Apps and sales channels > Develop apps > Create an app > Configuration: select Admin API scope `write_products`, save, **Install app**, copy the **Admin API access token** (`shpat_...`).
3. Paste the store address and token into the Connections page. The app checks the token and its scopes before saving, encrypts it (Fernet) in the local database, and never sends it back to the browser. **Disconnect** deletes it.

On a finished kit, **Send to Shopify as draft** creates a draft product with your studio + white-background photos, the video, description, tags and SEO. Nothing goes live until you publish it in Shopify. (Setting `SHOPIFY_STORE_DOMAIN` / `SHOPIFY_ADMIN_TOKEN` in `backend/.env` still works as a fallback.) Tested with a mocked Shopify, not yet against a live store.

One-click "Connect with Shopify" (OAuth) and Instagram/Facebook/Pinterest/Etsy posting need a registered developer app per platform and a stable public HTTPS address, so they're planned for a deployed version. This app has no user accounts: connections belong to the whole installation, so only run it for yourself.

## Access code (when shared over the internet)
`scripts/dev-phone.sh` generates a random access code, requires it on every API call, and puts it in the QR link (`...trycloudflare.com/#k=CODE`). Without it, anyone who learned the tunnel URL could use your GPU or publish to your connected store. Locally (no tunnel) there is no code unless you set `ACCESS_CODE` in `backend/.env`.

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

## Public demo (landing page only)
The landing page and its in-browser studio can be deployed on their own: no backend, no model, nothing leaves the visitor's browser. `render.yaml` does it for Render (`NEXT_PUBLIC_DEMO_ONLY=1`; the app routes then redirect home). The full app, which needs Ollama on your computer, is not part of that deploy.

## Screenshots and demo
`docs/images/` has landing and app screenshots (mobile and desktop); `docs/demo/sellcraft-demo-mobile.mp4` is a 70-second phone walkthrough from the landing page to a finished kit built from the sample product.

## Tests
`cd backend && .venv/bin/python -m pytest` (mocked LLM, no live services needed).

## Layout
`backend/` FastAPI + SQLite + Ollama provider · `frontend/` Next.js (App Router, Tailwind) · `plan.md` design and roadmap.

## Secrets
Keys live only in `backend/.env` (gitignored). Never commit them.
