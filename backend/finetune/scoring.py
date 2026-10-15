"""Scores one generated kit against its fact set, using deterministic checks only (no LLM judge, so the
numbers can't be biased toward any model family).

Hard violations make a kit unusable without human repair; soft ones are quality warnings."""
import json
import re
from collections import Counter

from app.schemas import CopyOutput, ProductInput
from app.services.copy import PLACEHOLDER, REQUIRED_NONEMPTY, _strip_placeholders, normalize, risky_terms
from app.services.prompts import PLATFORM_FIELDS
from app.schemas import Platform

HARD_CODES = ["invalid_output", "empty_required", "placeholder", "forbidden_word", "unsupported_claim", "invented_number"]
SOFT_CODES = ["hook_too_long", "voiceover_too_long", "storyboard_beats", "missed_missing_info", "false_missing_info"]
LABEL_KEYS = {"Summary": ["summary"], "Price": ["price", "cost"], "Materials / ingredients": ["material", "ingredient"],
              "Dimensions / specs": ["dimension", "size", "spec"], "Main features": ["feature"], "Verified benefits": ["benefit"],
              "Target audience": ["audience"], "Care / usage": ["care", "usage"]}
NUM = re.compile(r"\d+(?:[.,]\d+)?")


def _facts_blob(p: dict) -> str:
    vals = [p.get("name"), p.get("summary"), p.get("price"), p.get("materials"), p.get("dimensions"), p.get("audience"),
            p.get("brand_name"), p.get("brand_voice"), p.get("care_instructions"), p.get("extra_notes"),
            *(p.get("features") or []), *(p.get("benefits") or [])]
    return " ".join(str(v) for v in vals if v)


def _num_values(text: str) -> set[float]:
    out = set()
    for m in NUM.findall(text):
        try:
            out.add(float(m.replace(",", ".")))
        except ValueError:
            pass
    return out


def _texts(copy: CopyOutput, *, skip: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    """(field, text) for every text-bearing field, flattening lists and per-platform outputs."""
    out: list[tuple[str, str]] = []
    d = copy.model_dump(exclude={"platform_outputs"})
    for k, v in d.items():
        if k in skip:
            continue
        if k == "video_storyboard":
            out += [(k, f"{b['visual']} {b['on_screen_text']}") for b in v]
        elif isinstance(v, list):
            out.append((k, " ".join(map(str, v))))
        else:
            out.append((k, str(v)))
    for plat, fields in copy.platform_outputs.items():
        for k, v in fields.items():
            out.append((f"platform:{plat}", " ".join(v) if isinstance(v, list) else str(v)))
    return out


def score(factset: dict, data: dict | None, error: str | None = None) -> dict:
    """data = the merged JSON the model produced for the whole kit (before any post-processing)."""
    hard: list[dict] = []
    soft: list[dict] = []
    if data is None:
        return {"id": factset["id"], "ok": False, "hard": [{"code": "invalid_output", "detail": error or "no output", "fields": []}],
                "soft": [], "missing_recall": 0.0}
    raw = json.dumps(data, ensure_ascii=False)
    if PLACEHOLDER.search(raw):
        hard.append({"code": "placeholder", "detail": PLACEHOLDER.search(raw).group(0), "fields": []})
    cleaned = _strip_placeholders(data)
    try:
        copy = CopyOutput.model_validate({**normalize(cleaned), "platform_outputs": normalize(cleaned).get("platform_outputs", {})})
    except Exception as e:  # noqa: BLE001
        return {"id": factset["id"], "ok": False, "hard": [{"code": "invalid_output", "detail": str(e)[:120], "fields": []}], "soft": [], "missing_recall": 0.0}
    product = ProductInput.model_validate(factset["product"])
    platforms = [Platform(p) for p in factset["settings"]["platforms"]]

    empty = [f for f in REQUIRED_NONEMPTY if not getattr(copy, f).strip()]
    empty += [f"platform:{p.value}" for p in platforms if not any(copy.platform_outputs.get(p.value, {}).values())]
    if empty:
        hard.append({"code": "empty_required", "detail": ", ".join(empty), "fields": empty})

    body = _texts(copy, skip=("claims_requiring_review", "missing_information"))
    for w in product.forbidden_words:
        pat = re.compile(rf"(?<!\w){re.escape(w.lower())}(?!\w)")
        hit = sorted({f for f, t in body if pat.search(t.lower())})
        if hit:
            hard.append({"code": "forbidden_word", "detail": w, "fields": hit})
    for term in risky_terms(copy, product):
        pat = re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])")
        hard.append({"code": "unsupported_claim", "detail": term, "fields": sorted({f for f, t in body if pat.search(t.lower())})})

    allowed = _num_values(_facts_blob(factset["product"]))
    bad_nums: dict[str, set[str]] = {}
    for f, t in _texts(copy, skip=("claims_requiring_review", "missing_information", "video_generation_prompt", "video_storyboard", "hashtags", "tags", "keywords")):
        for m in NUM.findall(t):
            try:
                v = float(m.replace(",", "."))
            except ValueError:
                continue
            if v not in allowed:
                bad_nums.setdefault(m, set()).add(f)
    for m, fields in bad_nums.items():
        hard.append({"code": "invented_number", "detail": m, "fields": sorted(fields)})

    if len(copy.video_hook.split()) > 8:
        soft.append({"code": "hook_too_long", "detail": str(len(copy.video_hook.split())), "fields": ["video_hook"]})
    if len(copy.voiceover_script.split()) > 25:
        soft.append({"code": "voiceover_too_long", "detail": str(len(copy.voiceover_script.split())), "fields": ["voiceover_script"]})
    if len(copy.video_storyboard) != 4:
        soft.append({"code": "storyboard_beats", "detail": str(len(copy.video_storyboard)), "fields": ["video_storyboard"]})

    said = " ".join(copy.missing_information).lower()
    expected = factset.get("expected_missing") or []
    got = [k for k in expected if any(w in said for w in LABEL_KEYS.get(k, []))]
    recall = len(got) / len(expected) if expected else 1.0
    if expected and recall < 1.0:
        soft.append({"code": "missed_missing_info", "detail": ", ".join(k for k in expected if k not in got), "fields": ["missing_information"]})
    present = [k for k in LABEL_KEYS if k not in expected]
    false = [k for k in present if any(w in said for w in LABEL_KEYS[k])]
    if false:
        soft.append({"code": "false_missing_info", "detail": ", ".join(false), "fields": ["missing_information"]})
    return {"id": factset["id"], "ok": not hard, "hard": hard, "soft": soft, "missing_recall": round(recall, 3)}


def aggregate(results: list[dict]) -> dict:
    """results: [{'score': score(...), 'seconds': float, 'tokens': int}]"""
    n = len(results) or 1
    sc = [r["score"] for r in results]
    hard_kits = Counter(c for s in sc for c in {h["code"] for h in s["hard"]})
    soft_kits = Counter(c for s in sc for c in {h["code"] for h in s["soft"]})
    return {
        "n": len(results),
        "clean_kit_rate": round(sum(s["ok"] for s in sc) / n, 3),
        "hard_violations_per_kit": round(sum(len(s["hard"]) for s in sc) / n, 3),
        "hard_rate": {c: round(hard_kits[c] / n, 3) for c in HARD_CODES},
        "soft_rate": {c: round(soft_kits[c] / n, 3) for c in SOFT_CODES},
        "missing_info_recall": round(sum(s["missing_recall"] for s in sc) / n, 3),
        "mean_seconds": round(sum(r.get("seconds", 0) for r in results) / n, 1),
        "mean_tokens": round(sum(r.get("tokens", 0) for r in results) / n),
    }
