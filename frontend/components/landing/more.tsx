"use client";
import { ArrowRight, Pause, Play } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { APP, DEMO_ONLY } from "./config";
import { Logo } from "../logo";
import { generate, PLATFORMS, SAMPLE, TONES, type Tone } from "./demo";
import { useMedia, useReducedMotion, useScrollProgress, seg } from "./hooks";
import { CaptionPanel, ListingPanel, PinPanel, StoryboardPanel, TagsPanel } from "./parts";
import { SampleProduct } from "./sample-product";

/* ───────── Video-ad studio ───────── */
export function VideoShowcase() {
  const reduced = useReducedMotion();
  const [playing, setPlaying] = useState(true);
  const kit = useMemo(() => generate(SAMPLE.name, SAMPLE.details, "instagram", "luxury"), []);
  const run = playing && !reduced;
  const steps = ["The original product photo", "A camera move over the cleaned-up photo", "A short hook", "Your facts appear on screen", "End frame with a call to action"];
  const frames = [
    <div key="0" className="relative size-full"><SampleProduct id="v0" className="size-full" /><span className="label absolute left-3 top-14 rounded-full bg-black/60 px-2 py-1 text-[9px] text-white">Original photo</span></div>,
    <div key="1" className="relative size-full overflow-hidden"><div className="size-full origin-[50%_60%] scale-125"><SampleProduct id="v1" className="size-full" /></div><div className="absolute inset-0" style={{ background: "radial-gradient(60% 50% at 50% 50%, transparent, rgb(0 0 0 / .55))" }} /></div>,
    <div key="2" className="relative grid size-full place-items-center bg-[#0b0b0a] p-6 text-center"><p className="serif text-[2.4rem] leading-none text-[var(--turq)]">{kit.hook}</p></div>,
    <div key="3" className="relative size-full"><SampleProduct id="v3" className="size-full opacity-60" /><ul className="absolute inset-x-4 bottom-16 space-y-2">{kit.facts.slice(0, 3).map((f) => <li key={f} className="w-fit rounded-full bg-black/70 px-3 py-1.5 text-[13px] text-white backdrop-blur">{f}</li>)}</ul></div>,
    <div key="4" className="relative grid size-full place-items-center bg-[var(--turq)] p-6 text-center text-[var(--turq-ink)]"><div><p className="text-3xl font-medium tracking-tight">{SAMPLE.name}</p><p className="mt-4 inline-block rounded-full bg-[var(--ink)] px-5 py-2.5 text-sm text-[var(--paper)]">{kit.cta}</p></div></div>,
  ];
  return (
    <section className="relative py-[clamp(4rem,10vw,8rem)]" aria-labelledby="vid-h">
      <div className="wrap grid items-center gap-12 lg:grid-cols-[1fr_auto] lg:gap-20">
        <div className="order-2 lg:order-1">
          <p className="label tick reveal">Video-ad studio</p>
          <h2 id="vid-h" className="h2 reveal mt-3">Your next ad <span className="serif">starts with a photo.</span></h2>
          <p className="lede reveal mt-4 max-w-xl muted">A ten-second vertical ad, planned beat by beat from your facts. In the real app it&apos;s rendered into an MP4 from your own photos with real camera moves and text.</p>
          <ol className="reveal mt-8 space-y-0 divide-y divide-white/10 border-y border-white/10">
            {steps.map((s, i) => <li key={s} className="flex items-center gap-4 py-3.5"><span className="mono w-6 text-xs text-[var(--turq)]">0{i + 1}</span><span className="text-[15px]">{s}</span><span className="mono ml-auto text-xs muted">{i * 2}–{i * 2 + 2}s</span></li>)}
          </ol>
          <p className="mt-5 max-w-xl rounded-xl p-3.5 text-[13px] leading-relaxed muted" style={{ boxShadow: "inset 0 0 0 1px var(--line-d)" }}><b className="text-[var(--paper)]">This is an animated storyboard, not a rendered video.</b> The real kit exports an MP4 built from your photos with image processing and FFmpeg; it isn&apos;t AI-generated footage, and the app says so.</p>
          <Link href={APP} className="btn btn-turq mt-7 w-full sm:w-auto">Make a video ad <ArrowRight className="size-4" aria-hidden /></Link>
        </div>
        <div className="order-1 mx-auto lg:order-2">
          <div className="relative w-[min(78vw,19rem)] rounded-[2.6rem] bg-[#1a1a17] p-2.5 shadow-[0_50px_100px_-40px_#000] ring-1 ring-white/15">
            <div className={`relative aspect-[9/16] overflow-hidden rounded-[2.1rem] bg-black ${run ? "sb-run" : "sb-static"}`} style={{ ["--play" as string]: run ? "running" : "paused" }} role="img" aria-label="Animated storyboard of a ten second product ad">
              {frames.map((f, i) => <div key={i} className="sb-beat absolute inset-0" style={{ ["--i" as string]: i, opacity: reduced && i === 0 ? 1 : undefined }}>{f}</div>)}
              <div className="absolute inset-x-4 top-4 h-[3px] overflow-hidden rounded-full bg-white/25"><div className="sb-bar h-full w-full bg-white" /></div>
              <span className="label absolute right-3 top-8 rounded-full bg-black/60 px-2 py-1 text-[9px] text-white">Storyboard preview</span>
            </div>
            <button type="button" onClick={() => setPlaying((p) => !p)} aria-pressed={!playing} aria-label={playing ? "Pause storyboard" : "Play storyboard"} disabled={reduced}
              className="absolute -bottom-4 left-1/2 grid size-12 -translate-x-1/2 place-items-center rounded-full bg-[var(--turq)] text-[var(--turq-ink)] shadow-lg disabled:opacity-40">
              {playing && !reduced ? <Pause className="size-5" aria-hidden /> : <Play className="size-5" aria-hidden />}
            </button>
          </div>
          <div className="mt-10 flex flex-wrap justify-center gap-2" aria-label="Same concept, different channels">{PLATFORMS.map((p) => <span key={p.value} className="chip">{p.label}</span>)}</div>
        </div>
      </div>
    </section>
  );
}

/* ───────── One input, many outputs ───────── */
const DESK: [number, number][] = [[15, 17], [15, 50], [15, 83], [85, 17], [85, 50], [85, 83]];
const MOBI: [number, number][] = [[26, 46], [74, 46], [26, 65], [74, 65], [26, 84], [74, 84]];
export function OneToMany() {
  const reduced = useReducedMotion();
  const narrow = useMedia("(max-width: 767px)");
  const kit = useMemo(() => generate(SAMPLE.name, SAMPLE.details, "instagram", "luxury"), []);
  const pts = narrow ? MOBI : DESK;
  const box = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 1000, h: 480 });
  useEffect(() => {
    const el = box.current; if (!el) return;
    const ro = new ResizeObserver(([e]) => setSize({ w: Math.max(1, e.contentRect.width), h: Math.max(1, e.contentRect.height) }));
    ro.observe(el); return () => ro.disconnect();
  }, []);
  const c: [number, number] = narrow ? [50, 17] : [50, 50];
  const ref = useScrollProgress<HTMLElement>((p, el) => { el.style.setProperty("--q", seg(p, 0.05, 0.85).toFixed(3)); }, !reduced);
  const nodes = [<ListingPanel key="a" kit={kit} />, <TagsPanel key="b" kit={kit} max={4} />, <CaptionPanel key="c" kit={kit} />, <PinPanel key="d" kit={kit} />, <StoryboardPanel key="e" kit={kit} />,
    <div key="f" className="panel p-3.5 text-left"><p className="label muted">Brand-voice caption</p><p className="mt-1.5 text-[.9em] leading-snug">{generate(SAMPLE.name, SAMPLE.details, "facebook", "playful").caption}</p></div>];
  // Paths are drawn in real pixels (viewBox = container size) so dash-based "drawing" and stroke width stay undistorted.
  const px = (p: [number, number]) => [(p[0] / 100) * size.w, (p[1] / 100) * size.h] as const;
  const path = (to: [number, number]) => {
    const [cx, cy] = px(c), [tx, ty] = px(to);
    if (narrow) { const my = (cy + ty) / 2; return `M ${cx} ${cy + size.h * 0.09} C ${cx} ${my}, ${tx} ${my}, ${tx} ${ty - size.h * 0.06}`; }
    const sx = cx + (tx < cx ? -1 : 1) * size.w * 0.09, ex = tx + (tx < cx ? 1 : -1) * size.w * 0.135, mx = (sx + ex) / 2;
    return `M ${sx} ${cy} C ${mx} ${cy}, ${mx} ${ty}, ${ex} ${ty}`;
  };
  return (
    <section ref={ref} className={reduced ? "py-20" : "relative h-[250svh]"} style={{ ["--q" as string]: reduced ? 1 : 0 }} aria-label="One product photo becomes six deliverables">
      <div className={reduced ? "wrap" : "sticky top-0 flex h-[100svh] flex-col justify-center overflow-hidden"}>
        <div className="wrap w-full">
          <p className="label tick text-center">One input, many outputs</p>
          <h2 className="h2 mx-auto mt-3 max-w-3xl text-center">Upload once. <span className="serif">Get the lot.</span></h2>
          <div ref={box} className={`pp relative mx-auto mt-4 h-[min(74svh,38rem)] w-full max-w-5xl md:mt-6 md:h-[min(60svh,30rem)] ${narrow ? "compact" : ""}`} style={{ fontSize: "clamp(9px, 1.3cqw + 3px, 13px)" }}>
            <svg className="absolute inset-0 size-full" viewBox={`0 0 ${size.w} ${size.h}`} aria-hidden>
              {pts.map((to, i) => <path key={i} d={path(to)} pathLength={1} fill="none" stroke="var(--turq)" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="1" style={{ strokeDashoffset: `calc(1 - clamp(0, (var(--q) * 1.5 - ${i * 0.1}) * 2, 1))`, opacity: ".8" }} />)}
            </svg>
            <div className="absolute w-[22%] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-2xl shadow-[0_30px_60px_-24px_#000] ring-1 ring-white/20 md:w-[17%]" style={{ left: `${c[0]}%`, top: `${c[1]}%` }}>
              <SampleProduct id="o2m" className="aspect-[4/5] w-full" /></div>
            {pts.map((p, i) => <div key={i} className="absolute" style={{ left: `${p[0]}%`, top: `${p[1]}%`, width: narrow ? "44%" : "27%", opacity: `clamp(0, (var(--q) * 1.5 - ${i * 0.1} - .3) * 3, 1)`, transform: `translate(-50%, calc(-50% + (1 - clamp(0, (var(--q) * 1.5 - ${i * 0.1} - .3) * 3, 1)) * 14px))` }}>{nodes[i]}</div>)}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ───────── Brand voice ───────── */
const VOICES: Tone[] = ["minimal", "luxury", "playful", "emotional"];
export function BrandVoice() {
  const rows = useMemo(() => VOICES.map((t) => ({ t, kit: generate(SAMPLE.name, SAMPLE.details, "instagram", t) })), []);
  const before = SAMPLE.details.split("\n").join(". ") + ".";
  return (
    <section className="light py-[clamp(4rem,10vw,8rem)]" aria-labelledby="bv-h">
      <div className="wrap">
        <p className="label tick reveal">Brand voice</p>
        <h2 id="bv-h" className="h2 reveal mt-3 max-w-3xl">Same facts. <span className="serif">Your voice.</span></h2>
        <div className="reveal mt-8 rounded-2xl border border-black/15 bg-white p-4 sm:p-5"><p className="label muted">Before · the facts you typed</p><p className="mt-2 text-[15px] leading-relaxed">{SAMPLE.name}. {before}</p></div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {rows.map(({ t, kit }, i) => <article key={t} className="reveal flex flex-col rounded-2xl bg-[var(--ink)] p-5 text-[var(--paper)]" style={{ ["--d" as string]: `${i * 0.06}s` }}>
            <p className="label text-[var(--turq)]">{TONES.find((x) => x.value === t)?.label}</p><p className="mt-3 flex-1 text-[15px] leading-relaxed">{kit.description}</p></article>)}
        </div>
        <p className="mt-4 text-[13px] muted">Wording changes with the tone; the facts don&apos;t. Anything the copy asserts must come from what you provided, and the app flags what it can&apos;t verify.</p>
      </div>
    </section>
  );
}

/* ───────── How it works + CTA + footer ───────── */
export function HowItWorks() {
  const steps = [["Upload your product", "One to five photos and a few facts. The app reads the photo and pre-fills what it can; you confirm."], ["Choose your style and platform", "Instagram, Facebook, Pinterest, Etsy or Shopify, in the tone you want."], ["Generate your marketing package", "Copy, studio photos, an image deck and a 10-second video. Edit anything, then share or send a draft to your store."]];
  return (
    <section id="how" className="scroll-mt-16 py-[clamp(4rem,10vw,8rem)]" aria-labelledby="how-h">
      <div className="wrap grid gap-10 lg:grid-cols-[.8fr_1.2fr]">
        <div><p className="label tick reveal">How it works</p><h2 id="how-h" className="h2 reveal mt-3">Three steps. <span className="serif">About a minute.</span></h2></div>
        <ol className="divide-y divide-white/10 border-y border-white/10">
          {steps.map(([t, b], i) => <li key={t} className="reveal flex gap-5 py-6 sm:gap-8" style={{ ["--d" as string]: `${i * 0.08}s` }}><span className="grid size-11 shrink-0 place-items-center rounded-full bg-[#964734] text-lg font-medium text-white sm:size-14 sm:text-xl">{i + 1}</span><div><h3 className="text-xl font-medium tracking-tight sm:text-2xl">{t}</h3><p className="mt-1.5 max-w-lg muted">{b}</p></div></li>)}
        </ol>
      </div>
    </section>
  );
}

export function FinalCTA() {
  return (
    <section className="grain relative overflow-hidden py-[clamp(5rem,14vw,10rem)] text-white" aria-labelledby="cta-h"
      style={{ background: "radial-gradient(60% 80% at 85% 110%, rgb(150 71 52 / .55), transparent 70%), linear-gradient(135deg, #003135 0%, #024950 48%, #0FA4AF 120%)" }}>
      <div className="wrap relative text-center">
        <h2 id="cta-h" className="display mx-auto max-w-4xl !text-[clamp(2.4rem,8vw,6.5rem)]">Your product deserves <span className="serif">better marketing.</span></h2>
        <p className="lede mx-auto mt-6 max-w-xl text-white/80">Create better listings, stronger product stories, and campaign-ready content from the photos you already have.</p>
        <Link href={APP} className="btn mt-9 w-full bg-white text-[#003135] hover:shadow-[0_0_0_6px_rgb(255_255_255/.18)] sm:w-auto">Start creating <ArrowRight className="size-4" aria-hidden /></Link>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="py-10" style={{ paddingBottom: "max(2.5rem, env(safe-area-inset-bottom))" }}>
      <div className="wrap flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div><Logo size={34} /><p className="mt-1 text-sm muted">Your product. Your story. Ready to sell.</p></div>
        <nav aria-label="Footer" className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
          {(DEMO_ONLY ? [] : [["Create", "/create"], ["Connect a store", "/connections"]]).map(([l, h]) => <Link key={l} href={h} className="inline-flex min-h-11 items-center muted hover:text-[var(--paper)]">{l}</Link>)}
          {[["Product", "#studio"], ["How it works", "#how"]].map(([l, h]) => <a key={l} href={h} className="inline-flex min-h-11 items-center muted hover:text-[var(--paper)]">{l}</a>)}
        </nav>
      </div>
    </footer>
  );
}
