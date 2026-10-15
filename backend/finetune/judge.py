"""An INDEPENDENT second opinion on grounding, because the scorer's claim check is a fixed word list that the fine-tune was
trained against. A local model from a different family than the teacher (Gemma, vs the Qwen teacher) reads each kit next to
its facts and lists every statement the facts don't support. Gemma judging its own outputs may be lenient, which if anything
FLATTERS the baselines, so the direction of the bias is against our claim.

   python -m finetune.judge --files finetune/results/gemma3-12b.json finetune/results/qwen3.5-4b-finetuned.json --limit 20"""
import argparse
import json
from pathlib import Path

from app.services.llm.ollama import OllamaProvider

from .factsets import load
from .scoring import _facts_blob

DATA = Path(__file__).parent / "data"
SYSTEM = """You audit marketing copy for factual grounding. You get the seller's FACTS and a piece of COPY.
List every statement in the COPY that asserts something the FACTS do not support: a product property, material, size, number,
benefit, quality ("durable", "soft"), who it is for, an occasion, availability or urgency ("available now", "limited"), or a promise.
Do NOT flag: rephrasing of a given fact, a statement that names the stated audience ("for gift shoppers" when the audience is gift shoppers),
the product name, the brand name, the call to action wording, or tone and style.
Return JSON only: {"unsupported": ["short quote of each unsupported statement"]}. Use an empty list if everything is supported."""
SCHEMA = {"type": "object", "required": ["unsupported"], "properties": {"unsupported": {"type": "array", "items": {"type": "string"}}}}
FIELDS = ("short_description", "full_description", "social_caption", "ad_headline", "call_to_action", "voiceover_script", "video_hook")


def copy_text(data: dict, platforms: list[str]) -> str:
    parts = [f"{k}: {data[k]}" for k in FIELDS if data.get(k)]
    for p in platforms:
        o = (data.get("platform_outputs") or {}).get(p) or {}
        parts += [f"{p}.{k}: {' '.join(v) if isinstance(v, list) else v}" for k, v in o.items() if v]
    return "\n".join(parts)


def judge_kit(llm, factset: dict, data: dict) -> list[str]:
    from app.services.prompts import clean_fact
    p = {k: ([clean_fact(x) or x for x in v] if isinstance(v, list) else (clean_fact(v) if isinstance(v, str) else v)) for k, v in factset["product"].items()}
    facts = [f"name: {p['name']}"] + [f"{k}: {v}" for k, v in p.items()
                                      if k in ("materials", "dimensions", "audience", "price", "care_instructions", "extra_notes", "brand_name", "summary") and v]
    facts += [f"feature: {x}" for x in p.get("features") or []] + [f"benefit: {x}" for x in p.get("benefits") or []]
    user = "FACTS:\n" + "\n".join(facts) + "\n\nCOPY:\n" + copy_text(data, factset["settings"]["platforms"])
    r = llm.generate_json(SYSTEM, user, SCHEMA, temperature=0.0)
    return [str(x) for x in (r.data.get("unsupported") or []) if str(x).strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--files", nargs="+", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--model", default="gemma3:12b")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "results" / "judge.json")
    a = ap.parse_args(argv)
    sets = {f["id"]: f for f in load(DATA / "test_factsets.jsonl")}
    llm = OllamaProvider(model=a.model, timeout=600)
    report = json.loads(a.out.read_text()) if a.out.exists() else {}
    for fp in a.files:
        res = json.loads(fp.read_text())
        items = [i for i in res["items"] if i.get("data")][: a.limit]
        rows = []
        for i in items:
            flags = judge_kit(llm, sets[i["id"]], i["data"])
            rows.append({"id": i["id"], "flags": flags})
            print(f"{res['model']} {i['id']}: {len(flags)} flagged", flush=True)
        n = len(rows) or 1
        report[res["model"]] = {"n": len(rows), "kits_with_unsupported": round(sum(bool(r["flags"]) for r in rows) / n, 3),
                                "flags_per_kit": round(sum(len(r["flags"]) for r in rows) / n, 2), "rows": rows}
        a.out.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    for m, v in report.items():
        print(f"{m:34s} n={v['n']:3d}  kits with an unsupported claim: {v['kits_with_unsupported']:.0%}  flags/kit: {v['flags_per_kit']}")


if __name__ == "__main__":
    main()
