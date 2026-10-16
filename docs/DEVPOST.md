<!-- DRAFT for DEV. Fill every [TODO] before publishing. Nothing below claims a user, a payment or a result that hasn't happened. -->

# Mochi: one product photo, a few facts, a marketing kit that doesn't make things up

*Hacktoberfest Open-Source AI Challenge, Week 2: Side Hustle*

## What I built
A small-seller studio. You add up to five photos of a product and a few facts, pick a platform, a tone and a style, and it makes:
platform-specific listing copy, studio-style product photos (background removed, re-lit, designed backdrop), an image deck, and a
10-second vertical video ad. The copy is written by an **open-weight model**. The video is image processing and FFmpeg, not generated
footage, and the app says so.

The one rule I cared about: **the copy may only say what the seller said.** Anything missing is listed as missing, and a deterministic
check flags every claim that isn't in the facts, including regulated ones ("reduces wrinkles", "clinically proven").

## Why someone would pay for it
[TODO: the first user. Who they are, what they do today (tools opened, minutes), what they said, whether they'd pay and what they asked
for next. Use their words. If they were lukewarm, say so. Do not write this section until the session has happened.]

## The open pieces, and what each one does
| Piece | Job |
|---|---|
| **Gemma 3** (4B and 12B, through Ollama) | Writes the copy by default, reads the product photos to pre-fill the form, and acts as an independent judge |
| **Qwen3.5-4B + LoRA, trained on Tinker** | A fine-tuned copy writer that follows the grounding rules |
| **Sentry** | Traces every model call and records every flagged claim, without ever seeing product text |
| **Entire** | Records the Claude Code sessions that built this. 113 checkpoints across two sessions are pushed with the repo, and `docs/DECISIONS.md` ties each design decision to the session and commit it came from |

## The fine-tune, and the number I almost reported wrong
I generated 400 synthetic fact sets, held out 60, and had a large open teacher model write and revise kits until each one passed a
deterministic checker. I trained a small student on those kits with LoRA on Tinker.

My first model (v1) scored **93% clean** on the checker. Then I tightened the checker (number words like "fifty", invented urgency,
invented occasions) and re-scored the same outputs: **65%**. The v1 model had learned the checker's word list, not the idea. So I added
an independent judge (a different model family) to the data pipeline and trained v2 only on kits both passed.

On 60 held-out kits, under the same checker:

| Model | Clean kits | 95% CI |
|---|---|---|
| Qwen3.5-4B, untuned | 18% | 10-28% |
| Gemma 3 4B | 23% | 13-35% |
| Gemma 3 12B | 45% | 33-57% |
| Fine-tune v1 | 65% | 53-77% |
| **Fine-tune v2** | **88%** | **78-95%** |

The honest part: the checker is also what filtered the training data. On the independent judge (n=30) the result is more modest. v2
cuts the untuned model's unsupported statements per kit from 0.43 to 0.20 and matches Gemma 3 4B, but the intervals overlap, and
Gemma 3 12B is lower still. v1 was *worse* than its base on the judge (0.63), which is exactly the gap v2 closes.
Full tables and caveats: `docs/RESULTS.md`.

**Why open mattered here:** I could fine-tune the writer for this one job and measure it against its own base, swap models with one
setting, and keep the default path (Gemma through Ollama) entirely on the seller's computer. Where closed would have been better: a
frontier API would probably write nicer prose with no training. I traded that for control and for facts that never leave the machine.
The fine-tune itself runs on Tinker today, so using it means sending facts to a cloud service; it is not wired into the app's default path.

## From about 100 seconds to about 18
Testing on my own phone, a kit took close to two minutes. Stage timings in the job record showed why: copy took 52-105 s, while
video, deck and assembly together took under 25 s and ran alongside it. So the fix was the model, not the pipeline. I added a
"Writing speed" choice: **Fast** (Gemma 3 4B) builds the whole kit in about **18 s** (copy 14 s, video 13 s in parallel), **Best
quality** (Gemma 3 12B) in about 57 s, measured with the GPU otherwise idle. I also learned my own benchmarks slow the app: with an
evaluation running on the same GPU, the same job took 56 s and 102 s.

A second bug came from the phone: a photo scan that took over 30 s returned a bare "500". The Next.js proxy gives up after 30 s even
though the backend keeps working; the log showed the model call finishing afterwards. I raised the proxy timeout and replaced the
message with a plain-language one. In my phone recording the same five-photo scan completes and pre-fills the form.

## Sentry
Every model call is a `gen_ai.chat` span (model, token counts, tokens per second) under a `gen_ai.invoke_agent` span per job. Every
flagged claim is an issue tagged with the rule, the model and the prompt version, and a "The copy still made something up" button logs a
report against the job. The part I'm proudest of is a **canary test**: it pushes a unique marker through the facts and the model output
and fails if the marker shows up in any outgoing Sentry payload. An allow-list scrubber drops everything that isn't metadata.
[TODO: add 2-3 real screenshots (a trace, an issue list). Say what you found and fixed with them. If there is nothing yet, cut this
sentence rather than invent it.]

## Try it
<!-- Screenshots ready in docs/images/. The product film is kept outside the repo. -->
Code: https://github.com/advikdivekar/sellcraft (local setup is in the README: `ollama pull gemma3:4b`, start the backend and the frontend). A public demo link of the landing page and its in-browser studio: [TODO: add after deploying `render.yaml`] · Demo mode on the landing page assembles copy in the browser from
the facts you type and says so.

## What it can't do yet
No real-seller evaluation yet; synthetic data; the judge is n=30; Shopify publishing is tested against a mock only; no accounts; the
fine-tune needs a cloud call.

## Categories
Best Use of **Tinker** (LoRA fine-tune with a measured improvement over its base and over Gemma) · Best Use of **Gemma** (default
writer, photo reader and independent judge) · Best Use of **Sentry Agent Tracing** · Best Use of **Entire** (every decision in `docs/DECISIONS.md` links to its checkpoint; try `entire checkpoint explain 01M51MQH99N99QGA8RXNRSJTWF`).
