# Results

Everything here is reproducible from files in `backend/finetune/results/`. All numbers are on **60 held-out synthetic fact sets**
that the training pipeline refuses to read (`finetune/teacher.py` rejects the test split). Nothing is real seller data.

## 1. Rule-following (deterministic checker), n = 60

A kit is "clean" when it has **no hard violation**: an unsupported claim (a praise word, audience or occasion the facts don't give),
an invented number (digits or number words), a forbidden word, a placeholder, empty required fields or invalid JSON.
Every result file was **re-scored with the current checker** (`python -m finetune.rescore`), so old and new runs are comparable.

| Model | Clean kits | 95% CI | Hard violations / kit | Unsupported claim | Missing facts flagged |
|---|---|---|---|---|---|
| Qwen3.5-4B base | 18% | 10–28% | 1.38 | 82% | 91% |
| Gemma 3 4B | 23% | 13–35% | 1.03 | 75% | 77% |
| Gemma 3 12B | 45% | 33–57% | 0.70 | 55% | 91% |
| **Mochi fine-tune v1** (Qwen3.5-4B + LoRA) | 65% | 53–77% | 0.43 | 33% | 100% |
| **Mochi fine-tune v2** (Qwen3.5-4B + LoRA) | **88%** | **78–95%** | **0.15** | **12%** | **100%** |

v1 looked like 93% clean under the checker it was trained against. After the checker was tightened (number words, urgency,
occasions) the same outputs score 65%. v2 was trained on kits that passed both the tighter checker and an independent judge.

## 2. Independent judge (a different model family), n = 30 per model

The checker is a fixed word list, and the fine-tune was trained against it, so it can be gamed. As a second opinion, Gemma 3 12B
reads each kit next to its facts and lists every statement the facts don't support (`finetune/judge.py`).

| Model | Kits with an unsupported statement | 95% CI | Flags / kit | 95% CI |
|---|---|---|---|---|
| Qwen3.5-4B base | 23% | 10–40% | 0.43 | 0.10–0.83 |
| fine-tune v1 | 33% | 17–50% | 0.63 | 0.20–1.17 |
| **fine-tune v2** | 20% | 7–37% | 0.20 | 0.07–0.37 |
| Gemma 3 4B | 20% | 7–37% | 0.20 | 0.07–0.37 |
| Gemma 3 12B | 13% | 3–27% | 0.13 | 0.03–0.27 |

## What the two tables say, honestly
- **The fine-tune clearly learned the rules it was trained on.** 18% → 88% clean on the checker, and the gap to Gemma 12B (45%) is well
  outside the confidence intervals.
- **On the independent judge the picture is more modest.** v2 roughly halves the base model's flags per kit (0.43 → 0.20) and is level
  with Gemma 3 4B, but the intervals overlap with the base, and Gemma 3 12B is lower still. With n = 30 we can't claim more than that.
- **v1 was worse than its base on the judge** (0.63 vs 0.43 flags/kit): it had learned to pass the word list while still embellishing.
  That is the reason v2 exists, and v2 removes that gap.
- **The judge is Gemma**, so it may be lenient toward Gemma's own writing. That bias favours the Gemma rows, i.e. it works against the
  fine-tune's claim, not for it.

## 3. Speed and cost

| | Seconds per kit | Where | Marginal cost per 1,000 kits |
|---|---|---|---|
| Fine-tune v2 | 4.9 (mean of 60, includes network) | Tinker sampling (cloud) | about $3 (2,960 tokens/kit at the $1.005 per million listed for Qwen3.5-4B sampling) |
| Gemma 3 4B | 13.5 | your computer | $0 (electricity) |
| Gemma 3 12B | 48.7 | your computer | $0 (electricity) |

Gemma timings are from the earlier uncontended 20-kit runs; the 60-kit Gemma runs shared the GPU with other work, so their wall-clock
is not used. The cost uses total prompt+completion tokens at the sampling rate, which over-estimates. Training spend was not recorded
in the result files, so it is not claimed here.

**In the app** (end to end, 4 photos, GPU otherwise idle): the default "Fast" setting (Gemma 3 4B) finishes the whole kit,
including studio photos, deck and video, in about 18 seconds; "Best quality" (Gemma 3 12B) takes about 57 seconds.

## Limits
- Synthetic fact sets and a checker that also filtered the training data: strong evidence the model follows the rules, weaker
  evidence about real sellers' products.
- Judge n = 30 per model; intervals are wide.
- The fine-tuned model runs on Tinker today, so its inputs leave the machine. The app's default (Gemma via Ollama) stays local.
- No real-user result yet.

## Reproduce
```bash
cd backend && export PYTHONPATH=.
python -m finetune.eval --provider ollama --model gemma3:12b --out finetune/results/gemma3-12b-n60.json
python -m finetune.rescore finetune/results/*.json            # the table in section 1
python -m finetune.judge --files <result files> --limit 30    # the table in section 2
```
