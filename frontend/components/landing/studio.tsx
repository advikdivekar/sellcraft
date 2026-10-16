"use client";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, ImagePlus, Sparkles, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";
import { DEMO_ONLY } from "./config";
import { generate, PLATFORMS, SAMPLE, TONES, type Platform, type Tone } from "./demo";
import { useCopy } from "./hooks";
import { CopyButton } from "./parts";
import { SampleProduct } from "./sample-product";

const TABS = ["Title", "Description", "Tags", "Caption", "Video"] as const;
type Tab = (typeof TABS)[number];
const MAX_MB = 10;

export function Studio() {
  const uid = useId();
  const [name, setName] = useState(SAMPLE.name);
  const [details, setDetails] = useState(SAMPLE.details);
  const [submitted, setSubmitted] = useState({ name: SAMPLE.name, details: SAMPLE.details });
  const [platform, setPlatform] = useState<Platform>("instagram");
  const [tone, setTone] = useState<Tone>("luxury");
  const [tab, setTab] = useState<Tab>("Title");
  const [photo, setPhoto] = useState<{ url: string; name: string } | null>(null);
  const [error, setError] = useState("");
  const [drag, setDrag] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [flash, setFlash] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);
  const { done, copy } = useCopy();
  const kit = useMemo(() => generate(submitted.name, submitted.details, platform, tone), [submitted, platform, tone]);
  const status = useQuery({ queryKey: ["status"], queryFn: api.status, retry: 0, refetchInterval: 20000, enabled: !DEMO_ONLY });

  useEffect(() => () => { if (photo) URL.revokeObjectURL(photo.url); }, [photo]);
  function take(f?: File | null) {
    if (!f) return;
    if (!f.type.startsWith("image/")) return setError("That file isn't an image. Use a JPG, PNG or WebP photo.");
    if (f.size > MAX_MB * 1024 * 1024) return setError(`That photo is over ${MAX_MB} MB. Try a smaller one.`);
    setError(""); setPhoto((old) => { if (old) URL.revokeObjectURL(old.url); return { url: URL.createObjectURL(f), name: f.name }; });
  }
  function run(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return setError("Give the product a name first.");
    setError(""); setSubmitted({ name, details }); setGenerated(true); setFlash((n) => n + 1); setTab("Title");
  }
  const text: Record<Tab, string> = {
    Title: kit.title, Description: kit.description, Tags: kit.tags.join(", "), Caption: `${kit.caption}\n${kit.hashtags.join(" ")}`,
    Video: kit.beats.map((b) => `${b.t} ${b.label}: ${b.text}`).join("\n"),
  };
  const ready = status.data && !status.data.demo_mode && status.data.llm.reachable && status.data.llm.model_available;

  return (
    <section id="studio" className="light relative scroll-mt-16 py-[clamp(4rem,10vw,8rem)]" aria-labelledby="studio-h">
      <div className="wrap">
        <p className="label tick reveal">Interactive studio</p>
        <h2 id="studio-h" className="h2 reveal mt-3 max-w-3xl">One product. Every channel. <span className="serif">Ready to sell.</span></h2>
        <p className="lede reveal mt-4 max-w-2xl muted">Try it with the sample, or add your own photo and facts. This page runs in <strong className="text-[var(--text-l)]">demo mode</strong>: copy is assembled in your browser from the facts you type, and anything you don&apos;t give it is listed as missing, never invented.</p>

        <div className="mt-10 grid gap-5 lg:grid-cols-[minmax(0,.95fr)_minmax(0,1.05fr)]">
          <form onSubmit={run} className="panel-l space-y-5 p-4 sm:p-6" aria-label="Product details">
            <div>
              <p className="label muted">1 · Photo</p>
              <div className={`mt-2 grid gap-3 rounded-2xl border border-dashed p-3 transition sm:grid-cols-[8.5rem_1fr] ${drag ? "border-[#037A84] bg-[#E1F3F5]" : "border-black/20"}`}
                onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={(e) => { e.preventDefault(); setDrag(false); take(e.dataTransfer.files?.[0]); }}>
                <div className="relative mx-auto aspect-[4/5] w-32 overflow-hidden rounded-xl bg-[var(--paper-2)] sm:w-full">
                  {photo ? // eslint-disable-next-line @next/next/no-img-element
                    <img src={photo.url} alt="Your uploaded product" className="size-full object-cover" /> : <SampleProduct id="st" className="size-full" />}
                  {photo && <button type="button" onClick={() => { setPhoto(null); if (fileRef.current) fileRef.current.value = ""; }} aria-label="Remove photo" className="absolute right-1 top-1 grid size-9 place-items-center rounded-full bg-black/70 text-white"><X className="size-4" aria-hidden /></button>}
                </div>
                <div className="flex flex-col justify-center gap-2">
                  <input ref={fileRef} id={`${uid}-f`} type="file" accept="image/*" className="sr-only" onChange={(e) => take(e.target.files?.[0])} />
                  <label htmlFor={`${uid}-f`} className="btn btn-ink !min-h-12 cursor-pointer text-sm"><ImagePlus className="size-4" aria-hidden />{photo ? "Choose a different photo" : "Upload a photo"}</label>
                  <button type="button" className="btn btn-ghost !min-h-12 text-sm" onClick={() => { setPhoto(null); setName(SAMPLE.name); setDetails(SAMPLE.details); setError(""); }}>Use the sample product</button>
                  <p className="text-xs muted">{photo ? `${photo.name}. Stays in your browser; the demo doesn't analyse it.` : "Drag a photo here, or use the sample. Max 10 MB."}</p>
                </div>
              </div>
            </div>
            <div className="grid gap-4">
              <div><label htmlFor={`${uid}-n`} className="label muted">2 · Product name</label>
                <input id={`${uid}-n`} value={name} onChange={(e) => setName(e.target.value)} maxLength={80} className="mt-2 min-h-12 w-full rounded-xl border border-black/20 bg-white px-3.5" /></div>
              <div><label htmlFor={`${uid}-d`} className="label muted">3 · Facts (one per line)</label>
                <textarea id={`${uid}-d`} value={details} onChange={(e) => setDetails(e.target.value)} rows={4} maxLength={600} className="mt-2 w-full rounded-xl border border-black/20 bg-white px-3.5 py-3 leading-relaxed" /></div>
            </div>
            <Choice label="4 · Platform" value={platform} onChange={setPlatform} items={PLATFORMS} />
            <Choice label="5 · Tone" value={tone} onChange={setTone} items={TONES} />
            {error && <p role="alert" className="rounded-xl bg-[#fde8e8] px-3.5 py-2.5 text-sm text-[#8a1c1c]">{error}</p>}
            <button type="submit" className="btn btn-ink w-full"><Sparkles className="size-4" aria-hidden />Generate marketing package</button>
          </form>

          <div className="panel-l flex min-w-0 flex-col p-4 sm:p-6" aria-live="polite">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="label muted">Output · {PLATFORMS.find((p) => p.value === platform)?.label} · {TONES.find((t) => t.value === tone)?.label}</p>
              <span key={flash} className={`chip text-[11px] ${generated ? "anim-copied" : ""}`}>{generated ? "Generated from your facts" : "Sample output"} · demo mode</span>
            </div>
            <div role="tablist" aria-label="Generated content" className="no-scrollbar -mx-1 mt-4 flex gap-1 overflow-x-auto px-1">
              {TABS.map((t) => <button key={t} role="tab" id={`${uid}-t-${t}`} aria-selected={tab === t} aria-controls={`${uid}-p`} onClick={() => setTab(t)}
                className={`min-h-11 shrink-0 rounded-full px-4 text-sm transition ${tab === t ? "bg-[var(--ink)] text-[var(--paper)]" : "hover:bg-black/5"}`}>{t}</button>)}
            </div>
            <div role="tabpanel" id={`${uid}-p`} aria-labelledby={`${uid}-t-${tab}`} className="mt-4 min-h-[15rem] flex-1 rounded-2xl bg-[var(--paper)] p-4 sm:p-5">
              {tab === "Title" && <p className="text-xl font-medium leading-snug sm:text-2xl">{kit.title}</p>}
              {tab === "Description" && <p className="leading-relaxed">{kit.description}</p>}
              {tab === "Tags" && <div className="flex flex-wrap gap-2">{kit.tags.length ? kit.tags.map((t) => <span key={t} className="chip">{t}</span>) : <p className="text-sm muted">Add a few facts to get tags.</p>}</div>}
              {tab === "Caption" && <div><p className="leading-relaxed">{kit.caption}</p><p className="mt-3 text-sm font-medium text-[#037A84]">{kit.hashtags.join(" ")}</p><p className="mt-3 text-sm muted">Call to action: {kit.cta}</p></div>}
              {tab === "Video" && <ol className="space-y-2.5">{kit.beats.map((b) => <li key={b.label} className="flex gap-3"><span className="mono w-14 shrink-0 text-xs muted">{b.t}</span><span><span className="label muted">{b.label}</span><br /><span className="font-medium">{b.text}</span></span></li>)}</ol>}
              {kit.missing.length > 0 && <p className="mt-5 border-t border-black/10 pt-3 text-[13px] muted">Not provided, so left out: <strong className="text-[var(--text-l)]">{kit.missing.join(", ")}</strong>.</p>}
            </div>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
              <CopyButton id={tab.toLowerCase()} text={text[tab]} done={done} onCopy={copy} light label={`Copy ${tab.toLowerCase()}`} />
              {DEMO_ONLY ? null : ready
                ? <Link href="/create" className="btn btn-ink !min-h-11 text-sm">Generate for real with Gemma <ArrowRight className="size-4" aria-hidden /></Link>
                : <Link href="/create" className="btn btn-ghost !min-h-11 text-sm">Open the real studio <ArrowRight className="size-4" aria-hidden /></Link>}
            </div>
            <p className="mt-3 text-xs muted">{DEMO_ONLY ? "This is a public demo: it runs entirely in your browser. The full app runs on your own computer with an open model, so your photos and facts never leave it." : ready ? `The real app is running here with ${status.data?.llm.model} on your computer, so it can write from your actual photo.` : status.isLoading ? "Checking for the local model…" : "The local AI engine isn't running here, so this page stays in demo mode. See the README to start Gemma with Ollama."}</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function Choice<T extends string>({ label, value, onChange, items }: { label: string; value: T; onChange: (v: T) => void; items: { value: T; label: string }[] }) {
  return (
    <div role="radiogroup" aria-label={label}>
      <p className="label muted">{label}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {items.map((i) => <button key={i.value} type="button" role="radio" aria-checked={value === i.value} onClick={() => onChange(i.value)}
          className={`min-h-11 rounded-full px-4 text-sm transition ${value === i.value ? "bg-[var(--ink)] text-[var(--paper)]" : "bg-white shadow-[inset_0_0_0_1px_rgb(11_11_10/.18)] hover:shadow-[inset_0_0_0_1px_rgb(11_11_10/.5)]"}`}>{i.label}</button>)}
      </div>
    </div>
  );
}
