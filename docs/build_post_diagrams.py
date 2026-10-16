"""Diagrams drawn for the DEV post: 860 px wide with 14-16 px text so they stay readable in a narrow column.
The full-size architecture figures (build_diagrams.py) are for the repo docs; these carry the same facts, simplified.
Run:  python3 docs/build_post_diagrams.py   (writes docs/images/post/*.svg; render_post_diagrams.mjs makes the PNGs)"""
from html import escape
from pathlib import Path

INK, ACC, GREY = "#1b1815", "#ea580c", "#8a8a8a"
W = 860


class D:
    def __init__(self, h):
        self.h, self.o = h, []

    def text(self, x, y, t, size=15, weight=400, anchor="middle", fill=INK, op=1.0):
        self.o.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}" fill-opacity="{op}">{escape(t)}</text>')

    def box(self, x, y, w, h, title, subs=(), acc=False):
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{"#fdeee3" if acc else "#f4f4f4"}" stroke="{ACC if acc else GREY}" stroke-width="1.8"/>')
        n = len(subs)
        top = y + (h - (18 + n * 21)) / 2 + 16
        self.text(x + w / 2, top, title, size=16, weight=700)
        for i, s in enumerate(subs):
            self.text(x + w / 2, top + 24 + i * 21, s, size=14, op=0.78)

    def group(self, x, y, w, h, label, acc=False):
        c = ACC if acc else GREY
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="none" stroke="{c}" stroke-width="1.6" stroke-dasharray="6 6"/>')
        self.text(x + 16, y + 26, label.upper(), size=13, weight=700, anchor="start", fill=c)

    def arrow(self, x1, y1, x2, y2, acc=False, label=None, lx=0, ly=-8, anchor="middle"):
        c = ACC if acc else "#555"
        self.o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="2" marker-end="url(#a{"a" if acc else ""})"/>')
        if label:
            self.text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, size=14, anchor=anchor, fill=c, weight=600)

    def svg(self):
        defs = ('<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker>'
                f'<marker id="aa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{ACC}"/></marker></defs>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {self.h}" width="{W}" height="{self.h}" '
                f'font-family="-apple-system, \'Segoe UI\', Helvetica, Arial, sans-serif">{defs}<rect width="{W}" height="{self.h}" fill="#ffffff"/>'
                + "".join(self.o) + "</svg>")


def chain(d, x, y, w, items, h=72, gap=30):
    for i, (t, subs, acc) in enumerate(items):
        d.box(x, y, w, h, t, subs, acc)
        if i < len(items) - 1:
            d.arrow(x + w / 2, y + h, x + w / 2, y + h + gap, acc=acc)
        y += h + gap
    return y - gap


def system():
    d = D(850)
    d.box(180, 20, 500, 74, "Your photos + a few facts", ["up to 5 photos, from your phone or laptop"])
    d.arrow(430, 94, 215, 140, acc=True)
    d.arrow(430, 94, 645, 140, acc=True)
    d.text(430, 128, "both lanes start at once", size=14, fill=ACC, weight=700)
    d.group(20, 140, 400, 440, "Visual lane", acc=True)
    d.group(440, 140, 400, 440, "Language lane", acc=True)
    vis = [("Measure each photo", ["sharpness, brightness, noise"]), ("Cut out the product", ["rembg, at full resolution"]),
           ("Refine the product pixels", ["denoise, 2x upscale, contrast"]), ("Pick a backdrop", ["chosen from what the photo shows"]),
           ("Render the studio shots", ["still, marketplace photo, PNG"])]
    lang = [("Build the prompt", ["7 sections, JSON schema"]), ("Write the copy in parallel parts", ["4 core parts + 1 per platform"]),
            ("Check the copy", ["plain code: claims, numbers, words"]), ("Show flags to the seller", ["missing facts and risky claims"])]
    for col, items in ((40, vis), (460, lang)):
        y = 176
        for i, (t, s) in enumerate(items):
            d.box(col, y, 360, 62, t, s)
            if i < len(items) - 1:
                d.arrow(col + 180, y + 62, col + 180, y + 78)
            y += 78
    d.arrow(215, 580, 380, 626, acc=True)
    d.arrow(645, 580, 480, 626, acc=True)
    d.box(180, 626, 500, 74, "Image deck + 10-second video", ["these need the finished copy and the studio shots"], acc=True)
    d.arrow(430, 700, 430, 736)
    d.box(180, 736, 500, 74, "Your kit: Overview, Copy, Photos, Share", ["the page polls every 1.5 s and shows real progress"])
    return d


def models():
    d = D(560)
    cells = [("Gemma 3 4B", ["Fast copy (the default)", "reads your photos"], False), ("Gemma 3 12B", ["Best-quality copy", "the independent judge"], False),
             ("rembg (U2-Net)", ["cuts the product out", "of its background"], False), ("OpenCV, NumPy, Pillow", ["measure, retouch, build the deck", "deterministic code"], False),
             ("FFmpeg", ["builds the 10-second video", "not generative video"], False), ("Plain-code checker", ["scores and flags the copy", "no model involved"], False),
             ("Qwen3.5-4B + LoRA", ["my fine-tuned copy writer", "hosted on Tinker, not in the app yet"], True)]
    for i, (t, s, acc) in enumerate(cells):
        d.box(20 + (i % 2) * 420, 20 + (i // 2) * 124, 400, 104, t, s, acc)
    d.text(630, 500, "Orange runs on Tinker's cloud.", size=14, weight=700, fill=ACC)
    d.text(630, 524, "Everything else runs on your computer.", size=14, op=0.8)
    return d


def copy():
    d = D(0)
    items = [("Your facts", ["name, price, features, and what's missing"], False), ("Prompt + JSON schema", ["7 sections: facts, platform, tone, style,", "objective, rules, output"], False),
             ("Small parts, in parallel", ["4 core parts + 1 part per platform"], True), ("Merge", ["every part is forced into strict JSON"], False),
             ("Validate", ["a bad call is retried once;", "only the missing parts are redone"], False), ("Plain-code post-check", ["forbidden words, invented numbers,", "unsupported claims"], True),
             ("Flags shown to the seller", ["and sent to Sentry as metadata only"], False)]
    y = chain(d, 130, 20, 600, items, h=84, gap=26)
    d.h = y + 40
    return d


def photo_reading():
    d = D(0)
    items = [("Up to 5 photos", ["JPEG, PNG or WebP; type read from the bytes"], False), ("Shrunk to 768 px", ["so the read is fast"], False),
             ("Gemma 3 4B reads them", ["strict rules: copy what is there, never guess"], False), ("Suggestions only", ["tagged \"From photo, check it\"; you confirm"], True)]
    y = chain(d, 130, 20, 600, items, h=76, gap=30)
    d.h = y + 40
    return d


def studio():
    d = D(0)
    items = [("Measure the photo", ["sharpness, brightness, noise"], False), ("Cut out the product", ["rembg; falls back to a framed photo", "if the cutout looks wrong"], False),
             ("Refine the product's pixels", ["denoise, 2x upscale, local contrast"], False), ("Fix the tone", ["so the product reads clearly"], False),
             ("Choose a backdrop", ["from what the photo shows"], False), ("Compose", ["the product is never repainted"], True),
             ("Outputs", ["studio still 1080x1350, white marketplace photo,", "transparent PNG, video layers, deck slides"], False)]
    y = chain(d, 130, 20, 600, items, h=76, gap=24)
    d.h = y + 40
    return d


def video():
    d = D(0)
    items = [("Plan at least 4 shots", ["from your studio photos"], False), ("Render each shot with FFmpeg", ["up to 3 at once"], False),
             ("Crossfade 0.4 s", ["shots are joined into one clip"], False), ("Text cards from your copy", ["edit the copy: only this layer re-renders"], True),
             ("Check the result", ["10 s (plus or minus 0.5), 1080x1920"], False)]
    y = chain(d, 130, 20, 600, items, h=76, gap=28)
    d.h = y + 40
    return d


def speed():
    d = D(540)
    rows = [("Writing the copy", "Fast mode (Gemma 4B) as the default", 53, 14, "53 s", "14 s"),
            ("One 12B call, split into parallel parts", "", 145, 60, "90 to 145 s", "45 to 60 s"),
            ("Whole kit, four photos (Fast mode)", "", 100, 18, "about 100 s", "about 18 s")]
    y = 20
    for title, sub, b, a, bl, al in rows:
        d.text(20, y + 18, title, size=16, weight=700, anchor="start")
        if sub:
            d.text(20, y + 40, sub, size=14, anchor="start", op=0.75)
            y += 22
        sc = 560 / b
        d.o.append(f'<rect x="20" y="{y + 30}" width="{b * sc}" height="30" rx="6" fill="#d9d9d9"/>')
        d.text(20 + b * sc + 10, y + 51, "before: " + bl, size=14, anchor="start")
        d.o.append(f'<rect x="20" y="{y + 68}" width="{a * sc}" height="30" rx="6" fill="{ACC}"/>')
        d.text(20 + a * sc + 10, y + 89, "after: " + al, size=14, anchor="start", weight=700, fill=ACC)
        y += 138
    d.text(20, y - 10, "Best quality (Gemma 12B) takes about 57 s for the whole kit.", size=14, anchor="start", op=0.8)
    d.h = y + 20
    return d


def finetune():
    d = D(0)
    items = [("Teacher: Qwen3.5-397B-A17B", ["writes marketing kits on Tinker"], False), ("Checker + independent judge", ["reject any kit with an invented claim,", "number or forbidden word"], False),
             ("Revise", ["the teacher fixes it using the findings", "(at most 2 rounds)"], False), ("Keep only clean kits", ["319 kits with zero hard violations"], True),
             ("Train the student", ["Qwen3.5-4B + LoRA, rank 32, 3 epochs"], True), ("Test on 60 held-out products", ["the training code refuses to read them"], False)]
    y = chain(d, 130, 20, 600, items, h=82, gap=26)
    d.text(430, y + 34, "Spend: $5.41 of the $10 Tinker credit", size=14, weight=700, fill=ACC)
    d.h = y + 56
    return d


def evaluation():
    d = D(470)
    d.text(20, 30, "Clean kits (no hard violation)", size=17, weight=700, anchor="start")
    d.text(20, 54, "60 held-out synthetic products, one checker. Bars: share of clean kits. Lines: 95% interval.", size=14, anchor="start", op=0.75)
    x0, sc = 270, 5.6
    for t in (0, 25, 50, 75, 100):
        d.o.append(f'<line x1="{x0 + t * sc}" y1="84" x2="{x0 + t * sc}" y2="384" stroke="#e5e5e5" stroke-width="1.5"/>')
        d.text(x0 + t * sc, 408, f"{t}%", size=13, op=0.7)
    rows = [("Qwen3.5-4B, untuned", 18, 10, 28, False), ("Gemma 3 4B", 23, 13, 35, False), ("Gemma 3 12B", 45, 33, 57, False), ("Mochi fine-tune (v2)", 88, 78, 95, True)]
    for i, (n, v, lo, hi, acc) in enumerate(rows):
        y = 100 + i * 72
        d.text(x0 - 14, y + 26, n, size=15, weight=700 if acc else 400, anchor="end")
        d.o.append(f'<rect x="{x0}" y="{y}" width="{v * sc}" height="40" rx="6" fill="{ACC if acc else "#cfcfcf"}"/>')
        d.o.append(f'<line x1="{x0 + lo * sc}" y1="{y + 20}" x2="{x0 + hi * sc}" y2="{y + 20}" stroke="{INK}" stroke-width="2.4"/>')
        for e in (lo, hi):
            d.o.append(f'<line x1="{x0 + e * sc}" y1="{y + 10}" x2="{x0 + e * sc}" y2="{y + 30}" stroke="{INK}" stroke-width="2.4"/>')
        d.text(x0 + hi * sc + 10, y + 26, f"{v}%", size=16, weight=700, anchor="start", fill=ACC if acc else INK)
    return d


def two_columns(h, left, right, lt, rt, note=None, left_acc=False):
    d = D(h)
    d.group(20, 20, 400, h - 40 - (60 if note else 0), lt, acc=left_acc)
    d.group(440, 20, 400, h - 40 - (60 if note else 0), rt, acc=not left_acc)
    for col, items in ((40, left), (460, right)):
        y = 60
        for t, s in items:
            d.box(col, y, 360, 64, t, s)
            y += 80
    if note:
        for i, line in enumerate(note):
            d.text(430, h - 44 + i * 22, line, size=14, op=0.85, weight=600 if i == 0 else 400)
    return d


def observability():
    return two_columns(600, [("A span per model call", ["model, token counts, latency"]), ("A transaction per job", ["one for each generation job"]), ("An issue per flagged claim", ["which rule fired, and how many"]),
                             ("An event per seller report", ["a section name + a fixed reason code"])],
                       [("Product facts and copy", ["never sent"]), ("Photos and prompts", ["never sent"]), ("Free text from reports", ["not collected at all"]),
                        ("Anything not on the allow-list", ["removed by the scrubber"])],
                       "Sentry sees (metadata only)", "Sentry never sees", ["A canary test plants a fake product in every input path", "and fails if its marker reaches any outgoing payload."], left_acc=False)


def trust():
    d = two_columns(560, [("Your photos and facts", ["uploaded files, UUID names"]), ("All the Gemma calls", ["through Ollama, on your computer"]), ("Studio photos, deck, video", ["built locally with OpenCV and FFmpeg"]),
                          ("Jobs, files, database", ["SQLite and disk on your machine"])],
                    [("A Shopify draft", ["only when you tap it"]), ("Scrubbed Sentry metadata", ["no product text, ever"])],
                    "Stays on your computer", "Can leave (only these)", ["Not in the app: the fine-tune runs on Tinker today,", "so its inputs do leave. The default Gemma path stays local."], left_acc=False)
    return d


if __name__ == "__main__":
    out = Path(__file__).parent / "images" / "post"
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in [("system", system), ("models", models), ("copy", copy), ("photo-reading", photo_reading), ("studio", studio), ("video", video),
                     ("speed", speed), ("finetune", finetune), ("evaluation", evaluation), ("observability", observability), ("trust", trust)]:
        (out / f"{name}.svg").write_text(fn().svg())
        print("wrote", name)
