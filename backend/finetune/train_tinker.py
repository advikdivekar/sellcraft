"""LoRA supervised fine-tuning on Tinker (cross-entropy on the assistant tokens only).

   python -m finetune.train_tinker --base-model Qwen/Qwen3.5-4B --dry-run          # free: tokenize, show size + price
   python -m finetune.train_tinker --base-model Qwen/Qwen3.5-4B --epochs 3 --budget-usd 2.5

The training prompt is EXACTLY the prompt the app sends (no shape hint, thinking off), so the tuned model is later used the
same way the app uses any model."""
import argparse
import asyncio
import json
import random
from pathlib import Path

from .runners import load_env

DATA = Path(__file__).parent / "data"
# USD per million TRAINING tokens, Tinker Models & Pricing page (Oct 2026)
TRAIN_PRICES = {"Qwen/Qwen3.5-4B": 0.737, "Qwen/Qwen3.5-9B": 1.463, "Qwen/Qwen3-8B": 0.44, "openai/gpt-oss-20b": 0.396}


def load_examples(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def split_prompt_completion(tok, messages: list[dict]) -> tuple[list[int], list[int]]:
    """Token ids for (prompt, completion). The completion includes the end-of-turn token so the model learns to stop."""
    kw = dict(tokenize=False, enable_thinking=False)
    prompt_text = tok.apply_chat_template(messages[:-1], add_generation_prompt=True, **kw)
    full_text = tok.apply_chat_template(messages, **kw)
    if full_text.startswith(prompt_text):
        completion_text = full_text[len(prompt_text):]
    else:  # template re-renders the last turn differently: fall back to content + end-of-turn
        completion_text = messages[-1]["content"] + (tok.eos_token or "")
    return tok.encode(prompt_text, add_special_tokens=False), tok.encode(completion_text, add_special_tokens=False)


def make_datum(types, prompt: list[int], completion: list[int]):
    full = prompt + completion
    return types.Datum(
        model_input=types.ModelInput.from_ints(tokens=full[:-1]),
        loss_fn_inputs=dict(weights=[0.0] * (len(prompt) - 1) + [1.0] * len(completion), target_tokens=full[1:]),
    )


def plan(tok, examples: list[dict], epochs: int, price: float) -> dict:
    pairs = [split_prompt_completion(tok, e["messages"]) for e in examples]
    tokens = sum(len(p) + len(c) for p, c in pairs)
    return {"examples": len(pairs), "tokens_per_epoch": tokens, "train_tokens": tokens * epochs,
            "est_usd": round(tokens * epochs / 1_000_000 * price, 2), "pairs": pairs}


def load_tokenizer(base_model: str):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(base_model)


async def train(a, pairs):
    import tinker
    from tinker import types
    load_env()
    svc = tinker.ServiceClient()
    tc = svc.create_lora_training_client(base_model=a.base_model, rank=a.rank, user_metadata={"project": "sellcraft-copy"})
    tinker_tok = tc.get_tokenizer()
    probe = pairs[0][0][:64]
    if tinker_tok.decode(probe) != load_tokenizer(a.base_model).decode(probe):
        raise SystemExit("The local tokenizer and Tinker's tokenizer disagree; aborting before spending anything.")
    datums = [make_datum(types, p, c) for p, c in pairs]
    rng = random.Random(a.seed)
    steps_per_epoch = (len(datums) + a.batch_size - 1) // a.batch_size
    total = steps_per_epoch * a.epochs
    step = 0
    for epoch in range(a.epochs):
        rng.shuffle(datums)
        for i in range(0, len(datums), a.batch_size):
            lr = a.lr * max(0.1, 1 - step / max(total, 1))  # linear decay to 10%
            fwd = await tc.forward_backward_async(data=datums[i:i + a.batch_size], loss_fn="cross_entropy")
            res = await fwd.result_async()
            opt = await tc.optim_step_async(types.AdamParams(learning_rate=lr))
            await opt.result_async()
            step += 1
            if step % 5 == 0 or step == total:
                print(f"epoch {epoch + 1}/{a.epochs} step {step}/{total} loss={getattr(res, 'loss', '?')} lr={lr:.2e}", flush=True)
    ckpt = tc.save_weights_for_sampler(a.name).result()
    print("saved sampler weights:", ckpt.path)
    return ckpt.path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-model", default="Qwen/Qwen3.5-4B")
    ap.add_argument("--data", type=Path, default=DATA / "sft_train.jsonl")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--rank", type=int, default=32)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--name", default="sellcraft-copy-v1")
    ap.add_argument("--budget-usd", type=float, default=2.0, help="refuses to start if the estimate exceeds this")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    price = TRAIN_PRICES.get(a.base_model)
    if not price:
        raise SystemExit(f"No known training price for {a.base_model}; add it to TRAIN_PRICES so the cap can work.")
    examples = load_examples(a.data)
    tok = load_tokenizer(a.base_model)
    p = plan(tok, examples, a.epochs, price)
    print(f"{p['examples']} examples, {p['tokens_per_epoch']} tokens/epoch, {p['train_tokens']} training tokens, estimated ${p['est_usd']} (cap ${a.budget_usd})")
    prompt, comp = p["pairs"][0]
    print("--- example 1: prompt tail ---\n" + tok.decode(prompt[-60:]) + "\n--- completion (trained on) ---\n" + tok.decode(comp)[:400])
    if a.dry_run:
        return None
    if p["est_usd"] > a.budget_usd:
        raise SystemExit(f"Estimated ${p['est_usd']} exceeds the ${a.budget_usd} cap. Lower --epochs or raise --budget-usd.")
    path = asyncio.run(train(a, p["pairs"]))
    out = DATA.parent / "results" / f"checkpoint-{a.name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"base_model": a.base_model, "sampler_path": path, "epochs": a.epochs, "examples": p["examples"], "lr": a.lr, "rank": a.rank}, indent=1))
    print("wrote", out)
    return path


if __name__ == "__main__":
    main()
