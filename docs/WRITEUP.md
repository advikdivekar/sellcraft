<!--
BEFORE YOU PUBLISH (this comment does not show on DEV)

Title idea: "I watched my mom lose 4 hours to one Instagram post. So I built Mochi."
Tags (max 4): devchallenge, hf26challenge, opensource, ai

1. Search this file for "TODO" and fix every one. They are in bold so you can't miss them.
2. Push the images first, or none of them will show on DEV:
   docs/images/diagrams/*.png and docs/images/velora/*.png
3. Upload the video to YouTube (unlisted works). DEV embeds it with:  {% embed https://youtu.be/YOUR_ID %}
4. Set a cover image (docs/images/landing-hero-desktop.png works).
-->

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

## What I Built

**One product photo. About a minute. A full marketing kit.**

That's Mochi. You give it a photo and a few true facts. It gives you studio photos, an image deck, a 10-second vertical video, and copy for each platform you sell on. Every piece is built on your own computer, with open models.

Here is why I built it.

### I used to run an ecommerce brand

In small ecommerce, performance marketing is everything. If your ad is not live, you are not selling.

And making one ad was a slog. For every single product I had to:

- Get listing copy from two or three different AI chats, then stitch it together by hand
- Write the ad copy
- Edit the photos
- Generate the images for the listing
- Make video ads

Every step lived in a different tool. Every handoff was a copy and paste.

It cost me in three ways:

- **Time.** The slow part was never the idea. It was the gap between "I have a product" and "it's live". Every day in that gap was a lost sale.
- **Cashflow.** A subscription for images, one for video, one for copy, one for editing. In a small business, cashflow is tight, and tool bills quietly eat it.
- **Privacy.** My product details, my pricing and my workflow all sat inside other people's tools. None of it was ever private.

### Then I watched my mom do the same thing

My mom is a cosmetician. She sells skincare and beauty products.

To post one Instagram reel or one Facebook post, she goes through **3 to 4 different apps**:

1. Canva for the image
2. CapCut, or another editor, for the video
3. ChatGPT or Claude for the caption, then back and forth, copy, paste, "make it shorter", copy, paste again
4. Then the post itself, on each platform

**One single image post took her 3 to 4 hours.**

Those are hours she could have spent with customers. Instead she was learning video editors and rewriting captions. She is good at selling. The tools were making her a part-time designer.

That is the problem. It isn't "AI can't make content". It's that the work is split across too many tools, costs too much attention, and sends your product details to places you don't control.

### The fix: one flow, on your own machine

Mochi turns that whole chain into three taps.

<!-- DEV ignores relative paths, so use the raw GitHub URL once the images are pushed -->
![Mochi landing page](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/landing-hero-desktop.png)

You get:

- **Studio photos.** Your phone photo, cut out and placed on a designed backdrop, with the product itself never repainted
- **An image deck.** Slides ready for a feed or a catalog
- **A 10-second vertical video.** Camera moves and text cards built from your own copy
- **Platform copy.** Listing, social, Pinterest and a video brief, written for each place you sell

One thing I care about more than anything: **Mochi does not make things up.** If you didn't tell it your product is waterproof, the copy won't say so. Missing facts are listed back to you ("Not provided, so left out of the copy"). Risky claims get flagged before you post.

For a skincare seller, that matters. "Reduces wrinkles" is a legal claim, not a style choice.

### How to use it

It is three steps, and the draft saves itself as you go.

1. **Photos.** Add up to 5 photos. The first one is the main one.
2. **Facts.** Mochi reads your photos and pre-fills the form: product name, a short summary, and any text it can read on the label. Each of those is tagged **"From photo, check it"**, so you stay in charge. Blank fields are flagged as missing. They are never guessed.
3. **Style.** Pick where you sell (Instagram, Facebook, Pinterest, Etsy, Shopify), a tone, a goal, a backdrop, and a writing speed.

Then tap **Generate kit**. You can leave the page while it works. When it's done you get four tabs: **Overview, Copy, Photos, Share**.

Nothing posts on its own. The only thing Mochi can send anywhere is a Shopify **draft**, and only when you tap it.

## Demo

**Video:** **[TODO: paste the YouTube link here as `{% embed https://youtu.be/YOUR_ID %}`]**

**Try the demo studio:** [mochi-demo.onrender.com](https://mochi-demo.onrender.com)

I'll be honest about what that link is. It's the landing page plus a studio that runs entirely **in your browser**. It's labelled as a demo. It does **not** run the real models, because they need a computer with a GPU, and I won't pretend otherwise. The full app is the code below, running on your own machine. The first user session further down is the real thing.

## Code

{% embed https://github.com/advikdivekar/sellcraft %}

Backend: FastAPI, SQLite, Pydantic. Frontend: Next.js 16 and React 19. 135 backend tests pass. Every number in this post can be reproduced from the files in `backend/finetune/results/`, with the commands in [`docs/RESULTS.md`](https://github.com/advikdivekar/sellcraft/blob/main/docs/RESULTS.md).

## How I Built It

### The big picture

A request makes two lanes run **at the same time**: one for visuals and one for language. They meet at the deck and the video, which need the finished copy.

![System architecture](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/diagrams/system.png)

The page polls the job every 1.5 seconds and shows real progress and partial copy as it arrives. Nothing is faked.

### Which model does which job

Every model has **one job and one strict contract**.

| Model or tool | Job |
|---|---|
| **Gemma 3 4B** (Ollama) | Fast copy (the default), reading photos |
| **Gemma 3 12B** (Ollama) | Best-quality copy, and the independent judge in my evaluation |
| **rembg** (U2-Net) | Cuts the product out of its background |
| **OpenCV, NumPy, Pillow** | Measure, denoise, 2x upscale, fix tone, build the deck. Deterministic. |
| **FFmpeg** | The video. Camera moves, crossfades, text cards. **Not** generative video. |
| **Qwen3.5-4B + LoRA** (Tinker) | My fine-tuned copy writer |
| **A plain-code checker** | Scores and flags the copy |

Two choices worth explaining.

**The video is not AI-generated.** It's image processing plus FFmpeg. That means the product in the video is *your* product, pixel for pixel. Generative video tends to repaint the product, and a seller can't sell a product that looks different from the real one.

**The checker is plain code, not a second model.** A model can talk itself into anything. A word list and a number check can't.

### Photos to studio shots

![Studio imagery pipeline](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/diagrams/studio.png)

Measure the photo, cut out the product, clean the product's pixels, fix the tone, choose a backdrop that suits what the photo shows, then compose. If the cutout looks wrong (too little or too much of the frame), it falls back to a framed photo instead of a bad cutout.

### The copy pipeline

![Copy pipeline](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/diagrams/copy.png)

The kit is split into small parts that run in parallel: four core parts plus one per platform. Each part's output is forced into a JSON schema. A bad call is retried once, and only the missing parts are redone. Then plain code checks for forbidden words, invented numbers and unsupported claims, and anything it finds is shown to the seller.

### Why it's fast

![Where the time goes](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/diagrams/optimisations.png)

My first version was far too slow. One big generation on a laptop took 90 to 145 seconds. Three changes fixed most of it:

| Change | Before | After |
|---|---|---|
| Fast mode (Gemma 4B) as the default | copy 53 s | copy 14 s |
| Split the kit into parallel parts | one 12B call, 90 to 145 s | 45 to 60 s |
| Run the visual and language lanes together | the sum of both | the slower lane, plus a few seconds |

A four-photo kit went from about **100 s to about 18 s** in Fast mode. Best quality (Gemma 12B) takes about 57 s.

The trade-off is real. The 4B model gets more claims flagged than the 12B. The post-check still catches them, and Best quality is one switch away.

### Training a small model to follow the rules

This is the part I'm proudest of, and the part where I got it wrong first.

![Fine-tuning pipeline](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/diagrams/finetune.png)

The idea: a big teacher model writes marketing kits, code and an independent judge reject any kit that breaks the rules, and only the **clean** kits are used to train a small student. The full story and numbers are in the Tinker section below.

### Privacy by design

![What stays local and what can leave](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/diagrams/trust.png)

Your product facts stay on your computer. The only things that can ever leave are a Shopify draft you tap, and scrubbed Sentry metadata. Both are covered in the sections below.

## Why Does Open Innovation Matter?

Go back to my two stories. In both, the real cost was not money alone. It was **control**.

**1. Your product details are your business.**
Pricing, ingredients, launch plans, the way you describe your product. With open models running locally, all of it stays on your machine. There is no "we don't train on your data" to trust. The data never leaves.

**2. A fixed price of zero, per kit.**
On your own computer, every kit costs electricity. A seller can run it five times on one product, try three tones, and never wonder if it is "worth" the credits. In a business where cashflow is tight, that matters.

**3. I could change the model, not just the prompt.**
The most important thing I did in this project was fine-tune a small open model so it follows one rule better: *don't invent claims*. Prompting alone left the 4B model at 23% clean kits. Training took it to 88%. You can't do that to a closed model, and you can't download what you trained.

**4. I could look inside and measure.**
I saw that my first fine-tune had learned to pass my word list while still embellishing. I only found that out because I could test it against a second model. With a closed API I'd have had one number and no way to question it.

**5. One setting swaps the model.**
Fast or Best quality is a single setting, and both are open Gemma models. The next Gemma release is a one-line change.

The honest limit: open models on your own computer need a computer that can run them. That is why the public demo is a browser demo, and why I wrote the local setup into the README.

## My Agent Session

I built Mochi with Claude Code, and every session is recorded with **Entire**. Each commit carries the checkpoint of the conversation that produced it.

- [`docs/DECISIONS.md`](https://github.com/advikdivekar/sellcraft/blob/main/docs/DECISIONS.md) lists **19 decisions**, each with its reason, its commit and its Entire checkpoint ID
- About **113 checkpoints** are pushed to the repo
- To read one: `entire checkpoint explain <id>` in a clone of the repo

Two of the decisions the record shows, in my own words:

- **#8: re-scoring my own fine-tune.** I tightened the checker and my "93% clean" model became 65%. I recorded that instead of hiding it.
- **#16: making Fast the default.** Stage timings showed copy was the slowest part, so the default became the smaller model.

One caveat on honesty: checkpoints for work from before Entire was switched on were *imported* from my local history and matched to commits by time. Read those as "the conversation this came out of", not a one-to-one record. The decisions file says the same.

## My First User

**Velora**, a skincare brand, ran its **Sensicontrol Face Cleanser** through Mochi on a phone, on **16 October 2026**. I have the screen recording. Here is what happened, taken only from what is on screen.

**[TODO: say who at Velora used it, in one line. Then add one real quote from them, word for word, or delete this line. Also say plainly whether they would pay or paid. If not, write "not yet" or leave it out.]**

**1. They added three photos of the bottle.** Mochi started reading them straight away.

![Three product photos added](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/velora/velora-01-photos.png)

**2. Mochi read the label.** It pulled the ingredient list and the usage steps off the bottle, and offered them as notes to add. Nobody typed them.

![Text read from the product label](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/velora/velora-02-label-read.png)

**3. They chose how to sell it.** A persuasive tone, the goal "Drive sales", **Best quality** writing, Pinterest as the platform, and the warm and cozy backdrop.

![Choosing tone, goal and writing speed](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/velora/velora-03-style.png)
![Choosing a backdrop](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/velora/velora-03b-backdrop.png)

**4. The kit built itself.** Progress was real, step by step: writing copy, building the studio photos and video, adding text to the video.

![Building the kit](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/velora/velora-04-building.png)

**5. It was ready in 55 seconds.** On Best quality, with three photos, running on a Gemma 3 12B model on my own computer.

![Kit ready, built in 55 seconds](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/velora/velora-05-ready-55s.png)

**6. And here is the part I care about most.** Mochi told them what it *wouldn't* make up:

- **"Not provided, so left out of the copy":** dimensions, verified benefits, target audience, care instructions
- **"Double-check before posting":** *Not in your facts: "available now". Remove it unless it's true.*
- **"About your photos":** it skipped the close-up slide because the photo didn't have enough pixels on the product

![Mochi lists what it left out and what to double-check](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/velora/velora-06-double-check.png)

**7. The video ad, with Velora's own bottle in it.**

![The 10-second video ad](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/velora/velora-07-video-ad.png)

**8. The copy, studio photos and deck.**

![Keywords, tags and SEO title](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/velora/velora-08-copy.png)
![Studio photos](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/velora/velora-09-studio-photos.png)

The kit was five slides, nine studio photos, a 10-second video, and copy for one platform.

**What I learned from watching:** **[TODO: write 2 or 3 honest lines about what you saw when they used it. Something confusing, something slow, something they liked. Only what really happened.]**

## Prize Categories

I'm entering **Tinker, Gemma, Sentry Agent Tracing and Entire**, and I'm mentioning Render for the demo. Each section covers what I used, why, what it was meant to fix, and what I found.

### Best Use of Tinker

**What I used it for.** I fine-tuned **Qwen3.5-4B with a LoRA adapter** on Tinker to write marketing copy that follows one rule: *never invent a claim the seller didn't give.*

**Why Tinker.** Prompting a small model to follow that rule didn't work. Untuned Qwen3.5-4B produced a clean kit only 18% of the time. I wanted to change the model, not keep rewording the prompt, and Tinker let me train without running my own GPU servers.

**How it worked.**

1. A big teacher model, **Qwen3.5-397B-A17B**, writes and revises kits on Tinker
2. My checker and an independent judge reject any kit with an invented claim, number or forbidden word
3. The teacher revises with the checker's findings, at most 2 rounds
4. Only kits with **zero** hard violations become training data
5. A small student is trained on those: rank 32, 3 epochs, 319 examples, learning rate 2e-4
6. A held-out set of 60 products, which the training code refuses to read, tests it

The whole thing cost **$5.41 of the $10 credit**.

**Results** (60 held-out synthetic products, one checker):

![Evaluation results](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/diagrams/evaluation.png)

| Model | Clean kits | 95% CI |
|---|---|---|
| Qwen3.5-4B, untuned | 18% | 10 to 28% |
| Gemma 3 4B | 23% | 13 to 35% |
| Gemma 3 12B | 45% | 33 to 57% |
| Fine-tune v1 | 65% | 53 to 77% |
| **Fine-tune v2** | **88%** | **78 to 95%** |

That's a 4B model, a third of Gemma 12B's size, producing nearly twice as many clean kits, and about 10 times faster (4.9 s against 48.7 s per kit, though v2 runs on Tinker's cloud and Gemma on my laptop).

**What I got wrong first, and what it taught me.** v1 scored **93%** clean under my first checker. Then I tightened it to catch number words, urgency and occasions, and the same outputs scored **65%**. v1 had learned to pass my word list.

So I added a second opinion: an independent judge from a different model family (Gemma 12B) that lists every statement the facts don't support. On that judge, **v1 was worse than the untuned model** (0.63 flags per kit against 0.43). Same trap, confirmed by a second measure.

v2 fixes that by training only on kits that passed **both** the checker and the judge.

**The honest result on the judge.** v2 halves the untuned model's flags (0.43 to 0.20), but the confidence intervals overlap, and Gemma 12B is lower still at 0.13. With 30 kits per model I can't claim more than that.

**Limits I'm stating on purpose:**
- The test set is synthetic, and the checker also filtered the training data
- The fine-tune runs on Tinker, so its inputs leave the machine. The app's default (Gemma via Ollama) stays local.
- The fine-tune is **not** in the app's path yet. I haven't exported it to GGUF for Ollama.
- Hosted cost is about $3 per 1,000 kits, estimated from token counts

**What I learned.** A fine-tune can look great while learning the wrong lesson. The only reason I caught it is that I measured it twice, with two different judges, and wrote both down.

### Best Use of Gemma

**What I used it for.** Gemma does three jobs inside Mochi, all through Ollama on the seller's own computer:

1. **The copy writer.** Gemma 3 4B for Fast, Gemma 3 12B for Best quality
2. **The photo reader.** It reads up to 5 photos and returns suggested facts, each tagged "From photo, check it"
3. **The independent judge.** Gemma 3 12B, a different family from the Qwen teacher, reviews kits in my evaluation

**Why Gemma.** It's open-weight, it runs on one machine, and it can be held to a JSON schema. That matters here: the seller's facts shouldn't leave their computer, and every part of a kit must come back as strict, checkable JSON.

**What it was meant to fix.** The cost and privacy problems from my ecommerce days: no per-kit fee, and nothing sent to anyone else's server.

**Results.**

- Both sizes run the same prompt and the same checker, so I could compare them fairly: **23% clean kits on 4B and 45% on 12B**
- Speed is the trade-off. Fast (4B) builds a four-photo kit in about **18 s**, Best quality (12B) in about **57 s**
- As the judge, Gemma 12B had the fewest flags of any model I tested (0.13 per kit)

**What I learned.** Two things. First, the model size is a user choice, not a technical one, so I made it a switch on the form. Second, the judge is Gemma, so it may be lenient toward Gemma's own writing. That bias favours the Gemma rows and works *against* my fine-tune's claim, so it can't be inflating my result.

### Best Use of Sentry Agent Tracing

**What I used it for.** Tracing every model call and every job, without Sentry ever seeing a seller's product facts.

**Why this was the hard part.** A marketing tool handles a seller's most private material: product details, prices, plans. Sending prompts to a tracing service would break the promise the whole product makes. So the question was not "can I trace this", it was "can I trace this and prove nothing private leaks".

**What Sentry sees.**

![What Sentry sees, and what it never sees](https://raw.githubusercontent.com/advikdivekar/sellcraft/main/docs/images/diagrams/observability.png)

- Each model call is a **`gen_ai.chat` span**, with the model, token counts and latency
- Each generation job is a transaction
- Each flagged claim is an issue (which rule fired, and how many)
- Each seller report is an event. The report button sends a section name and a fixed reason code, **never free text**

**What it never sees.** An allow-list scrubber removes everything that is not on the list of allowed metadata. Product facts, copy, photos and prompts can't pass it.

**How I know it works.** A canary test pushes a unique fake product through every input path of the real app, then fails if that marker shows up in *any* outgoing Sentry payload. It's in `tests/test_tracing.py`.

**Results and honesty.** The scrubber and the canary test are in place and pass. I am **not** claiming Sentry has caught a real production incident, because it hasn't. Mochi has had one real user session, not production traffic.

**What I learned.** Making tracing safe was a bigger design question than turning it on. The allow-list approach (what's permitted, not what's blocked) is the one that survives new fields being added later.

### Best Use of Entire

**What I used it for.** To record how Mochi was built, so a reader can see *why* the code is the way it is, not just what it does.

**Why.** Most repos show a result. For a project where I changed my mind several times, the changes are the story. A re-scored fine-tune, a cut feature and a new default each have a reason that a commit message can't hold.

**What came of it.**

- **About 113 checkpoints** of Claude Code sessions, pushed to the repo
- [`docs/DECISIONS.md`](https://github.com/advikdivekar/sellcraft/blob/main/docs/DECISIONS.md): **19 numbered decisions**, each with the reason, the commit and the Entire checkpoint ID
- Anyone can run `entire checkpoint explain <id>` in a clone and read the prompts, files and reasoning behind a decision

**The most useful example.** Decision #8 records the day my fine-tune went from 93% to 65% under a stricter checker. That is the kind of moment that normally disappears. Here it is written down, with the conversation that led to it.

**Honest limit.** Checkpoints from before Entire was enabled were imported from local history and matched by time. They show the conversation a commit came out of, not a one-to-one record.

### Render (mentioned, with limits)

The public demo at [mochi-demo.onrender.com](https://mochi-demo.onrender.com) is deployed on Render from a `render.yaml` Blueprint, on the free plan.

That's a static front end plus an in-browser demo, with **no model running on Render**. I'm not claiming Render as an AI runtime. It's there so anyone can try the interface without installing anything. The real product runs on your own machine.

---

**What's next:** exporting the fine-tune to GGUF so it can run in Ollama with everything else, a real-seller evaluation instead of a synthetic one, and more first-user sessions.

If you sell something and make your own content, I'd love to hear what's missing. Tell me in the comments.

*Built solo, with Claude Code.*
