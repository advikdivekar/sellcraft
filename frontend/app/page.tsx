import { ArrowRight, Camera, Film, GalleryHorizontal, Layers, ShieldCheck, Share2, Wand2 } from "lucide-react";
import Link from "next/link";
import { StatusBadge } from "@/components/status-badge";

const steps = [
  { n: 1, icon: Camera, title: "Add photos and a few facts", body: "Up to 5 photos. We read them and pre-fill the form; you only confirm." },
  { n: 2, icon: Wand2, title: "Pick platform, tone and style", body: "Instagram, Facebook, Pinterest, Etsy or Shopify, written the way each one works." },
  { n: 3, icon: Share2, title: "Review, share or publish", body: "Edit anything, then share from your phone or send a draft to your store." },
];
const gets = [
  { icon: Layers, title: "Refined product photos", body: "Background removed, noise reduced, upscaled, lit and placed on a studio backdrop." },
  { icon: GalleryHorizontal, title: "Image deck", body: "Hero, benefits, close-up and call-to-action slides, ready for a carousel." },
  { icon: Film, title: "10-second video ad", body: "Vertical 9:16 with camera moves and text, made from your own photos." },
  { icon: ShieldCheck, title: "Copy that sticks to your facts", body: "Missing details are flagged, never invented. Risky claims are called out." },
];

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-safe sm:px-6">
      <section className="grid items-center gap-10 py-10 sm:py-16 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="anim-in space-y-6">
          <StatusBadge />
          <h1 className="text-4xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
            One product photo.<br />A few facts.<br /><span className="text-accent">A complete marketing kit.</span>
          </h1>
          <p className="max-w-lg text-lg text-muted">
            Studio-quality photos, an image deck, a 10-second video ad and platform-ready copy, built from your own photos on open models that run on your computer.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/create" className="inline-flex min-h-13 items-center gap-2 rounded-xl bg-accent px-6 text-base font-medium text-accent-fg shadow-card transition hover:brightness-110 active:scale-[0.98]">
              Create a marketing kit <ArrowRight className="size-4" aria-hidden />
            </Link>
            <Link href="/connections" className="inline-flex min-h-13 items-center rounded-xl border border-border-strong bg-surface px-5 text-base font-medium shadow-card transition hover:bg-surface-2">
              Connect your store
            </Link>
          </div>
        </div>

        <div className="relative mx-auto hidden h-[420px] w-full max-w-md sm:block" aria-hidden>
          {[
            { cls: "left-0 top-10 -rotate-6", bg: "from-[#0b0b0f] to-[#2a2733]", label: "Hero", fg: "text-white" },
            { cls: "left-[28%] top-0 rotate-2", bg: "from-[#f3efe8] to-[#d9d1c4]", label: "Benefits", fg: "text-[#1b1815]" },
            { cls: "right-0 top-16 rotate-6", bg: "from-[#46291a] to-[#92583a]", label: "Close-up", fg: "text-white" },
          ].map((c) => (
            <div key={c.label} className={`absolute aspect-[4/5] w-[46%] rounded-3xl bg-gradient-to-b ${c.bg} p-4 shadow-float ring-1 ring-black/5 ${c.cls}`}>
              <div className="mx-auto mt-6 h-[46%] w-[46%] rounded-[40%] bg-white/25 blur-[1px]" />
              <div className="mt-5 space-y-2"><div className="h-2.5 w-3/4 rounded-full bg-current opacity-30" /><div className="h-2.5 w-1/2 rounded-full bg-current opacity-20" /></div>
              <span className={`absolute bottom-3 left-4 text-xs font-medium opacity-70 ${c.fg}`}>{c.label}</span>
              <span className={`absolute inset-0 rounded-3xl ${c.fg}`} />
            </div>
          ))}
        </div>
      </section>

      <section aria-labelledby="how" className="space-y-5 py-8">
        <h2 id="how" className="text-2xl font-semibold tracking-tight">How it works</h2>
        <ol className="grid gap-3 sm:grid-cols-3">
          {steps.map(({ n, icon: Icon, title, body }) => (
            <li key={n} className="rounded-2xl border border-border bg-surface p-5 shadow-card">
              <div className="mb-3 flex items-center gap-3"><span className="grid size-8 place-items-center rounded-full bg-accent-soft text-sm font-semibold text-accent">{n}</span><Icon className="size-5 text-muted" aria-hidden /></div>
              <h3 className="font-medium">{title}</h3><p className="mt-1 text-sm text-muted">{body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="gets" className="space-y-5 py-8">
        <h2 id="gets" className="text-2xl font-semibold tracking-tight">What you get</h2>
        <ul className="grid gap-3 sm:grid-cols-2">
          {gets.map(({ icon: Icon, title, body }) => (
            <li key={title} className="flex gap-4 rounded-2xl border border-border bg-surface p-5 shadow-card">
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-accent-soft text-accent"><Icon className="size-5" aria-hidden /></span>
              <div><h3 className="font-medium">{title}</h3><p className="mt-1 text-sm text-muted">{body}</p></div>
            </li>
          ))}
        </ul>
      </section>

      <footer className="border-t border-border py-8 text-sm text-muted">
        Runs on open-weight models (Gemma through Ollama) on your own computer. Nothing is posted anywhere unless you tap the button.
      </footer>
    </main>
  );
}
