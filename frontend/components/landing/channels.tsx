"use client";
import { Heart, MessageCircle, Send } from "lucide-react";
import { useMemo, useState } from "react";
import { generate, PLATFORMS, platformBlurb, SAMPLE, type Kit, type Platform } from "./demo";
import { SampleProduct } from "./sample-product";

export function PlatformPreview({ platform, kit }: { platform: Platform; kit: Kit }) {
  const tags = kit.tags;
  if (platform === "instagram") return (
    <article className="mx-auto w-full max-w-[22rem] overflow-hidden rounded-2xl bg-white text-[var(--ink)] shadow-xl ring-1 ring-black/10">
      <header className="flex items-center gap-2 p-3"><span className="size-8 rounded-full bg-[var(--lime)]" aria-hidden /><span className="text-sm font-medium">yourshop</span></header>
      <SampleProduct id="ig" className="aspect-square w-full" />
      <div className="flex gap-3 p-3 text-[var(--ink)]"><Heart className="size-5" aria-hidden /><MessageCircle className="size-5" aria-hidden /><Send className="size-5" aria-hidden /></div>
      <p className="px-3 pb-4 text-[13.5px] leading-snug"><b>yourshop</b> {kit.caption} <span className="text-[#3a5a00]">{kit.hashtags.join(" ")}</span></p>
    </article>);
  if (platform === "facebook") return (
    <article className="mx-auto w-full max-w-[26rem] overflow-hidden rounded-xl bg-white text-[var(--ink)] shadow-xl ring-1 ring-black/10">
      <p className="p-3.5 text-[14px] leading-snug">{kit.caption}</p>
      <SampleProduct id="fb" className="aspect-[1.6/1] w-full" />
      <div className="flex items-center justify-between gap-3 bg-[#f0f2f5] p-3"><div><p className="text-[11px] uppercase tracking-wide text-black/50">yourshop.com</p><p className="text-sm font-semibold leading-tight">{kit.title}</p></div><span className="shrink-0 rounded-md bg-black/10 px-3 py-2 text-xs font-semibold">{kit.cta}</span></div>
    </article>);
  if (platform === "pinterest") return (
    <article className="mx-auto w-full max-w-[15rem] overflow-hidden rounded-3xl bg-white text-[var(--ink)] shadow-xl ring-1 ring-black/10">
      <SampleProduct id="pn" className="aspect-[2/3] w-full" />
      <div className="p-3.5"><p className="text-[15px] font-semibold leading-tight">{kit.title}</p><p className="mt-1 line-clamp-3 text-[12.5px] leading-snug text-black/60">{kit.description}</p><span className="mt-3 inline-block rounded-full bg-[#e60023] px-4 py-2 text-xs font-semibold text-white">Save</span></div>
    </article>);
  if (platform === "etsy") return (
    <article className="mx-auto w-full max-w-[26rem] overflow-hidden rounded-xl bg-white text-[var(--ink)] shadow-xl ring-1 ring-black/10">
      <SampleProduct id="et" className="aspect-[4/3] w-full" />
      <div className="space-y-2 p-4"><p className="text-[15px] font-medium leading-snug">{kit.title}</p><p className="text-sm text-black/55">Price not provided, so none is shown</p>
        <p className="text-[13px] leading-snug text-black/70">{kit.description}</p><div className="flex flex-wrap gap-1.5">{tags.slice(0, 13).map((t) => <span key={t} className="rounded-full bg-black/5 px-2.5 py-1 text-[11.5px]">{t}</span>)}</div></div>
    </article>);
  return (
    <article className="mx-auto w-full max-w-[28rem] overflow-hidden rounded-xl bg-white text-[var(--ink)] shadow-xl ring-1 ring-black/10">
      <div className="grid grid-cols-[38%_1fr]"><SampleProduct id="sh" className="aspect-[4/5] size-full" />
        <div className="space-y-2 p-4"><p className="text-[16px] font-semibold leading-tight">{kit.title}</p><p className="text-[12.5px] leading-snug text-black/65">{kit.description}</p>
          <span className="mt-1 block rounded-md bg-[var(--ink)] py-2.5 text-center text-xs font-semibold text-white">{kit.cta}</span><p className="text-[11px] text-black/45">SEO · {tags.slice(0, 4).join(", ")}</p></div></div>
    </article>);
}

export function Channels() {
  const [p, setP] = useState<Platform>("instagram");
  const kit = useMemo(() => generate(SAMPLE.name, SAMPLE.details, p, "luxury"), [p]);
  return (
    <section id="channels" className="relative scroll-mt-16 overflow-hidden py-[clamp(4rem,10vw,8rem)]" aria-labelledby="ch-h">
      <div className="wrap grid items-center gap-10 lg:grid-cols-[.9fr_1.1fr]">
        <div>
          <p className="label tick reveal">Every selling channel</p>
          <h2 id="ch-h" className="h2 reveal mt-3">Written the way <span className="serif">each channel</span> works.</h2>
          <p className="lede reveal mt-4 max-w-md muted">The same product becomes a reel caption, a keyword-rich Etsy title, a pin, a product page. Pick a channel and the preview rebuilds.</p>
          <div role="tablist" aria-label="Selling channel" className="reveal mt-7 flex flex-wrap gap-2">
            {PLATFORMS.map((x) => <button key={x.value} role="tab" aria-selected={p === x.value} onClick={() => setP(x.value)} className={`min-h-12 rounded-full px-5 text-[15px] transition ${p === x.value ? "bg-[var(--lime)] text-[var(--lime-ink)]" : "chip !min-h-12 hover:bg-white/5"}`}>{x.label}</button>)}
          </div>
          <p className="mt-5 text-sm muted" aria-live="polite">{platformBlurb(p)}</p>
        </div>
        <div className="relative rounded-[2rem] p-4 sm:p-8" style={{ background: "radial-gradient(70% 60% at 50% 40%, rgb(198 244 50 / .08), transparent 75%), var(--ink-2)", boxShadow: "inset 0 0 0 1px var(--line-d)" }}>
          <div key={p} className="anim-in min-h-[22rem] py-2" role="tabpanel"><PlatformPreview platform={p} kit={kit} /></div>
          <p className="label muted mt-4 text-center">Illustrated preview · sample copy</p>
        </div>
      </div>
    </section>
  );
}
