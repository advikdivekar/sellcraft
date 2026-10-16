# Decisions, and why the code is the way it is

Each decision names the commit that introduced it. The **Entire checkpoint** column is left blank on purpose: fill it in with
the checkpoint ID of the coding-agent session that produced the commit (`entire checkpoint explain <id>` shows the prompts and
reasoning), so a reader can go from a line of code to the conversation that caused it.

| # | Decision | Why | Commit | Entire checkpoint |
|---|---|---|---|---|
| 1 | Copy is written by an open-weight model (Gemma) through Ollama, behind a provider interface | Seller facts stay on the seller's computer; no per-use cost; swap the model with one setting | `3f82ede` | |
| 2 | Copy is split into 5-6 small JSON generations that run in parallel | One big generation took 90-145 s on a laptop; parts also let the UI show finished sections early | `1098445` | |
| 3 | Risky claims are caught by a deterministic word check, not by a second model pass | A checker the model can't talk its way around, and free to run | `1098445` | |
| 4 | Placeholders are stripped and flagged in place instead of re-running the model | A re-run costs a whole generation to fix one token | `722429a` | |
| 5 | The fine-tune is scored with deterministic checks and a held-out set the teacher script refuses to touch | No data leakage from test to train | `6445276` | |
| 6 | A teacher model critiques and revises its own drafts using the checker's findings; only kits with zero hard violations become training data | Teaches the student to follow the rules, not just to imitate style | `6445276`, `1ac4d36` | |
| 7 | Added an independent judge (Gemma, a different family from the Qwen teacher) | The checker is a fixed word list the fine-tune was trained against, so it can be gamed. A second opinion from another model family cannot be | `fc83433` | |
| 8 | Re-scored v1 honestly after tightening the checker (number words, urgency, occasions) | v1 looked like 93% clean under the old rules and was 65% under the new ones. Reporting only the old number would have been wrong | `fc83433` | |
| 9 | v2 trains only on kits the judge also passed (judge-in-the-loop) | v1 learned to pass the word list while still inventing statements the list could not see | `e0928f5` | |
| 10 | Regulated-claims check for cosmetic and medical products | The planned first user sells skincare. "Reduces wrinkles" is a legal claim, not a style choice | `152ac45` | |
| 11 | Sentry gets metadata only (model, tokens, latency, which rule fired, flag counts), enforced by an allow-list scrubber | Product facts are the seller's data. A canary test fails if a marker reaches any outgoing Sentry payload | `138e85c` and the commit after it | |
| 12 | Report button sends a section name and a fixed reason code, never text | Free text could carry product facts into telemetry | see 11 | |
| 13 | ElevenLabs voiceover is out of this release | Scope call: effort goes to the fine-tune, tracing and a real user first. The settings stay in `.env.example` for later | | |
