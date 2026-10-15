# SellCraft AI — Project Plan

**Tagline:** One product photo. A few facts. A complete marketing kit.
**Event:** Hacktoberfest Open-Source AI Challenge, Week 2 — *Side Hustle*. Submissions due **Oct 18, 2026**.
**Status:** Planning complete. Verdict: **GO** (scope-cut MVP).

> **Scope decision:** ElevenLabs voiceover is **deferred** (no free tier). The TTS layer stays behind an interface so it can be added later (ElevenLabs, or the open-source Piper). The MVP produces a **silent video with on-screen text/captions**; the voiceover script is still generated and editable as text.

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
 │   3 TTSService      → (deferred) ElevenLabs / Piper                │
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
| TTS | ElevenLabs, Piper | **Deferred** | interface stubbed, UI shows "not configured" |
| Assembly | **FFmpeg (argv list, no shell)**, MoviePy | FFmpeg | |
| Storage | **Local FS**, S3/R2 | Local FS | ephemeral on deploy |
| Tests | **pytest + httpx + mocks**, Vitest/Playwright | pytest + manual E2E script | |
| Hosting | **Local**, Render, DigitalOcean | Local demo first | |

## 5. Backend design

**Provider interfaces**
- `LLMProvider`: `health()`, `generate_json(prompt, schema)` → `OllamaProvider` (+ visibly-labelled `DemoProvider` when Ollama is offline)
- `ImageToVideoProvider`: `available()`, `generate(image, motion_prompt, duration, aspect, ctx)` → `AnimatedPhotoFallbackProvider`, `LTXProvider`
- `TTSProvider` (stub only in MVP): `available()`, `voices()`, `synthesize()`

**Prompt structure** (separate sections): `FACTS | PLATFORM | TONE | STYLE | OBJECTIVE | RULES | OUTPUT SCHEMA`.
Rules: facts are the only source of truth; never invent specs, prices, discounts, reviews, certifications, "eco/organic/handmade/hypoallergenic" claims; flag gaps in `missing_information`; list risky phrasing in `claims_requiring_review`; honour the seller's forbidden words (post-check enforced in code).

**Job states:** `queued → generating_copy → generating_video → assembling_video → completed` (or `failed`). `generating_voiceover` exists in the enum but is skipped in MVP. Copy-only regeneration never re-runs video.

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
Style: light neutral background, dark text, one accent color, rounded cards used purposefully, responsive, accessible focus states.

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
`OLLAMA_BASE_URL` `OLLAMA_MODEL` `VIDEO_PROVIDER` (`fallback`|`ltx`) `VIDEO_PROVIDER_URL` `VIDEO_PROVIDER_API_KEY` `UPLOAD_DIR` `OUTPUT_DIR` `DATABASE_URL` · (later) `ELEVENLABS_API_KEY` `ELEVENLABS_DEFAULT_VOICE_ID`

## 10. Milestones (deadline Oct 18)

| Day | Goal | Done when |
|---|---|---|
| **Day 1 (Oct 15–16)** | Scaffold + product form → Gemma copy → editable results | Real structured copy from local Gemma; edit/copy/regenerate section & tone |
| **Day 2 (Oct 16–17)** | FFmpeg animated-photo MP4 + assembly + preview/download | ffprobe-verified ~10 s MP4 with overlays, labelled correctly |
| **Day 3 (Oct 17–18)** | Polish, tests, README, real-seller test, DEV post | Tests pass; README run-through works; post submitted |
| Stretch | LTX adapter, ElevenLabs/Piper voiceover, Render deploy | only if time/GPU/credits |

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
Main ($250, writing weighted most) · **Best Use of Gemma** ($200). Optional: Entire/DevRelay session share. ElevenLabs/Render/Temporal categories skipped for now.

## 14. Definition of done (MVP)
1. Upload photo + facts. 2. Choose platform/tone/style/objective. 3. Gemma generates structured, editable copy. 4. Missing facts flagged, not invented. 5. Regenerate a single section/tone without touching video. 6. Valid ~10 s MP4 (labelled animated-photo ad unless a real model ran). 7. Preview + download. 8. Truthful progress/errors. 9. README setup works. 10. Tests pass. 11. No secrets committed.

## 15. Open items
- Gemma size / RAM and whether Ollama + ffmpeg are installed (to be checked at scaffold time).
- Real seller for the first-user feedback.
- Local-only demo vs. deploy.
