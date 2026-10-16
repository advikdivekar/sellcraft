"""Generates the architecture diagrams (SVG + an HTML page). Run:  python3 docs/build_diagrams.py
Coordinates are on a 10px grid so edges line up; every arrow carries a label that says what moves."""
from html import escape
from pathlib import Path

ACCENT = "#ea580c"
FS = 12


class Fig:
    def __init__(self, w, h, bg):
        self.w, self.h, self.bg, self.out = w, h, bg, []

    # --- primitives -------------------------------------------------------------------------------------------
    def text(self, x, y, s, size=FS, weight=400, anchor="start", opacity=1.0, fill="currentColor", halo=False):
        halo_attr = f' stroke="{self.bg}" stroke-width="5" stroke-linejoin="round" paint-order="stroke"' if halo else ""
        self.out.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}" '
                        f'fill-opacity="{opacity}"{halo_attr}>{escape(s)}</text>')

    def group(self, x, y, w, h, label, accent=False):
        col = ACCENT if accent else "currentColor"
        self.out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="none" stroke="{col}" stroke-opacity="{0.9 if accent else 0.28}" '
                        f'stroke-dasharray="5 5"/>')
        self.text(x + 14, y + 22, label.upper(), size=11, weight=700, opacity=0.55 if not accent else 1, fill=col)

    def box(self, x, y, w, h, title, sub=(), kind="normal", title_size=13):
        stroke = ACCENT if kind == "accent" else "currentColor"
        so = 0.95 if kind == "accent" else 0.55
        dash = ' stroke-dasharray="4 4"' if kind == "planned" else ""
        fo = 0.10 if kind == "accent" else (0.02 if kind == "planned" else 0.05)
        self.out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{stroke}" fill-opacity="{fo}" stroke="{stroke}" stroke-opacity="{so}"{dash}/>')
        n = len(sub)
        top = y + (h - (title_size + 4 + n * 15)) / 2 + title_size - 1
        self.text(x + w / 2, top, title, size=title_size, weight=600, anchor="middle", opacity=0.55 if kind == "planned" else 1)
        for i, line in enumerate(sub):
            self.text(x + w / 2, top + 18 + i * 15, line, size=11, anchor="middle", opacity=0.72)

    def store(self, x, y, w, h, title, sub=()):
        """A cylinder-ish store: rect with a top band."""
        self.out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.55"/>')
        self.out.append(f'<line x1="{x}" y1="{y + 16}" x2="{x + w}" y2="{y + 16}" stroke="currentColor" stroke-opacity="0.3"/>')
        self.text(x + w / 2, y + 12, title, size=11, weight=700, anchor="middle", opacity=0.8)
        for i, line in enumerate(sub):
            self.text(x + w / 2, y + 36 + i * 15, line, size=11, anchor="middle", opacity=0.72)

    def arrow(self, pts, label=None, at=0, dx=0, dy=-6, dashed=False, accent=False, anchor="middle", both=False):
        col = ACCENT if accent else "currentColor"
        op = 1 if accent else 0.7
        d = ' stroke-dasharray="5 4"' if dashed else ""
        m_end = "url(#arr-a)" if accent else "url(#arr)"
        m_start = f' marker-start="{"url(#arr-a-s)" if accent else "url(#arr-s)"}"' if both else ""
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="{2 if accent else 1.5}"{d} marker-end="{m_end}"{m_start}/>')
        if label:
            (x1, y1), (x2, y2) = pts[at], pts[at + 1]
            self.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, label, size=11, anchor=anchor, opacity=1 if accent else 0.85, fill=col, halo=True)

    def svg(self, title, claim):
        defs = ('<defs>'
                '<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor" fill-opacity="0.75"/></marker>'
                '<marker id="arr-s" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M10,0 L0,5 L10,10 z" fill="currentColor" fill-opacity="0.75"/></marker>'
                f'<marker id="arr-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{ACCENT}"/></marker>'
                f'<marker id="arr-a-s" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M10,0 L0,5 L10,10 z" fill="{ACCENT}"/></marker>'
                '</defs>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(claim)}" '
                f'font-family="ui-sans-serif, -apple-system, \'Segoe UI\', Helvetica, Arial, sans-serif" style="max-width:100%;height:auto">'
                f'<title>{escape(title)}</title>{defs}' + "".join(self.out) + "</svg>")


# =============================================================================================================
def system(bg):
    f = Fig(1560, 1000, bg)
    # ---- client + edge
    f.group(20, 50, 250, 440, "Seller's phone or laptop")
    f.box(40, 90, 210, 100, "Next.js app (installable PWA)", ["Create → Progress → Results", "polls the job every 1.5 s"])
    f.box(40, 210, 210, 70, "Browser storage", ["draft autosave (text only)"])
    f.box(40, 300, 210, 70, "Camera + share sheet", ["take photos · share video + deck"])
    f.box(40, 390, 210, 70, "Edits copy in place", ["saved on blur → PATCH /copy"])
    f.group(320, 50, 250, 440, "Edge on your own machine")
    f.box(340, 90, 210, 80, "Cloudflare quick tunnel", ["public HTTPS URL, changes each run"])
    f.box(340, 200, 210, 80, "Access gate", ["random code in a cookie", "401 on every /api call without it"])
    f.box(340, 310, 210, 90, "Next.js server", ["serves the UI", "proxies /api/* to FastAPI", "(phone talks to ONE origin)"])
    f.arrow([(250, 130), (340, 130)], "HTTPS", dy=-8)
    f.arrow([(445, 170), (445, 200)])
    f.arrow([(445, 280), (445, 310)])

    # ---- backend frame
    f.group(616, 50, 650, 930, "FastAPI backend (Python)")
    f.box(640, 90, 190, 100, "API routes", ["uploads · analyze · generations", "copy · reassemble · kit.zip", "publish · connections"])
    f.box(860, 90, 190, 100, "Job orchestrator", ["background thread", "stage state machine", "real progress % per stage"])
    f.store(1080, 90, 170, 100, "Vault", ["Shopify token", "Fernet-encrypted at rest"])
    f.store(640, 230, 190, 70, "SQLite", ["jobs · assets · connections"])
    f.store(1060, 230, 190, 70, "Disk", ["uploads/ · outputs/ (UUID names)"])
    f.arrow([(550, 355), (590, 355), (590, 140), (640, 140)])
    f.text(556, 376, "photos, facts,", size=11, opacity=0.85, halo=True)
    f.text(556, 391, "edits (JSON)", size=11, opacity=0.85, halo=True)
    f.arrow([(830, 140), (860, 140)])
    f.arrow([(890, 190), (890, 265), (830, 265)], "state · partial copy", at=0, dx=8, dy=-14, anchor="start")
    f.arrow([(1020, 190), (1020, 265), (1060, 265)], "files", at=0, dx=8, dy=-14, anchor="start")

    # ---- two lanes (visual left, language right; Ollama sits next to the language lane)
    f.group(640, 340, 290, 470, "Visual lane", accent=True)
    f.group(960, 340, 290, 470, "Language lane", accent=True)
    f.arrow([(955, 190), (955, 322), (785, 322), (785, 372)], None, accent=True)
    f.arrow([(955, 322), (1105, 322), (1105, 372)], "starts BOTH at once", at=0, dx=-78, dy=-8, accent=True)
    V = [("1  Measure each photo", "NumPy: sharpness · brightness · colour"), ("2  Cut out the product", "rembg (U2-Net) at full resolution"),
         ("3  Refine the product itself", "OpenCV: denoise · 2× super-res · contrast"), ("4  Backdrop from photo stats", "Pillow: shadow · reflection · light sweep"),
         ("5  Render 4–6 shots", "FFmpeg: camera moves + crossfades")]
    L = [("1  Build prompts", "facts · tone · platform · goal"), ("2  Split kit into 5–6 parts", "listing · social · video · per platform"),
         ("3  Parallel LLM calls", "Ollama, OLLAMA_NUM_PARALLEL=4"), ("4  Safety post-check", "risky claims · forbidden words · placeholders"),
         ("5  Publish parts as they finish", "UI shows copy at ~20 s")]
    for lane, items, x in ((V, V, 655), (L, L, 975)):
        for i, (t, sub) in enumerate(items):
            f.box(x, 372 + i * 78, 260, 58, t, [sub], title_size=12)
            if i:
                f.arrow([(x + 130, 372 + i * 78 - 20), (x + 130, 372 + i * 78)], None)

    # ---- merge
    f.arrow([(785, 810 - 8), (785, 836)], None, accent=True)
    f.arrow([(1105, 810 - 8), (1105, 836)], None, accent=True)
    f.box(655, 838, 580, 84, "Image deck (Pillow), then final video (FFmpeg)",
          ["deck: hero · benefits · close-up · angles · CTA, laid out from the finished copy",
           "video: motion clip + text cards, ffprobe-checked ≈ 10 s, H.264 yuv420p (plays on iPhone)"], kind="accent", title_size=12)
    f.text(945, 950, "The two lanes only meet here. A copy edit re-runs just this box, not the lanes.", size=11, anchor="middle", opacity=0.9, fill=ACCENT)

    # ---- local model server + outside
    f.group(1316, 440, 224, 200, "Local model server")
    f.box(1336, 480, 184, 130, "Ollama", ["Gemma 3 12B writes copy", "Gemma 3 4B reads photos", "(set at start-up)"])
    f.arrow([(1235, 545), (1336, 545)], "5–6 JSON calls", dx=-14, dy=17, anchor="end")
    f.group(1316, 680, 224, 300, "Outside (optional)")
    f.box(1336, 720, 184, 90, "Shopify Admin API", ["creates a DRAFT product", "photos + video + copy"])
    f.box(1336, 830, 184, 60, "ElevenLabs", ["voiceover (not built yet)"], kind="planned")
    f.box(1336, 905, 184, 60, "Sentry", ["stage traces (not wired)"], kind="planned")
    f.arrow([(1250, 140), (1290, 140), (1290, 765), (1336, 765)], None, dashed=True)
    f.text(1298, 404, "publish draft", size=11, opacity=0.9, halo=True)
    f.text(1298, 419, "(token from the vault)", size=11, opacity=0.7, halo=True)
    return f.svg("SellCraft system architecture", "How a photo and a few facts become a kit: two lanes run in parallel inside the FastAPI backend and meet at the deck and final video")


def pipeline(bg):
    f = Fig(1500, 560, bg)
    x0, scale = 230, 18.0   # 18 px per second
    sx = lambda s: x0 + s * scale
    for s in range(0, 71, 10):
        f.out.append(f'<line x1="{sx(s)}" y1="54" x2="{sx(s)}" y2="290" stroke="currentColor" stroke-opacity="0.12"/>')
        f.text(sx(s), 40, f"{s} s", size=11, anchor="middle", opacity=0.6)
    f.text(20, 40, "Time since you tap Generate", size=11, weight=700, opacity=0.6)
    # sequential
    f.text(20, 92, "SEQUENTIAL", size=12, weight=700)
    f.text(20, 110, "what the first version did", size=11, opacity=0.65)
    f.box(sx(0), 70, 45 * scale, 40, "Write copy (Gemma 12B)", [], title_size=12)
    f.box(sx(45), 70, 16 * scale, 40, "Build video", [], title_size=12)
    f.text(sx(61) + 14, 95, "≈ 65 s", size=13, weight=700, opacity=0.9)
    # overlapped
    f.text(20, 202, "OVERLAPPED", size=12, weight=700, fill=ACCENT)
    f.text(20, 220, "what runs now", size=11, opacity=0.65)
    f.text(sx(0) - 10, 174, "language lane", size=11, anchor="end", opacity=0.75)
    f.text(sx(0) - 10, 246, "visual lane", size=11, anchor="end", opacity=0.75)
    f.box(sx(0), 150, 45 * scale, 40, "Write copy: 5–6 parts in parallel", [], title_size=12)
    for s in (20, 33):
        f.out.append(f'<circle cx="{sx(s)}" cy="190" r="4" fill="{ACCENT}"/>')
    f.text(sx(20), 210, "first parts appear in the editor (read-only)", size=11, anchor="middle", fill=ACCENT, halo=True)
    f.box(sx(0), 226, 16 * scale, 40, "Refine photos + render shots", [], title_size=12, kind="accent")
    f.out.append(f'<line x1="{sx(16) + 6}" y1="246" x2="{sx(45) - 4}" y2="246" stroke="currentColor" stroke-opacity="0.4" stroke-dasharray="3 4"/>')
    f.text(sx(31), 238, "video ready at 16 s, waits for the copy", size=11, anchor="middle", opacity=0.7, halo=True)
    f.box(sx(45), 150, 4 * scale, 116, "", [], kind="accent")
    f.text(sx(45) + 36, 204, "deck", size=11, anchor="middle", weight=700, fill=ACCENT)
    f.text(sx(45) + 36, 219, "+ text", size=11, anchor="middle", fill=ACCENT)
    f.text(sx(49) + 14, 214, "≈ 49 s", size=13, weight=700, fill=ACCENT)
    f.text(sx(49) + 14, 232, "copy visible from ~20 s", size=11, fill=ACCENT)
    # why
    f.text(20, 330, "Where the saving comes from (measured on an 18 GB Mac)", size=12, weight=700)
    pts = ["Video needs only the photos, never the copy, so it starts at t = 0 instead of waiting.",
           "Ollama serves requests together (OLLAMA_NUM_PARALLEL=4). Decoding is memory-bound, so 3 parallel calls took 19 s instead of 37 s.",
           "Each parallel call re-reads its prompt, so every part gets only the sections it needs: 6 parts went from 63 s to 46 s.",
           "A leftover [placeholder] is stripped in place and only parts that really failed are re-run, so there is no second full round."]
    for k, t in enumerate(pts):
        f.text(20, 354 + k * 22, "•  " + t, size=12, opacity=0.88)
    # states
    f.text(20, 462, "Job states (stored in SQLite, polled by the UI)", size=12, weight=700)
    y = 478
    chars = 7.0
    st = [("queued", 20), ("generating_copy", 140), ("generating_video", 320), ("deck", 520), ("assembling_video", 600), ("completed", 800)]
    for name, x in st:
        f.box(x, y, len(name) * chars + 26, 30, name, [], title_size=11, kind="accent" if name in ("generating_copy", "generating_video") else "normal")
    f.arrow([(20 + 6 * chars + 26, y + 15), (140, y + 15)])
    f.arrow([(140 + 15 * chars + 26, y + 15), (320, y + 15)], "run together", dy=-9, accent=True)
    f.arrow([(320 + 16 * chars + 26, y + 15), (520, y + 15)])
    f.arrow([(520 + 4 * chars + 26, y + 15), (600, y + 15)])
    f.arrow([(600 + 16 * chars + 26, y + 15), (800, y + 15)])
    f.box(960, y, 70, 30, "failed", [], title_size=11, kind="planned")
    f.text(1046, y + 20, "a failed video keeps the copy; Try again skips the copy step", size=11, opacity=0.8)
    return f.svg("Pipeline timing", "Copy and video are produced at the same time and meet at the deck and final video, so the wait is the slower lane plus a few seconds, not the sum")


def finetune(bg):
    f = Fig(1560, 700, bg)
    # data
    f.group(20, 50, 230, 250, "1  Data (synthetic)")
    f.box(40, 90, 190, 80, "Fact-set generator", ["12 categories, 4 tiers", "sparse · medium · dense · tricky"])
    f.box(40, 190, 190, 90, "400 train · 60 test", ["test has 2 unseen categories", "no product in both splits"])
    f.arrow([(135, 170), (135, 190)], None)
    # teacher loop
    f.group(300, 50, 620, 250, "2  Teacher writes, checker judges")
    f.box(320, 100, 190, 100, "Teacher model", ["Qwen3.5-397B on Tinker", "whole kit in one call", "+ audit by a second model (v2)"], kind="accent")
    f.box(580, 100, 190, 100, "Checker + judge", ["code: claims, numbers (digits", "and words), forbidden words;", "Gemma 12B judge reads each kit"])
    f.box(810, 100, 100, 100, "Keep", ["v2: 60 of 68", "kits passed"])
    f.arrow([(250, 235), (300, 235), (300, 150), (320, 150)], "facts", at=1, dx=-20, dy=-8, anchor="end")
    f.arrow([(510, 150), (580, 150)], "draft kit", dy=-8)
    f.arrow([(770, 150), (810, 150)], "clean", dy=-8)
    f.arrow([(675, 200), (675, 262), (415, 262), (415, 200)], "violations → revise (max 2 rounds), with the checker's findings", at=1, dy=16, accent=True)
    f.text(910, 285, "8 kits never got clean: dropped", size=11, anchor="end", opacity=0.65)
    # student training
    f.group(960, 50, 580, 250, "3  Student learns (Tinker, LoRA)")
    f.box(980, 100, 170, 100, "Per-part examples", ["v2: 319 chat examples", "student prompt = the app's", "own prompt (no teacher note)"])
    f.box(1170, 100, 170, 100, "LoRA fine-tune", ["Qwen3.5-4B, rank 32", "3 epochs, loss on the", "answer tokens only"], kind="accent")
    f.box(1360, 100, 160, 100, "Checkpoint", ["tinker:// sampler", "weights (small LoRA", "adapter, not a model)"])
    f.arrow([(910, 150), (980, 150)], "per part", dy=-8)
    f.arrow([(1150, 150), (1170, 150)], None)
    f.arrow([(1340, 150), (1360, 150)], None)
    # eval
    f.group(300, 340, 1240, 330, "4  Does it work? 60 held-out products (Gemma rows: first 20)")
    f.box(330, 390, 220, 110, "Gemma 3 4B (baseline)", ["35% clean kits", "judge flags 5% of kits", "13.5 s per kit (local)"])
    f.box(580, 390, 220, 110, "Gemma 3 12B (baseline)", ["50% clean kits", "judge flags 15% of kits", "48.7 s per kit (local)"])
    f.box(830, 390, 250, 110, "Qwen3.5-4B tuned v2", ["88% clean (untuned 18%, v1 65%)", "judge flags 20% of kits", "4.3 s per kit (hosted, not local)"], kind="accent")
    f.arrow([(1440, 200), (1440, 330), (955, 330), (955, 390)], "sample the checkpoint on the 60 test products", at=1, dy=-8, accent=True)
    f.box(1120, 390, 190, 110, "Manual read", ["I read every flag: v2 has", "~1 real, 1 borderline", "of 20 (v1: ~5)"])
    f.box(1340, 390, 170, 110, "Local run", ["merge adapter → GGUF", "→ ollama create", "not done yet"], kind="planned")
    f.arrow([(1080, 445), (1120, 445)], None)
    f.arrow([(1310, 445), (1340, 445)], None, dashed=True)
    f.text(930, 540, "v1 scored 93% on a word-list checker; the independent judge disagreed, which is why v2 exists.", size=11, anchor="middle", opacity=0.8)
    f.text(930, 560, "The 60 test products are never used to build training data (the teacher script refuses the test split).", size=11, anchor="middle", opacity=0.8)
    f.text(930, 600, "Spend capped in code; Tinker usage page: $5.41 of the $10 credit. Judge sample is small (20 kits) and Gemma 12B grades its own output too.", size=11, anchor="middle", opacity=0.8, fill=ACCENT)
    return f.svg("Fine-tuning loop", "A strong teacher writes copy, a code checker rejects anything that breaks the rules, and only clean kits train a small student that is then tested against the Gemma baselines on held-out products")


FIGS = [
    ("system", system, "1. Where everything runs", "Every component and what moves between them. The orange parts are the mechanism worth understanding: the two lanes start together and only meet at the deck and final video."),
    ("pipeline", pipeline, "2. Why the wait is shorter", "Timing of one kit with Gemma 12B and one or two photos (typical, measured on an 18 GB Mac). Copy and video overlap, so the wait is the slower lane plus a few seconds."),
    ("finetune", finetune, "3. The fine-tuning experiment", "How a strong teacher plus a rule-checking script produce training data for a small model, and how the result is judged against the Gemma baselines."),
]

if __name__ == "__main__":
    here = Path(__file__).parent
    page = []
    for key, fn, title, caption in FIGS:
        (here / f"architecture-{key}.svg").write_text(fn("#ffffff").replace("<svg ", '<svg style="color:#1b1815;background:#ffffff;max-width:100%;height:auto" ', 1).replace(' style="max-width:100%;height:auto"', "", 1))
        page.append(f'<figure><h2>{escape(title)}</h2>{fn("var(--bg)")}<figcaption>{escape(caption)}</figcaption></figure>')
    (here / "architecture.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SellCraft architecture</title><style>
:root{{--bg:#fafaf9;--fg:#1b1815}}@media(prefers-color-scheme:dark){{:root{{--bg:#0b0b0c;--fg:#f4efe8}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 ui-sans-serif,-apple-system,Helvetica,Arial,sans-serif}}
main{{max-width:1560px;margin:0 auto;padding:32px 24px 64px}}h1{{font-size:28px;letter-spacing:-.03em;margin:0 0 4px}}
p.lede{{color:color-mix(in srgb,var(--fg) 65%,transparent);margin:0 0 32px;max-width:70ch}}
figure{{margin:0 0 56px}}h2{{font-size:18px;margin:0 0 12px;letter-spacing:-.02em}}figcaption{{margin-top:10px;max-width:90ch;color:color-mix(in srgb,var(--fg) 70%,transparent)}}
svg{{display:block;width:100%;height:auto;overflow:visible}}</style></head><body><main>
<h1>SellCraft AI: how it works</h1><p class="lede">One product photo and a few facts become refined photos, an image deck, a 10-second video and platform copy. Open models run on the seller's own machine.</p>
{''.join(page)}</main></body></html>""")
    print("wrote", [p.name for p in sorted(here.glob("architecture*"))])
