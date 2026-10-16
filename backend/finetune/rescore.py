"""Re-score every saved result file with the CURRENT checker, so old and new models are compared under the same rules,
and add 95% bootstrap confidence intervals.

   python -m finetune.rescore finetune/results/gemma3-4b-n60.json finetune/results/qwen3.5-4b-base.json ... --out finetune/results/RESULTS.md

Why: the checker was tightened after v1 was trained (number words, urgency, occasions). A result file records the score
it got at the time, so mixing files from different days would flatter the older runs."""
import argparse
import json
import random
from pathlib import Path

from .factsets import load
from .scoring import aggregate, score

DATA = Path(__file__).parent / "data"


def bootstrap_ci(values: list[float], reps: int = 2000, seed: int = 7) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(rng.choices(values, k=n)) / n for _ in range(reps))
    return means[int(0.025 * reps)], means[int(0.975 * reps) - 1]


def rescore(path: Path, sets: dict) -> dict:
    res = json.loads(path.read_text())
    items = []
    for i in res["items"]:
        items.append({**i, "score": score(sets[i["id"]], i.get("data"), None if i.get("data") else "no output")})
    clean = [1.0 if i["score"]["ok"] else 0.0 for i in items]
    lo, hi = bootstrap_ci(clean) if clean else (0.0, 0.0)
    agg = aggregate(items)
    return {"model": res["model"], "agg": agg, "ci": (lo, hi), "clean": {i["id"]: i["score"]["ok"] for i in items}}


def table(rows: list[dict]) -> str:
    head = "| Model | n | Clean kits | 95% CI | Hard violations / kit | Unsupported claim | Invented number | Forbidden word | Missing facts flagged | Seconds / kit |"
    lines = [head, "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        a = r["agg"]
        name = r["model"] if len(r["model"]) < 40 else r["model"].split("/")[-1][:40] + "…"
        lines.append(f"| {name} | {a['n']} | {a['clean_kit_rate']:.0%} | {r['ci'][0]:.0%}–{r['ci'][1]:.0%} | {a['hard_violations_per_kit']:.2f} | "
                     f"{a['hard_rate']['unsupported_claim']:.0%} | {a['hard_rate']['invented_number']:.0%} | {a['hard_rate']['forbidden_word']:.0%} | "
                     f"{a['missing_info_recall']:.0%} | {a['mean_seconds']} |")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    sets = {f["id"]: f for f in load(DATA / "test_factsets.jsonl")}
    rows = [rescore(p, sets) for p in a.files]
    md = table(rows)
    print(md)
    if a.out:
        a.out.write_text(md + "\n")


if __name__ == "__main__":
    main()
