# SellCraft AI — Project Plan

**Tagline:** One product photo. A few facts. A complete marketing kit.
**Event:** Hacktoberfest Open-Source AI Challenge, Week 2 — *Side Hustle*. Submissions due **Oct 18, 2026**.
**Status:** Planning complete. Verdict: **GO** (scope-cut MVP).

> **Scope decision (updated Oct 15):** ElevenLabs is **back in**: we have an API key with ~10,000 free credits. Voiceover is optional per job, backend-only key, and the app still works silently if the key is missing or credits run out. Budget the credits: ~10 s of narration per ad, cache audio per script, and don't regenerate unless the script changes. No voice cloning.

---

## 1. What we're building
An AI marketing studio for small online sellers (Instagram, Etsy, Shopify, etc.). The seller uploads a product photo, enters a few verified facts, picks platform/tone/style/goal, and gets:

- Platform-specific listing copy (title, descriptions, bullets, tags, SEO, caption, CTA)
- A video-ad brief (hook, storyboard, motion prompt, on-screen text, voiceover script)
- A 10-second vertical (9:16) MP4 ad — real image-to-video model if available, otherwise an honestly-labelled **animated-photo ad** built with FFmpeg

The open-weight LLM (Gemma via Ollama) does the core content generation. It never invents facts; missing info is flagged.

**Not in MVP:** accounts, payments, auto-publishing, custom training, analytics, catalog manager, many video modes, voiceover (deferred).

## 2. Why open-source matters (for the DEV post)
- Copy generation runs **locally** on Gemma: seller product data stays on their machine, zero per-generation cost.
- Swappable model behind a provider interface (change `OLLAMA_MODEL`).
- Honest about what is not local (hosted video provider, if ever enabled).
- Targets prizes: **Best Use of Gemma** ($200) + main prize (writing quality weighted most).

## 3. System architecture

```
 ┌───────────────────────── BROWSER (Seller) ─────────────────────────┐
 │ Next.js (App Router) · TypeScript · Tailwind · shadcn/ui · Lucide  │
 │ Home/Status │ Product Form │ Creative Controls │ Progress │ Results│
 └───────────────────────────────┬────────────────────────────────────┘
                                 │ HTTP/JSON + multipart (no secrets)
 ┌───────────────────────────────▼────────────────────────────────────┐
 │                FASTAPI BACKEND (Python, Pydantic)                  │
 │ API routers → Job Orchestrator (BackgroundTasks) → SQLite (jobs)   │
 │ Upload service (type/size/safe name)                               │
 │   1 CopyService     → OllamaProvider (open-weight, local)          │
 │   2 VideoService    → ImageToVideoProvider                         │
 │                        ├ AnimatedPhotoFallback (FFmpeg)  [default] │
 │                        └ LTXProvider (optional, GPU/hosted)        │
 │   3 TTSService      → ElevenLabs (optional)                │
 │   4 AssemblyService → FFmpeg overlays + FFprobe validation         │
 │ Local file storage (UPLOAD_DIR / OUTPUT_DIR) + cleanup             │
 └──────┬───────────────────────┬──────────────────────┬──────────────┘
   ┌────▼─────┐          ┌──────▼──────┐        ┌──────▼─────┐
   │ Ollama   │          │ LTX-2/hosted│        │ FFmpeg /   │
   │ :11434   │          │ (optional)  │        │ FFprobe    │
   │ LOCAL    │          └─────────────┘        └────────────┘
   └──────────┘
```

## 4. Options per component

| Layer | Options | Chosen | Notes |
|---|---|---|---|
| Frontend | **Next.js App Router**, Vite+React | Next.js | per spec |
| UI | **shadcn/ui + Tailwind**, Mantine | shadcn | accessible |
| Data fetching | **TanStack Query**, SWR | TanStack Query | job polling |
| Backend | **FastAPI**, Flask | FastAPI | Pydantic |
| Job runner | **BackgroundTasks**, ARQ/Redis, Celery, Temporal | BackgroundTasks | documented limit; modular for worker later |
| DB | **SQLite**, Postgres, MongoDB | SQLite | job metadata only |
| LLM runtime | **Ollama**, llama.cpp, vLLM | Ollama | local |
| LLM model | **Gemma 3 (4B/12B)**, Llama, Qwen | Gemma (size by RAM) | verify tag with `ollama list` |
| Structured output | **Ollama JSON-schema `format` + Pydantic + 1 repair retry** | same | |
| Image→video | **FFmpeg fallback**, LTX-Video/LTX-2, hosted GPU | Fallback default, LTX adapter behind flag | label honestly |
| TTS | **ElevenLabs**, Piper | ElevenLabs (optional, key in `.env`) | free credits; silent fallback if unconfigured/exhausted |
| Assembly | **FFmpeg (argv list, no shell)**, MoviePy | FFmpeg | |
| Storage | **Local FS**, S3/R2 | Local FS | ephemeral on deploy |
| Tests | **pytest + httpx + mocks**, Vitest/Playwright | pytest + manual E2E script | |
| Hosting | **Local**, Render, DigitalOcean | Local demo first | |

## 5. Backend design

**Provider interfaces**
- `LLMProvider`: `health()`, `generate_json(prompt, schema)` → `OllamaProvider` (+ visibly-labelled `DemoProvider` when Ollama is offline)
- `ImageToVideoProvider`: `available()`, `generate(image, motion_prompt, duration, aspect, ctx)` → `AnimatedPhotoFallbackProvider`, `LTXProvider`
- `TTSProvider` → `ElevenLabsProvider`: `available()`, `voices()`, `synthesize()`

**Prompt structure** (separate sections): `FACTS | PLATFORM | TONE | STYLE | OBJECTIVE | RULES | OUTPUT SCHEMA`.
Rules: facts are the only source of truth; never invent specs, prices, discounts, reviews, certifications, "eco/organic/handmade/hypoallergenic" claims; flag gaps in `missing_information`; list risky phrasing in `claims_requiring_review`; honour the seller's forbidden words (post-check enforced in code).

**Job states:** `queued → generating_copy → generating_video → assembling_video → completed` (or `failed`). `generating_voiceover` runs only when voiceover is enabled and ElevenLabs is configured; otherwise skipped. Copy-only regeneration never re-runs video.

**Data models (Pydantic):** `ProductInput`, `CreativeSettings`, `CopyOutput` (+ per-platform outputs), `GenerationJob`, `GeneratedAsset`.
Enums — Platform: instagram/facebook/pinterest/etsy/shopify · Tone: straightforward/persuasive/emotional/friendly/luxury/playful · Style: premium_studio/ugc/minimal/warm_cozy/bold_colorful · Objective: sales/awareness/gift/features.

**API**

| Method | Path | Purpose |
|---|---|---|
| GET | /api/health | liveness |
| GET | /api/providers/status | ollama/model, ffmpeg, video provider (no secrets) |
| POST | /api/uploads | validated image → asset_id |
| POST | /api/generations | create job (202) |
| GET | /api/generations/{id} | status + results |
| PATCH | /api/generations/{id}/copy | save user edits |
| POST | /api/generations/{id}/regenerate-copy | section/tone regen, no video rerun |
| GET | /api/generations/{id}/assets/{asset_id} | protected download |

**Security:** magic-byte + MIME check, ≤10 MB, JPEG/PNG/WebP; UUID filenames; asset access by ID scoped to job; FFmpeg via argv list + sanitized text (use `textfile=`); no product text or secrets in logs; CORS locked; periodic cleanup.

## 6. Video pipeline (10 s, 9:16, 1080×1920)

```
 0–2s Hook │ 2–6s Product showcase │ 6–8s Key verified feature │ 8–10s CTA (name + CTA)
```
Fallback: blurred background + fitted product (no stretching), gentle zoom/pan, drawtext with a bundled font, safe margins, burned-in captions. Export H.264 (+AAC only if audio exists). FFprobe must confirm ≈10 s (9.5–10.5) or the job fails. UI/API label: **"Animated-photo ad"** vs **"AI-generated video (LTX)"**. LTX adapter only claimed as working if actually run.

## 7. Frontend design

```
app/
 ├ page.tsx            Home: hero, provider-status badge, "Create marketing kit"
 ├ create/page.tsx     ProductForm (+ImageDropzone) · CreativeControls · Generate
 └ jobs/[id]/page.tsx  ProgressStepper (real backend state) → ResultsWorkspace
      CopyTabs (per platform, editable, copy, regenerate)
      ToneRegenerate · WarningsPanel (missing info / claims to review)
      VideoPlayer + MethodBadge · DownloadBar (MP4, listing .txt/.json)
      Voiceover script panel (text only, fit-in-10s estimate)
```
Style: light neutral background, dark text, one accent color, rounded cards used purposefully, **mobile-first responsive** (see 7b), accessible focus states.

## 7b. Mobile-first requirements (demo will be shown on a phone)

**Principle:** design for ~390px width first, then scale up to desktop. The phone is the primary demo device — **target device: iPhone (Safari)**; Android is secondary.

iPhone notes: HEIC photos are common (convert client-side to JPEG); Safari needs `playsinline` and H.264/yuv420p/faststart video; camera, Clipboard and Web Share need HTTPS (use the tunnel); Safari ignores `<a download>` for video, so use the share sheet "Save Video".

**Layout & UX**
- Single-column, one-step-at-a-time wizard on mobile (Product → Style → Generate → Results); side-by-side panels only at `md:` and up.
- Touch targets ≥ 44×44 px; segmented controls become horizontally scrollable chips or bottom-sheet pickers; sticky bottom "Generate" / "Download" bar.
- No horizontal page scroll; use `100dvh` (not `100vh`), safe-area insets (`env(safe-area-inset-*)`), and viewport meta `width=device-width, initial-scale=1`.
- Inputs use ≥16px font (prevents iOS zoom-on-focus) and proper `inputMode`/`autocomplete`.
- Results: tabs collapse to a scrollable tab bar; copy buttons give instant "Copied" feedback (Clipboard API with fallback).
- Respect `prefers-color-scheme`/reduced motion; keep the UI light and fast (no heavy JS, lazy-load the video).

**Photo input**
- `<input type="file" accept="image/jpeg,image/png,image/webp" capture="environment">` option so the seller can **take a photo with the phone camera** or pick from the gallery.
- Handle large phone photos: client-side downscale (max ~2048px, re-encode) before upload, server still validates type/size; handle HEIC by converting client-side or showing a clear "use JPEG/PNG/WebP" message.

**Video on mobile**
- `<video playsinline controls muted preload="metadata">` with a poster frame; vertical 9:16 fits the phone screen natively.
- Export H.264, `-pix_fmt yuv420p`, `-movflags +faststart`, even dimensions → plays in iOS Safari and Android Chrome.
- Download: use `<a download>` plus the Web Share API (`navigator.share({files})`) as the "Save / Share" path, since iOS often ignores direct downloads.

**Reaching the app from the phone (demo setup)**
- Run Next.js with `-H 0.0.0.0` and FastAPI on `0.0.0.0`; the phone opens `http://<laptop-LAN-IP>:3000` on the same Wi-Fi. Next `rewrites` proxy `/api/*` to FastAPI so the phone only talks to one origin (no CORS/mixed-content issues).
- Ollama and FFmpeg stay on the laptop; the phone is just the UI.
- Fallback if Wi-Fi blocks device-to-device traffic (e.g. college/venue networks): a tunnel such as `cloudflared tunnel --url http://localhost:3000` (HTTPS also needed for camera access/Clipboard/Share on some browsers). Document both in the README.
- Camera capture and `navigator.share` require a secure context on some browsers → plan on the HTTPS tunnel for the camera part of the demo.

**Testing for mobile**
- Manual checklist on a real iPhone Safari and Android Chrome: upload from camera, form usability with keyboard open, progress screen, video playback, copy, share/save.
- Playwright run with a mobile viewport (e.g. iPhone 14 / Pixel 7 device profiles) for the core flow.
- Optional: make it installable as a PWA (manifest + icons) so it opens full-screen from the home screen for the demo; no offline mode needed.

## 8. Directory structure

```
sellcraft/
 ├ plan.md  README.md  .env.example  .gitignore
 ├ backend/  requirements.txt
 │   ├ app/ main.py config.py db.py
 │   │   ├ api/  schemas/  core/
 │   │   └ services/ llm/ video/ tts/ assembly/ jobs/ storage/ prompts/
 │   ├ data/ (uploads, outputs, db — gitignored)
 │   └ tests/
 ├ frontend/ (Next.js app)
 └ docs/ (architecture, demo script, licenses)
```

## 9. Config (`.env.example`, placeholders only)
`OLLAMA_BASE_URL` `OLLAMA_MODEL` `VIDEO_PROVIDER` (`fallback`|`ltx`) `VIDEO_PROVIDER_URL` `VIDEO_PROVIDER_API_KEY` `UPLOAD_DIR` `OUTPUT_DIR` `DATABASE_URL` · `ELEVENLABS_API_KEY` `ELEVENLABS_DEFAULT_VOICE_ID` `SENTRY_DSN` (optional)

## 10. Milestones (deadline Oct 18)

| Day | Goal | Done when |
|---|---|---|
| **Day 1 (Oct 15–16)** | Scaffold + product form → Gemma copy → editable results | Real structured copy from local Gemma; edit/copy/regenerate section & tone |
| **Day 2 (Oct 16–17)** | FFmpeg animated-photo MP4 + assembly + preview/download | ffprobe-verified ~10 s MP4 with overlays, labelled correctly |
| **Day 3 (Oct 17–18)** | Polish, tests, README, real-seller test, DEV post | Tests pass; README run-through works; post submitted |
| Day 2-3 add | ElevenLabs voiceover + audio mix; Sentry tracing; start recording Entire/DevRelay sessions from Day 1 | voiceover mixes into MP4; traces visible in Sentry |
| Parallel/stretch | Tinker fine-tune (section 16); LTX adapter; deploy | only after core flow works |

## 11. Testing
pytest with mocks (never live paid APIs): input validation, missing facts, structured-output validation, prompt building, Ollama-offline error, failed video, job state transitions, invalid upload, FFmpeg assembly + duration (if installed), asset authorization. Plus one repeatable manual E2E script.

## 12. Risks

| Risk | Mitigation |
|---|---|
| 3-day deadline | strict order; video AI optional |
| No GPU | fallback is first-class and honestly labelled |
| Bad JSON from Gemma | schema `format`, Pydantic, one repair retry, clear errors |
| Hallucinated claims | strict prompt + `missing_information` + forbidden-word check |
| FFmpeg text/font bugs | bundled font, `textfile=`, argv list |
| Weak writing score | reserve final half-day for the post + user feedback |

## 13. Prize focus
Only one win is possible, but we can enter several categories (confirm in the official rules). Entering: **Main ($250), Best Use of Gemma ($200), Best Use of Sentry Agent Tracing ($100), Best Use of Entire ($100), Best Use of Tinker ($200)**. ElevenLabs ($100) also applies naturally since voiceover is in.

| Category | What we must ship / show |
|---|---|
| Gemma | Gemma via Ollama as the core generator; README + post explain model choice, local run, swap via `OLLAMA_MODEL`; check Gemma terms |
| Sentry | `sentry-sdk` in FastAPI; traces/spans per job stage (copy, video, TTS, assembly) with latency; LLM token counts + cost ($0 local) as span data; screenshots of traces + one real debugging story in the post; scrub product text/PII (`send_default_pii=False`) |
| Entire | Capture agent sessions (Entire / DevRelay) during the build and embed/link them in the post |
| Tinker | Fine-tune a Gemma-family model for listing copy (see section 16); show measured improvement vs. base model |
| ElevenLabs (bonus) | Voiceover integrated, key backend-only, graceful degradation |

## 14. Definition of done (MVP)
1. Upload photo + facts. 2. Choose platform/tone/style/objective. 3. Gemma generates structured, editable copy. 4. Missing facts flagged, not invented. 5. Regenerate a single section/tone without touching video. 6. Valid ~10 s MP4 (labelled animated-photo ad unless a real model ran). 7. Preview + download. 8. Truthful progress/errors. 9. README setup works. 10. Tests pass. 11. No secrets committed. 12. Full flow (camera photo → generate → play video → copy/share) works on a real phone.

## 15. Open items
- Gemma size / RAM and whether Ollama + ffmpeg are installed (to be checked at scaffold time).
- Real seller for the first-user feedback.
- Local-only demo vs. deploy.
- Confirm in the official rules whether one project may enter multiple categories.

## 16. Tinker fine-tune plan (stretch, must show measurable improvement)
**Goal:** fine-tune a Gemma model so listing copy follows the schema and the "never invent facts" rules better than the base model, at equal or lower cost/latency.

1. **Check availability first:** confirm Tinker supports a Gemma model (else use the closest open model it offers and say so honestly). Claim credits at hacktoberfest.com/my/promos.
2. **Data:** build a small dataset (~100-300 examples) of product facts + settings → ideal structured copy. Hand-write a seed set, expand with careful generation, then review. Include negative cases (sparse facts → `missing_information`, forbidden words honoured). Hold out ~20% as an eval set. No real customer data.
3. **Eval harness (build before training):** score base vs. tuned on the held-out set: valid-JSON rate, schema pass rate, **hallucinated-claim rate** (claims not in the facts), forbidden-word violations, missing-info flagged correctly, latency, token cost.
4. **Train** with Tinker (LoRA), export/serve the tuned weights through Ollama if licence and tooling allow; else document how it would be served.
5. **Report** a before/after table in the DEV post.
Risk: time. Gate: only start after Day 2 milestone is done; the app works without it (`OLLAMA_MODEL` just points at the base model).

## 17. Secrets handling
ElevenLabs/Sentry/Tinker keys live only in `backend/.env` (gitignored). Never paste keys into chat, commits or the frontend. `.env.example` has placeholders.
