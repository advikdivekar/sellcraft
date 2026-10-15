"""Run a model over the held-out fact sets and score it.
   python -m finetune.eval --provider ollama --model gemma3:12b --limit 20 --out finetune/results/gemma3-12b.json"""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.errors import AppError
from app.schemas import CreativeSettings, ProductInput
from app.services.copy import CopyService

from .factsets import load
from .runners import add_provider_args, provider_from_args
from .scoring import aggregate, score

DATA = Path(__file__).parent / "data"


def run_kit(llm, fs: dict) -> dict:
    """Generate one kit exactly the way the app does (parallel parts), but keep the RAW merged output for scoring."""
    product, settings = ProductInput.model_validate(fs["product"]), CreativeSettings.model_validate(fs["settings"])
    svc = CopyService(llm)
    t0 = time.monotonic()
    try:
        data, usage, _ = svc._merge(svc._run(svc._chunks(product, settings)))
        err = None
    except AppError as e:
        data, usage, err = None, {}, f"{e.code}: {e.message}"
    secs = time.monotonic() - t0
    return {"id": fs["id"], "score": score(fs, data, err), "seconds": round(secs, 1),
            "tokens": (usage.get("prompt_tokens") or 0) + (usage.get("completion_tokens") or 0), "data": data}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    add_provider_args(ap)
    ap.add_argument("--split", choices=["train", "test"], default="test")
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--workers", type=int, default=1, help="fact sets in flight at once (keep 1 for a local model)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    llm = provider_from_args(a)
    sets = load(DATA / f"{a.split}_factsets.jsonl")
    sets = sets[: a.limit] if a.limit else sets
    done: list[dict] = []
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for i, r in enumerate(pool.map(lambda fs: run_kit(llm, fs), sets), start=1):
            done.append(r)
            print(f"[{i}/{len(sets)}] {r['id']} {'clean' if r['score']['ok'] else 'VIOLATIONS: ' + ', '.join(sorted({h['code'] for h in r['score']['hard']}))} ({r['seconds']}s)", flush=True)
    out = {"model": a.model, "provider": a.provider, "split": a.split, "aggregate": aggregate(done), "items": done}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps(out["aggregate"], indent=1))


if __name__ == "__main__":
    main()
