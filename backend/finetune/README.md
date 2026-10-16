# Fine-tuning toolkit (teacher -> student)

Goal: a small "Mochi Copy" model that writes teacher-quality, rule-following copy, measured against Gemma baselines.
Everything here is synthetic data and deterministic checks; no real seller data, no LLM judge.

```bash
cd backend
export PYTHONPATH=.

# 1. data (deterministic): 400 train + 60 held-out test fact sets
.venv/bin/python -m finetune.factsets

# 2. baselines on the held-out set (free, local). Use --limit 20 for a quick first look
.venv/bin/python -m finetune.eval --provider ollama --model gemma3:12b --limit 20 --out finetune/results/gemma3-12b.json
.venv/bin/python -m finetune.eval --provider ollama --model gemma3:4b  --limit 20 --out finetune/results/gemma3-4b.json
.venv/bin/python -m finetune.report finetune/results/*.json

# 3. teacher builds the training set (critique-and-revise, hard-check filtered)
export TEACHER_API_KEY=...        # any OpenAI-compatible host serving an open-weight teacher
.venv/bin/python -m finetune.teacher --provider openai --base-url https://.../v1 --model <teacher> --workers 4
# free dry run with a local stand-in teacher:
.venv/bin/python -m finetune.teacher --provider ollama --model gemma3:12b --limit 3 --workers 1
```
`finetune/data/sft_train.jsonl` is chat-format (system/user/assistant per part of the kit) and is what a Tinker LoRA run consumes.
The test split can never be used to build training data (the teacher script refuses).

**What is verified and what isn't:** the generator, scorer, teacher loop and providers are unit-tested with fake models.
The OpenAI-compatible provider is tested against a mocked transport; the Tinker-native provider is written from the docs
and has not been run against a live key.
