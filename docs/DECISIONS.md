# Decisions, and why the code is the way it is

Each decision names the commit that introduced it and an **Entire checkpoint**: the Claude Code session segment that was running
when that commit was made (`entire checkpoint explain <id>` shows its prompts, files and reasoning). Checkpoints for work before
Entire was enabled are *imported* from the local session history and matched to the commit by time, so treat the match as "the
conversation this came out of", not a one-to-one record.

| # | Decision | Why | Commit | Entire checkpoint |
|---|---|---|---|---|
| 1 | Copy is written by an open-weight model (Gemma) through Ollama, behind a provider interface | Seller facts stay on the seller's computer; no per-use cost; swap the model with one setting | `3f82ede` | `01M4ZZH4R676P58NF9DTCQX4C1` |
| 2 | Copy is split into 5-6 small JSON generations that run in parallel | One big generation took 90-145 s on a laptop; parts also let the UI show finished sections early | `1098445` | `01M50AHBGW63C190ETVBD418PE` |
| 3 | Risky claims are caught by a deterministic word check, not by a second model pass | A checker the model can't talk its way around, and free to run | `1098445` | `01M50AHBGW63C190ETVBD418PE` |
| 4 | Placeholders are stripped and flagged in place instead of re-running the model | A re-run costs a whole generation to fix one token | `722429a` | `01M505XK4PDWN2KARPWSWFN7QX` |
| 5 | The fine-tune is scored with deterministic checks and a held-out set the teacher script refuses to touch | No data leakage from test to train | `6445276` | `01M50QZNJTZNR6WSF9ZKK7CJEM` |
| 6 | A teacher model critiques and revises its own drafts using the checker's findings; only kits with zero hard violations become training data | Teaches the student to follow the rules, not just to imitate style | `6445276`, `1ac4d36` | `01M50QZNJTZNR6WSF9ZKK7CJEM`, `01M50STXRR8JVMAK7XC0Q67VQP` |
| 7 | Added an independent judge (Gemma, a different family from the Qwen teacher) | The checker is a fixed word list the fine-tune was trained against, so it can be gamed. A second opinion from another model family cannot be | `fc83433` | `01M50VNYW6ZNSWE40JZBHYGQHX` |
| 8 | Re-scored v1 honestly after tightening the checker (number words, urgency, occasions) | v1 looked like 93% clean under the old rules and was 65% under the new ones. Reporting only the old number would have been wrong | `fc83433` | `01M50VNYW6ZNSWE40JZBHYGQHX` |
| 9 | v2 trains only on kits the judge also passed (judge-in-the-loop) | v1 learned to pass the word list while still inventing statements the list could not see | `e0928f5` | `01M517Y8FYBZK4DR01HY6AG385` |
| 10 | Regulated-claims check for cosmetic and medical products | The planned first user sells skincare. "Reduces wrinkles" is a legal claim, not a style choice | `152ac45` | `01M50WPDAX0QNZ7MYG591G87BH` |
| 11 | Sentry gets metadata only (model, tokens, latency, which rule fired, flag counts), enforced by an allow-list scrubber | Product facts are the seller's data. A canary test fails if a marker reaches any outgoing Sentry payload | `138e85c`, `6964983` | `01M518BSETV4ND5F9186FYN9YT`, `01M51MQH99N99QGA8RXNRSJTWF` |
| 12 | Report button sends a section name and a fixed reason code, never text | Free text could carry product facts into telemetry | `6964983` | `01M51MQH99N99QGA8RXNRSJTWF` |
| 13 | ElevenLabs voiceover is out of this release | Scope call: effort goes to the fine-tune, tracing and a real user first. The settings stay in `.env.example` for later | `6964983` | `01M51MQH99N99QGA8RXNRSJTWF` |
| 14 | Rebrand to Mochi. The supplied logo is used on a dark teal tile, the wordmark is live text, the palette is Deep Ocean / Ocean Teal / Turquoise / Ice Blue with Burnt Terracotta used sparingly | One identity across landing page, app and icons; turquoise buttons carry dark text because white on #0FA4AF fails contrast | `4122ade` | `01M51TFVBHP577RBTCW5K3TWCB` |
| 15 | The sample product is an abstract ceramic sphere on a plinth, not an illustrated item | A literal illustrated product looked cartoonish and lowered trust. There are no stock photos in the repo, and the page labels the sample as an illustration | `4122ade` | `01M51TFVBHP577RBTCW5K3TWCB` |
| 16 | "Fast" (Gemma 3 4B) is the default writing speed, "Best quality" (Gemma 3 12B) is optional | Job stage timings showed copy took 52-105 s while video, deck and assembly together took under 25 s. Fast builds the whole kit in about 18 s | `4122ade` | `01M51TFVBHP577RBTCW5K3TWCB` |
| 17 | The web server proxy waits up to 5 minutes, and server errors say "took too long" instead of "(500)" | A photo scan over 30 s hit the proxy's default limit and showed a bare 500 on a phone | `4122ade` | `01M51TFVBHP577RBTCW5K3TWCB` |
| 18 | A public demo build (`NEXT_PUBLIC_DEMO_ONLY=1`, `render.yaml`) serves only the landing page and its in-browser studio | A link that does not depend on one laptop; the full app needs a local model | `4122ade` | `01M51TFVBHP577RBTCW5K3TWCB` |
| 19 | A layout check (`frontend/e2e/layout-overlap.mjs`) measures overlaps at 11 screen sizes and 7 scroll stages | A user screenshot showed a photo covering a card; one size is not enough to catch that | `4122ade` | `01M51TFVBHP577RBTCW5K3TWCB` |
