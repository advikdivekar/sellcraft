"""Build the supervised fine-tuning set with a strong "teacher" model.

For each synthetic fact set:
  1. The teacher writes every part of the kit, using the SAME prompts the app uses plus a copywriting-style note.
  2. Deterministic checks score the result (finetune.scoring). Hard violations are sent back to the teacher with the
     checker's findings for up to two revisions ("critique and revise").
  3. Only kits that end with ZERO hard violations are kept. `missing_information` is set to the exact ground-truth
     labels for that fact set (we know them, since the facts are synthetic).
  4. One training example per part, in chat format. The student's prompt is the app's normal prompt WITHOUT the teacher
     note, so the student learns to write teacher-quality, rule-following copy from the prompt it will actually get.

   python -m finetune.teacher --provider openai --base-url <url> --model <teacher> --limit 50 --workers 4
"""
import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.errors import AppError
from app.schemas import CreativeSettings, ProductInput
from app.services import prompts
from app.services.copy import RISKY, CopyService, normalize

from .factsets import load
from .runners import add_provider_args, provider_from_args
from .scoring import score

DATA = Path(__file__).parent / "data"

_RISKY = ", ".join(RISKY)
TEACHER_STYLE = """

COPYWRITING STANDARD (teacher note)
You are an elite direct-response copywriter with ten years of experience writing product pages that convert for small
brands. Write vivid, specific, human copy: concrete sensory words, varied sentence rhythm, a strong first line, and no
clichés ("elevate", "game-changer", "unleash"). Short beats long. Never trade truth for flair: every claim, number and
material must come from the PRODUCT FACTS, and anything not given stays out of the copy.

Drafts most often fail in two ways, so check yourself before answering:
1. Praise words the seller never supplied. Do not use any of these unless the word itself appears in the facts: {risky}.
   Also avoid similar flattery (stunning, beautiful, premium quality, must-have, irresistible). When the facts are thin,
   write SHORTER copy.
2. Numbers the seller never supplied. Do not write any number at all (hours, days, percentages, years, quantities) unless
   it appears in the facts. Do not number lists in the text.""".replace("{risky}", _RISKY)

# USD per million tokens to SAMPLE (prompt + completion counted at the same rate, which over-estimates: a safe cap).
# From Tinker's Models & Pricing page, Oct 2026. Unknown models need --price-per-m.
PRICES = {"Qwen/Qwen3.5-397B-A17B": 7.50, "Qwen/Qwen3.8-27B": 5.595, "Qwen/Qwen3.6-35B-A3B": 1.335, "Qwen/Qwen3.5-9B": 0.807,
          "Qwen/Qwen3.5-4B": 1.005, "Qwen/Qwen3-8B": 0.60, "openai/gpt-oss-120b": 0.84, "openai/gpt-oss-20b": 0.45}


def spend_usd(tokens: int, price_per_m: float) -> float:
    return tokens / 1_000_000 * price_per_m


CHUNK_FIELDS = {f"core:{i}": keys for i, keys in enumerate(prompts.CORE_CHUNKS)}


def chunk_data(name: str, data: dict) -> dict:
    if name.startswith("platform:"):
        p = name.split(":", 1)[1]
        return {p: data.get("platform_outputs", {}).get(p, {})}
    return {k: data.get(k) for k in CHUNK_FIELDS[name]}


def chunks_for_fields(fields: list[str], names: list[str]) -> set[str]:
    """Which parts to rewrite. Violations with no field (e.g. a placeholder somewhere) touch every part."""
    if not fields:
        return set(names)
    out: set[str] = set()
    for f in fields:
        if f.startswith("platform:"):
            out.add(f)
        else:
            out.update(n for n, keys in CHUNK_FIELDS.items() if f in keys)
    return out & set(names) or set(names)


def touches(h: dict, part: str) -> bool:
    """Does this violation concern this part of the kit? (No field named = it could be anywhere, so yes.)"""
    if not h.get("fields"):
        return True
    return any(f == part or f in CHUNK_FIELDS.get(part, []) for f in h["fields"])


def problems_text(hard: list[dict]) -> list[str]:
    msg = {"placeholder": "a template placeholder ({detail}) was left in the text; write final wording",
           "forbidden_word": "'{detail}' is a forbidden word; do not use it or any form of it",
           "unsupported_claim": "'{detail}' is not supported by the facts; remove or replace it with something the facts support",
           "invented_number": "the number '{detail}' does not appear in the facts; remove it",
           "empty_required": "these required fields were empty: {detail}",
           "invalid_output": "the output was not valid for the schema: {detail}"}
    out = []
    for h in hard:
        where = f" (in {', '.join(h['fields'])})" if h.get("fields") else ""
        out.append(msg[h["code"]].format(detail=h["detail"]) + where)
    return out


def revise_prompt(user: str, draft: dict, problems: list[str]) -> str:
    return (user + "\n\n## REVISION\nYour previous draft of this part:\n" + json.dumps(draft, ensure_ascii=False) +
            "\n\nAn automatic checker found these problems:\n" + "\n".join(f"- {p}" for p in problems) +
            "\n\nRewrite the draft and fix EVERY problem. Keep what was already good. Use only the facts. Return the same JSON keys.")


def build_one(teacher, fs: dict, *, max_revisions: int = 2, temperature: float = 0.7, mode: str = "kit") -> dict:
    """mode 'kit': one teacher call writes the whole kit (the facts are sent once: ~40% fewer tokens, so cheaper).
    mode 'parts': one call per part, exactly like the app. Either way the STUDENT examples are per part."""
    product, settings = ProductInput.model_validate(fs["product"]), CreativeSettings.model_validate(fs["settings"])
    svc = CopyService(teacher)
    jobs = svc._chunks(product, settings)  # [(name, schema, student_user_prompt)]
    by_name = {n: (schema, user) for n, schema, user in jobs}
    system_t = prompts.SYSTEM_PROMPT + TEACHER_STYLE
    kit_schema = prompts.build_schema(settings.platforms)
    kit_user = prompts.build_user_prompt(product, settings)
    tokens = [0]
    lock = threading.Lock()

    def ask(user: str, schema: dict) -> dict:
        r = teacher.generate_json(system_t, user, schema, temperature=temperature)
        with lock:
            tokens[0] += (r.usage.get("prompt_tokens") or 0) + (r.usage.get("completion_tokens") or 0)
        return r.data

    def call(name: str, user: str):
        return ask(user, by_name[name][0])

    try:
        if mode == "kit":
            full = ask(kit_user, kit_schema)
            parts = {n: chunk_data(n, full) for n, _, _ in jobs}
        else:
            parts = {n: call(n, u) for n, _, u in jobs}
    except AppError as e:
        return {"id": fs["id"], "accepted": False, "rounds": 0, "tokens": tokens[0], "reason": f"{e.code}: {e.message}", "examples": []}

    def merged() -> dict:
        data: dict = {"platform_outputs": {}}
        for n, d in parts.items():
            if n.startswith("platform:"):
                data["platform_outputs"][n.split(":", 1)[1]] = d.get(n.split(":", 1)[1]) or {}
            else:
                data.update(d)
        return data

    sc = score(fs, merged())
    rounds = 0
    while sc["hard"] and rounds < max_revisions and mode == "kit":
        rounds += 1
        try:
            full = ask(revise_prompt(kit_user, merged(), problems_text(sc["hard"])), kit_schema)
            parts = {n: chunk_data(n, full) for n, _, _ in jobs}
        except AppError:
            break
        sc = score(fs, merged())
    while sc["hard"] and rounds < max_revisions and mode == "parts":
        rounds += 1
        fields = sorted({f for h in sc["hard"] for f in h.get("fields", [])})
        for n in sorted(chunks_for_fields(fields, [j[0] for j in jobs])):
            mine = [h for h in sc["hard"] if touches(h, n)]
            try:
                parts[n] = call(n, revise_prompt(by_name[n][1], chunk_data(n, merged()), problems_text(mine or sc["hard"])))
            except AppError:
                pass
        sc = score(fs, merged())
    if sc["hard"]:
        return {"id": fs["id"], "accepted": False, "rounds": rounds, "tokens": tokens[0],
                "reason": "; ".join(f"{h['code']}:{h['detail']}" for h in sc["hard"])[:300], "examples": []}

    final = normalize(merged())  # null -> "" / [] so targets always match the schema the student is trained on
    final["missing_information"] = fs["expected_missing"]  # ground truth, known because the facts are synthetic
    ex = []
    for n, _, user in jobs:
        out = chunk_data(n, final)
        ex.append({"messages": [{"role": "system", "content": prompts.SYSTEM_PROMPT}, {"role": "user", "content": user},
                                {"role": "assistant", "content": json.dumps(out, ensure_ascii=False)}],
                   "meta": {"id": fs["id"], "part": n, "tier": fs.get("tier"), "category": fs.get("category")}})
    return {"id": fs["id"], "accepted": True, "rounds": rounds, "tokens": tokens[0], "reason": "", "examples": ex}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_provider_args(ap)
    ap.add_argument("--split", choices=["train", "test"], default="train")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--max-revisions", type=int, default=2)
    ap.add_argument("--mode", choices=["kit", "parts"], default="kit")
    ap.add_argument("--budget-usd", type=float, default=1.0, help="HARD cap: stops starting new kits once the estimated spend reaches it")
    ap.add_argument("--price-per-m", type=float, default=0.0, help="USD per million sampled tokens (looked up for known models)")
    ap.add_argument("--out", type=Path, default=DATA / "sft_train.jsonl")
    a = ap.parse_args(argv)
    if a.split == "test":
        raise SystemExit("Refusing to build training data from the held-out test split.")
    price = a.price_per_m or (PRICES.get(a.model, 0.0) if a.provider != "ollama" else 0.0)
    if a.provider != "ollama" and not price:
        raise SystemExit(f"No known price for '{a.model}'. Pass --price-per-m so the spend cap can work.")
    teacher = provider_from_args(a)
    log_path = a.out.with_suffix(".log.jsonl")
    done_ids = {json.loads(l)["id"] for l in log_path.read_text().splitlines()} if log_path.exists() else set()
    prior = sum(json.loads(l)["tokens"] for l in log_path.read_text().splitlines()) if log_path.exists() else 0
    sets = [fs for fs in load(DATA / "train_factsets.jsonl") if fs["id"] not in done_ids]
    sets = sets[: a.limit] if a.limit else sets
    a.out.parent.mkdir(parents=True, exist_ok=True)
    ok = rev = n_done = 0
    tok = prior
    stopped = False
    with ThreadPoolExecutor(max_workers=a.workers) as pool, a.out.open("a") as out, log_path.open("a") as log:
        for start in range(0, len(sets), a.workers):
            if spend_usd(tok, price) >= a.budget_usd:
                stopped = True
                break
            batch = sets[start:start + a.workers]
            for r in pool.map(lambda fs: build_one(teacher, fs, max_revisions=a.max_revisions, mode=a.mode), batch):
                n_done += 1
                for e in r["examples"]:
                    out.write(json.dumps(e, ensure_ascii=False) + "\n")
                log.write(json.dumps({k: r[k] for k in ("id", "accepted", "rounds", "tokens", "reason")}) + "\n")
                out.flush(); log.flush()
                ok += r["accepted"]; rev += r["rounds"]; tok += r["tokens"]
                print(f"[{n_done}/{len(sets)}] {r['id']} {'kept' if r['accepted'] else 'REJECTED ' + r['reason'][:80]} (revisions: {r['rounds']}) spend ~${spend_usd(tok, price):.2f}", flush=True)
    print(f"\nkept {ok}/{n_done} kits, {rev} revision rounds, {tok} teacher tokens (~${spend_usd(tok, price):.2f} of ${a.budget_usd:.2f} cap)"
          + (" -- STOPPED at the spend cap" if stopped else "") + f" -> {a.out}")


if __name__ == "__main__":
    main()
