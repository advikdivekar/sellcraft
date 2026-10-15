import { ArrowRight, Check, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { StatusBadge } from "@/components/status-badge";
import { buttonClass } from "@/lib/styles";

const stack = ["Gemma", "Ollama", "FFmpeg", "OpenCV", "rembg"];

export default function Home() {
  return (
    <main className="relative mx-auto w-full max-w-6xl flex-1 overflow-x-clip px-4 pb-safe sm:px-6">
      <div className="bg-grid pointer-events-none absolute inset-x-0 top-0 -z-10 h-[620px]" aria-hidden />

      {/* Hero */}
      <section className="grid items-center gap-12 pb-12 pt-10 sm:pt-20 lg:grid-cols-[1.15fr_0.85fr] lg:gap-8">
        <div className="stagger space-y-7">
          <Link href="/create" className="group inline-flex items-center gap-2 rounded-full bg-surface py-1 pl-1 pr-3 text-[13px] shadow-card ring-1 ring-border transition hover:ring-border-strong">
            <span className="rounded-full bg-accent-soft px-2 py-0.5 text-xs font-semibold text-accent-text">Open source</span>
            <span className="text-muted"><span className="sm:hidden">Runs on your computer</span><span className="max-sm:hidden">Runs on your computer, not someone else&apos;s cloud</span></span>
            <ArrowRight className="size-3.5 text-muted transition group-hover:translate-x-0.5" aria-hidden />
          </Link>
          <h1 className="text-[2.6rem] font-semibold leading-[1.02] sm:text-6xl lg:text-7xl">
            One product photo.<br />A complete <span className="relative whitespace-nowrap text-accent-text">marketing kit<svg aria-hidden viewBox="0 0 300 12" className="absolute -bottom-1.5 left-0 h-2 w-full text-accent/60" preserveAspectRatio="none"><path d="M2 8 C 70 2, 160 2, 298 7" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" /></svg></span>.
          </h1>
          <p className="max-w-xl text-lg leading-relaxed text-muted">
            Studio-quality photos, an image deck, a 10-second video ad and platform-ready copy. Built from your own photos, in about a minute.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link href="/create" className={buttonClass("primary", "lg", "w-full sm:w-auto")}>Create your first kit <ArrowRight className="size-4" aria-hidden /></Link>
            <Link href="/connections" className={buttonClass("secondary", "lg", "w-full sm:w-auto")}>Connect your store</Link>
          </div>
          <StatusBadge />
        </div>

        {/* Phone mock: illustration only */}
        <div className="relative mx-auto w-full max-w-[320px]" aria-hidden>
          <div className="absolute -inset-10 -z-10 rounded-full bg-accent/15 blur-3xl" />
          <div className="rounded-[2.4rem] bg-primary p-[9px] shadow-float">
            <div className="overflow-hidden rounded-[1.9rem] bg-background">
              <div className="mx-auto mt-2 h-1.5 w-16 rounded-full bg-border-strong" />
              <div className="space-y-3 p-4">
                <div className="flex items-center justify-between"><div className="h-3 w-24 rounded-full bg-foreground/80" /><div className="h-6 w-16 rounded-full bg-accent-soft" /></div>
                <div className="relative aspect-[9/12] overflow-hidden rounded-xl bg-gradient-to-b from-[#0b0b0f] to-[#2c2936]">
                  <div className="absolute left-1/2 top-[38%] h-[44%] w-[34%] -translate-x-1/2 -translate-y-1/2 rounded-[45%] bg-gradient-to-b from-white/50 to-white/15 shadow-2xl" />
                  <div className="absolute bottom-0 inset-x-0 space-y-1.5 p-3"><div className="h-2.5 w-2/3 rounded-full bg-white/80" /><div className="h-2 w-1/3 rounded-full bg-white/40" /></div>
                  <span className="absolute left-3 top-3 rounded-full bg-white/15 px-2 py-0.5 font-mono text-[10px] text-white/80 backdrop-blur">0:10</span>
                </div>
                <div className="flex gap-2">
                  {["from-[#f4f1ea] to-[#d8d0c2]", "from-[#46291a] to-[#92583a]", "from-[#0b0b0f] to-[#2c2936]"].map((g, i) => <div key={i} className={`aspect-[4/5] flex-1 rounded-lg bg-gradient-to-b ${g} ring-1 ring-border`} />)}
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-border"><div className="h-full w-3/4 rounded-full bg-accent" /></div>
              </div>
            </div>
          </div>
          <span className="absolute -left-4 top-24 hidden rounded-full bg-surface px-3 py-1.5 text-xs font-medium shadow-float ring-1 ring-border sm:block" style={{ animation: "float-y 5s ease-in-out infinite" }}>Studio photos</span>
          <span className="absolute -right-3 bottom-32 hidden rounded-full bg-surface px-3 py-1.5 text-xs font-medium shadow-float ring-1 ring-border sm:block" style={{ animation: "float-y 6s ease-in-out 1s infinite" }}>Image deck</span>
        </div>
      </section>

      <section aria-label="Built on" className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 border-y border-border py-5 text-sm text-muted">
        <span className="eyebrow">Built on open source</span>
        {stack.map((s) => <span key={s} className="font-medium text-foreground/70">{s}</span>)}
      </section>

      {/* Bento */}
      <section aria-labelledby="gets" className="space-y-8 py-16">
        <div className="max-w-xl space-y-2"><p className="eyebrow">What you get</p><h2 id="gets" className="text-3xl font-semibold sm:text-4xl">Everything a listing needs, from one upload.</h2></div>
        <div className="grid gap-3 sm:grid-cols-6">
          <Bento className="sm:col-span-4" title="Photos that look professional" body="We retouch the product itself: noise out, resolution up, colour and light corrected, then place it on a studio backdrop that makes it stand out.">
            <div className="mt-5 flex items-end gap-3">
              <Tile label="Your photo" className="from-[#cfc7ba] to-[#a79d8c] blur-[1.5px] saturate-75" />
              <ArrowRight className="mb-10 size-5 shrink-0 text-muted" aria-hidden />
              <Tile label="Refined" className="from-[#0b0b0f] to-[#2c2936]" glow />
              <Tile label="Marketplace" className="from-white to-[#f1f1ef]" light />
            </div>
          </Bento>
          <Bento className="sm:col-span-2" title="A swipeable image deck" body="Hero, benefits, close-up and call to action slides.">
            <div className="relative mt-5 h-28">{["-rotate-6 left-2", "rotate-0 left-10 z-10", "rotate-6 left-[4.5rem]"].map((c, i) => <div key={i} className={`absolute top-0 aspect-[4/5] h-28 rounded-lg bg-gradient-to-b ${["from-[#0b0b0f] to-[#2c2936]", "from-[#f4f1ea] to-[#d8d0c2]", "from-[#46291a] to-[#92583a]"][i]} shadow-float ring-1 ring-black/5 ${c}`} />)}</div>
          </Bento>
          <Bento className="sm:col-span-2" title="A 10-second video ad" body="Vertical 9:16 with camera moves and text, made from your photos.">
            <div className="mt-5 flex h-2 overflow-hidden rounded-full" aria-hidden>{["bg-foreground/80 w-[20%]", "bg-foreground/50 w-[40%]", "bg-foreground/30 w-[20%]", "bg-accent w-[20%]"].map((c, i) => <div key={i} className={`${c} ${i ? "ml-0.5" : ""} rounded-full`} />)}</div>
            <div className="mt-2 flex justify-between font-mono text-[10px] text-muted"><span>Hook</span><span>Showcase</span><span>Feature</span><span>CTA</span></div>
          </Bento>
          <Bento className="sm:col-span-2" title="Copy that sticks to your facts" body="Missing details are flagged, never invented.">
            <div className="mt-5 flex flex-wrap gap-1.5"><Chip>Missing: price</Chip><Chip warn>Check: &ldquo;perfect&rdquo;</Chip><Chip ok>Facts only</Chip></div>
          </Bento>
          <Bento className="sm:col-span-2" title="Private by default" body="Models run on your computer. Nothing posts without your tap.">
            <ShieldCheck className="mt-5 size-8 text-accent-text" aria-hidden />
          </Bento>
        </div>
      </section>

      {/* How it works */}
      <section aria-labelledby="how" className="grid gap-10 border-t border-border py-16 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="space-y-2"><p className="eyebrow">How it works</p><h2 id="how" className="text-3xl font-semibold sm:text-4xl">Three steps. About a minute.</h2></div>
        <ol className="divide-y divide-border">
          {[["Add photos and a few facts", "Up to 5 photos. We read them and pre-fill the form; you only confirm."], ["Pick platform, tone and style", "Instagram, Facebook, Pinterest, Etsy or Shopify, each written the way it works."], ["Review, share or publish", "Edit anything, share from your phone, or send a draft to your store."]].map(([t, b], i) => (
            <li key={t} className="flex gap-5 py-5 first:pt-0"><span className="font-mono text-sm text-accent-text">0{i + 1}</span><div><h3 className="font-medium">{t}</h3><p className="mt-1 text-[15px] text-muted">{b}</p></div></li>
          ))}
        </ol>
      </section>

      {/* CTA */}
      <section className="mb-10 overflow-hidden rounded-2xl bg-primary px-6 py-12 text-center text-primary-fg sm:px-12 sm:py-16">
        <h2 className="mx-auto max-w-xl text-3xl font-semibold sm:text-4xl">Your next listing, finished before your coffee cools.</h2>
        <Link href="/create" className="mt-7 inline-flex min-h-13 items-center gap-2 rounded-[10px] bg-background px-6 text-base font-medium text-foreground transition hover:opacity-90 active:scale-[0.97]">Create a kit <ArrowRight className="size-4" aria-hidden /></Link>
      </section>
      <footer className="flex flex-wrap items-center justify-between gap-2 pb-10 text-[13px] text-muted"><span>SellCraft AI. Open models, your computer.</span><span className="inline-flex items-center gap-1.5"><Check className="size-3.5" aria-hidden />Nothing is posted unless you tap the button.</span></footer>
    </main>
  );
}

function Bento({ title, body, children, className = "" }: { title: string; body: string; children?: React.ReactNode; className?: string }) {
  return (
    <div className={`flex flex-col justify-between rounded-xl bg-surface p-5 shadow-card ring-1 ring-border sm:p-6 ${className}`}>
      <div><h3 className="font-semibold tracking-tight">{title}</h3><p className="mt-1.5 text-[14px] leading-relaxed text-muted">{body}</p></div>
      {children}
    </div>
  );
}
function Tile({ label, className, glow, light }: { label: string; className: string; glow?: boolean; light?: boolean }) {
  return (
    <div className="flex-1 text-center">
      <div className={`relative mx-auto aspect-[4/5] w-full max-w-[110px] overflow-hidden rounded-lg bg-gradient-to-b ${className} ring-1 ring-black/5`}>
        <div className={`absolute left-1/2 top-1/2 h-[46%] w-[38%] -translate-x-1/2 -translate-y-1/2 rounded-[45%] ${light ? "bg-gradient-to-b from-[#c9c2b6] to-[#8f8678]" : "bg-gradient-to-b from-white/55 to-white/15"} ${glow ? "shadow-[0_0_30px_rgba(255,255,255,0.25)]" : ""}`} />
      </div>
      <p className="mt-1.5 text-[11px] text-muted">{label}</p>
    </div>
  );
}
function Chip({ children, warn, ok }: { children: React.ReactNode; warn?: boolean; ok?: boolean }) {
  return <span className={`rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${warn ? "bg-warn/10 text-warn ring-warn/25" : ok ? "bg-ok/10 text-ok ring-ok/25" : "bg-surface-2 text-muted ring-border"}`}>{children}</span>;
}
