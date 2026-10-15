"use client";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, ChevronDown, Loader2, ScanSearch, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { ImageDropzone, type UploadedImage } from "@/components/image-dropzone";
import { Stepper } from "@/components/stepper";
import { Button, Card, Chips, Field, SectionTitle, Skeleton, cx, inputCls } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { OBJECTIVES, PLATFORMS, STYLES, TONES } from "@/lib/options";
import type { CreativeSettings, Objective, Platform, ProductInput, Tone, VisualStyle } from "@/lib/types";

const EMPTY = {
  name: "", summary: "", price: "", currency: "USD", materials: "", dimensions: "", features: "", benefits: "",
  audience: "", brand_name: "", brand_voice: "", care: "", forbidden: "", extra: "",
};
type Form = typeof EMPTY;
type Draft = { v: Form; platforms: Platform[]; tone: Tone; style: VisualStyle; objective: Objective; voiceover: boolean };
const DRAFT_KEY = "sellcraft:draft:v1";
const lines = (s: string) => s.split("\n").map((x) => x.trim()).filter(Boolean);

const STYLE_META: Record<VisualStyle, { blurb: string; swatch: string }> = {
  premium_studio: { blurb: "Dark, glossy, spotlit", swatch: "from-[#0b0b0f] to-[#2b2834]" },
  minimal: { blurb: "Clean and airy", swatch: "from-[#f6f3ee] to-[#d9d1c4]" },
  warm_cozy: { blurb: "Warm, soft, inviting", swatch: "from-[#46291a] to-[#92583a]" },
  bold_colorful: { blurb: "Punchy and energetic", swatch: "from-[#ff5638] to-[#ffb028]" },
  ugc: { blurb: "Natural, social-first", swatch: "from-[#eee7e0] to-[#cfc5bd]" },
};

function readDraft(): Draft | null {
  try { const r = localStorage.getItem(DRAFT_KEY); return r ? (JSON.parse(r) as Draft) : null; } catch { return null; }
}
const noopSubscribe = () => () => {};

export default function CreatePage() {
  const mounted = useSyncExternalStore(noopSubscribe, () => true, () => false);
  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-36 pt-6 sm:px-6 lg:pb-12">
      {mounted ? <Wizard /> : <div className="space-y-4"><Skeleton className="h-10 w-72" /><Skeleton className="h-64 w-full" /></div>}
    </main>
  );
}

function Wizard() {
  const router = useRouter();
  const status = useQuery({ queryKey: ["status"], queryFn: api.status });
  const [draft] = useState<Draft | null>(readDraft);

  const [step, setStep] = useState(0);
  const [reached, setReached] = useState(0);
  const [touched, setTouched] = useState(false);
  const [images, setImages] = useState<UploadedImage[]>([]);
  const imagesRef = useRef<UploadedImage[]>([]);
  const scanned = useRef(false);
  const scanToken = useRef(0);
  const [form, setForm] = useState<{ v: Form; s: string[] }>({ v: { ...EMPTY, ...(draft?.v ?? {}) }, s: [] });
  const [moreOpen, setMoreOpen] = useState(() => Boolean(draft && Object.entries(draft.v).some(([k, x]) => !["name", "price", "currency"].includes(k) && x && x !== "USD")));
  const [platforms, setPlatforms] = useState<Platform[]>(draft?.platforms ?? ["instagram"]);
  const [tone, setTone] = useState<Tone>(draft?.tone ?? "friendly");
  const [style, setStyle] = useState<VisualStyle>(draft?.style ?? "premium_studio");
  const [objective, setObjective] = useState<Objective>(draft?.objective ?? "sales");
  const [voiceover, setVoiceover] = useState(draft?.voiceover ?? false);
  const [scan, setScan] = useState<{ state: "idle" | "running" | "done" | "error"; message?: string; visible: string[] }>({ state: "idle", visible: [] });
  const f = form.v;

  // Autosave the draft (text and settings; photos can't be saved) so a refresh never loses typing.
  useEffect(() => {
    const t = setTimeout(() => { try { localStorage.setItem(DRAFT_KEY, JSON.stringify({ v: f, platforms, tone, style, objective, voiceover } satisfies Draft)); } catch { /* storage unavailable */ } }, 400);
    return () => clearTimeout(t);
  }, [f, platforms, tone, style, objective, voiceover]);

  const updateImages = (fn: (cur: UploadedImage[]) => UploadedImage[]) => {
    imagesRef.current = fn(imagesRef.current);
    setImages(imagesRef.current);
    if (imagesRef.current.length === 0) { scanned.current = false; scanToken.current++; setScan({ state: "idle", visible: [] }); }
  };
  const set = (k: keyof Form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((c) => ({ v: { ...c.v, [k]: e.target.value }, s: c.s.filter((x) => x !== k) }));
  const sug = (k: string) => form.s.includes(k);

  async function analyze(ids: string[]) {
    const token = ++scanToken.current;
    setScan({ state: "running", visible: [] });
    try {
      const r = await api.analyze(ids);
      if (token !== scanToken.current) return;
      const fl = r.fields;
      setForm((c) => {
        const v = { ...c.v }, s = [...c.s];
        const put = (k: keyof Form, val?: string) => { if (val && !v[k].trim()) { v[k] = val; if (!s.includes(k)) s.push(k); } };
        put("name", fl.name); put("brand_name", fl.brand_name); put("summary", fl.summary);
        put("materials", fl.materials); put("dimensions", fl.dimensions); put("features", fl.features?.join("\n"));
        return { v, s };
      });
      setMoreOpen(true);
      setScan({ state: "done", visible: fl.visible_text ?? [], message: r.note });
    } catch (e) {
      if (token !== scanToken.current) return;
      setScan({ state: "error", visible: [], message: e instanceof ApiError ? e.message : "Couldn't read the photo." });
    }
  }
  const onPhotosAdded = () => { if (!scanned.current) { scanned.current = true; analyze(imagesRef.current.map((i) => i.assetId)); } };
  const addNote = (t: string) => setForm((c) => ({ v: { ...c.v, extra: c.v.extra.includes(t) ? c.v.extra : (c.v.extra ? c.v.extra + "\n" : "") + t }, s: c.s }));

  const nameErr = touched && !f.name.trim() ? "Add a product name." : undefined;
  const photoErr = touched && images.length === 0 ? "Add at least one photo." : undefined;

  const create = useMutation({
    mutationFn: () => {
      const product: ProductInput = {
        name: f.name.trim(), image_asset_ids: images.map((i) => i.assetId),
        summary: f.summary || null, price: f.price || null, currency: f.price ? f.currency || null : null,
        materials: f.materials || null, dimensions: f.dimensions || null, features: lines(f.features), benefits: lines(f.benefits),
        audience: f.audience || null, brand_name: f.brand_name || null, brand_voice: f.brand_voice || null,
        care_instructions: f.care || null, extra_notes: f.extra || null,
        forbidden_words: f.forbidden.split(/[,\n]/).map((x) => x.trim()).filter(Boolean),
      };
      const settings: CreativeSettings = { platforms, tone, visual_style: style, objective, duration_seconds: 10, aspect_ratio: "9:16", voiceover };
      return api.createJob(product, settings);
    },
    onSuccess: (job) => { try { localStorage.removeItem(DRAFT_KEY); } catch { /* ignore */ } router.push(`/jobs/${job.id}`); },
  });

  const go = (i: number) => { setStep(i); setReached((r) => Math.max(r, i)); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const next = () => {
    setTouched(true);
    if (step === 0 && images.length === 0) return;
    if (step === 1 && !f.name.trim()) return;
    go(step + 1);
  };
  const submit = () => {
    setTouched(true);
    if (images.length === 0) return go(0);
    if (!f.name.trim()) return go(1);
    create.mutate();
  };

  const allSelected = platforms.length === PLATFORMS.length;
  const togglePlatform = (p: Platform) => setPlatforms((cur) => (cur.includes(p) ? (cur.length > 1 ? cur.filter((x) => x !== p) : cur) : [...cur, p]));
  const canVoice = status.data?.voiceover.configured;

  return (
    <>
      <div className="mb-6 space-y-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Create a marketing kit</h1>
          <p className="mt-1 text-muted">Three quick steps. Your draft is saved automatically.</p>
        </div>
        <Stepper steps={["Photos", "Facts", "Style"]} current={step} onGo={go} maxReached={reached} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px] lg:items-start">
        <div key={step} className="anim-in space-y-5">
          {step === 0 && (
            <Card>
              <SectionTitle hint="Different angles make a better video and deck. The first photo is your main one.">Product photos</SectionTitle>
              <ImageDropzone value={images} update={updateImages} onAdded={onPhotosAdded} />
              {photoErr && <p role="alert" className="mt-3 text-sm font-medium text-danger">{photoErr}</p>}
              <ScanStatus scan={scan} filled={form.s.length} onRescan={() => images.length > 0 && analyze(images.map((i) => i.assetId))} onAdd={addNote} />
            </Card>
          )}

          {step === 1 && (
            <Card className="space-y-5">
              <SectionTitle hint="Only add what is true. Blank fields are flagged as missing, never guessed.">About your product</SectionTitle>
              <Field label="Product name" error={nameErr} suggested={sug("name")}>
                <input className={inputCls} value={f.name} onChange={set("name")} maxLength={120} autoComplete="off" placeholder="e.g. Silver moon necklace" autoFocus />
              </Field>
              <div className="grid grid-cols-[1fr_6.5rem] gap-3">
                <Field label="Price" optional><input className={inputCls} inputMode="decimal" value={f.price} onChange={set("price")} maxLength={40} placeholder="29.00" /></Field>
                <Field label="Currency" optional><input className={inputCls} value={f.currency} onChange={set("currency")} maxLength={8} autoCapitalize="characters" /></Field>
              </div>
              <button type="button" onClick={() => setMoreOpen((o) => !o)} aria-expanded={moreOpen}
                className="flex min-h-12 w-full items-center justify-between rounded-xl border border-border-strong bg-surface-2 px-4 text-left text-sm font-medium transition hover:bg-accent-soft">
                <span>More details <span className="font-normal text-muted">(better copy, optional)</span></span>
                <ChevronDown className={cx("size-4 text-muted transition-transform", moreOpen && "rotate-180")} aria-hidden />
              </button>
              {moreOpen && (
                <div className="anim-in space-y-5">
                  <Field label="Short summary" optional suggested={sug("summary")}><textarea className={inputCls} rows={2} value={f.summary} onChange={set("summary")} maxLength={1000} /></Field>
                  <Field label="Main features" optional hint="One per line" suggested={sug("features")}><textarea className={inputCls} rows={3} value={f.features} onChange={set("features")} /></Field>
                  <Field label="Verified benefits" optional hint="One per line. Only what you can stand behind. Powers the benefits slide."><textarea className={inputCls} rows={3} value={f.benefits} onChange={set("benefits")} /></Field>
                  <div className="grid gap-5 sm:grid-cols-2">
                    <Field label="Materials / ingredients" optional suggested={sug("materials")}><input className={inputCls} value={f.materials} onChange={set("materials")} maxLength={500} /></Field>
                    <Field label="Dimensions / size" optional suggested={sug("dimensions")}><input className={inputCls} value={f.dimensions} onChange={set("dimensions")} maxLength={300} /></Field>
                    <Field label="Brand name" optional suggested={sug("brand_name")}><input className={inputCls} value={f.brand_name} onChange={set("brand_name")} maxLength={80} /></Field>
                    <Field label="Target audience" optional><input className={inputCls} value={f.audience} onChange={set("audience")} maxLength={300} /></Field>
                  </div>
                  <Field label="Care / usage" optional><input className={inputCls} value={f.care} onChange={set("care")} maxLength={500} /></Field>
                  <Field label="Anything else to add?" optional hint="What photos can't show: flavours, sizes, offers you really run."><textarea className={inputCls} rows={3} value={f.extra} onChange={set("extra")} maxLength={1000} /></Field>
                  <Field label="Brand voice" optional><textarea className={inputCls} rows={2} value={f.brand_voice} onChange={set("brand_voice")} maxLength={500} /></Field>
                  <Field label="Words or claims to avoid" optional hint="Separate with commas"><input className={inputCls} value={f.forbidden} onChange={set("forbidden")} placeholder="cheap, best, guaranteed" /></Field>
                </div>
              )}
            </Card>
          )}

          {step === 2 && (
            <>
              <Card className="space-y-6">
                <div>
                  <SectionTitle action={<button type="button" className="min-h-11 text-sm font-medium text-accent" onClick={() => setPlatforms(allSelected ? ["instagram"] : PLATFORMS.map((p) => p.value))}>{allSelected ? "Just one" : "Select all"}</button>}>Where will you sell?</SectionTitle>
                  <Chips multi label="Platforms" options={PLATFORMS} value={platforms} onChange={togglePlatform} />
                  {platforms.length > 1 && <p className="mt-2 text-xs text-muted">One video and deck are shared; copy is written separately for each platform.</p>}
                </div>
                <div><SectionTitle>Writing tone</SectionTitle><Chips label="Tone" options={TONES} value={tone} onChange={setTone} /></div>
                <div><SectionTitle>Marketing goal</SectionTitle><Chips label="Marketing goal" options={OBJECTIVES} value={objective} onChange={setObjective} /></div>
              </Card>
              <Card>
                <SectionTitle hint="Sets the backdrop, lighting and mood of your photos, deck and video.">Visual style</SectionTitle>
                <div role="radiogroup" aria-label="Visual style" className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {STYLES.map((s) => (
                    <button key={s.value} type="button" role="radio" aria-checked={style === s.value} onClick={() => setStyle(s.value)}
                      className={cx("group overflow-hidden rounded-2xl border text-left transition active:scale-[0.98]", style === s.value ? "border-accent ring-2 ring-accent/30" : "border-border-strong hover:border-foreground/40")}>
                      <div className={`relative h-20 bg-gradient-to-b ${STYLE_META[s.value].swatch}`}>
                        <span className="absolute left-1/2 top-1/2 h-10 w-7 -translate-x-1/2 -translate-y-1/2 rounded-[45%] bg-white/30 shadow-lg" />
                      </div>
                      <div className="p-3"><p className="text-sm font-medium">{s.label}</p><p className="text-xs text-muted">{STYLE_META[s.value].blurb}</p></div>
                    </button>
                  ))}
                </div>
              </Card>
              <Card>
                <label className={cx("flex min-h-11 items-start gap-3", !canVoice && "opacity-60")}>
                  <input type="checkbox" className="mt-1 size-5 accent-[var(--accent)]" checked={voiceover && !!canVoice} disabled={!canVoice} onChange={(e) => setVoiceover(e.target.checked)} />
                  <span><span className="block text-sm font-medium">Add AI voiceover</span>
                    <span className="block text-xs text-muted">{canVoice ? "Uses ElevenLabs. Your script is sent to their service." : "Coming soon: needs an ElevenLabs key. The script is still written for you."}</span></span>
                </label>
              </Card>
            </>
          )}

          {create.isError && <div role="alert" className="rounded-xl border border-danger/40 bg-danger/10 p-3.5 text-sm font-medium text-danger">{(create.error as ApiError).message}</div>}
        </div>

        {/* Summary rail (desktop) */}
        <aside className="hidden space-y-4 lg:sticky lg:top-20 lg:block">
          <Card className="space-y-4">
            <h2 className="font-semibold">Your kit</h2>
            {images.length > 0 ? (
              <div className="flex gap-1.5">{images.slice(0, 5).map((i, n) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img key={i.assetId} src={i.previewUrl} alt="" className={cx("size-14 rounded-lg object-cover", n === 0 && "ring-2 ring-accent")} />))}</div>
            ) : <p className="text-sm text-muted">No photos yet</p>}
            <dl className="space-y-1.5 text-sm">
              <Row k="Product" v={f.name || "-"} /><Row k="Platforms" v={platforms.map((p) => PLATFORMS.find((x) => x.value === p)!.label).join(", ")} />
              <Row k="Tone" v={TONES.find((t) => t.value === tone)!.label} /><Row k="Style" v={STYLES.find((s) => s.value === style)!.label} />
            </dl>
            <ul className="space-y-1 border-t border-border pt-3 text-xs text-muted">
              <li>Refined studio photos</li><li>Image deck (hero, benefits, close-up, CTA)</li><li>10-second vertical video</li><li>Copy for {platforms.length} platform{platforms.length > 1 ? "s" : ""}</li>
            </ul>
            <Button className="w-full" size="lg" busy={create.isPending} onClick={submit}><Sparkles className="size-5" />Generate kit</Button>
            <p className="text-center text-xs text-muted">Takes about a minute</p>
          </Card>
        </aside>
      </div>

      {/* Mobile action bar */}
      <div className="pb-safe fixed inset-x-0 bottom-0 z-20 border-t border-border bg-background/90 px-4 pt-3 backdrop-blur-md lg:hidden">
        <div className="mx-auto flex max-w-xl gap-2">
          {step > 0 && <Button variant="secondary" size="lg" onClick={() => go(step - 1)} aria-label="Back"><ArrowLeft className="size-5" /></Button>}
          {step < 2
            ? <Button className="flex-1" size="lg" onClick={next}>Next <ArrowRight className="size-5" /></Button>
            : <Button className="flex-1" size="lg" busy={create.isPending} onClick={submit}><Sparkles className="size-5" />Generate kit</Button>}
        </div>
      </div>
      <div className="mt-8 hidden justify-between lg:flex">
        {step > 0 ? <Button variant="ghost" onClick={() => go(step - 1)}><ArrowLeft className="size-4" />Back</Button> : <span />}
        {step < 2 && <Button onClick={next}>Continue <ArrowRight className="size-4" /></Button>}
      </div>
    </>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return <div className="flex justify-between gap-3"><dt className="text-muted">{k}</dt><dd className="truncate text-right font-medium">{v}</dd></div>;
}

function ScanStatus({ scan, filled, onRescan, onAdd }: {
  scan: { state: "idle" | "running" | "done" | "error"; message?: string; visible: string[] }; filled: number; onRescan: () => void; onAdd: (t: string) => void;
}) {
  if (scan.state === "idle") return null;
  if (scan.state === "running")
    return <p role="status" className="mt-4 flex items-center gap-2 rounded-xl bg-accent-soft px-3.5 py-3 text-sm"><Loader2 className="size-4 animate-spin text-accent" />Reading your photos to pre-fill the form… you can keep going.</p>;
  if (scan.state === "error")
    return (
      <div role="alert" className="mt-4 space-y-2 rounded-xl border border-warn/40 bg-warn/10 p-3.5 text-sm">
        <p>{scan.message} You can still fill in the facts yourself.</p>
        <Button variant="secondary" size="sm" onClick={onRescan}><ScanSearch className="size-4" />Try again</Button>
      </div>
    );
  return (
    <div className="anim-in mt-4 space-y-3 rounded-xl bg-accent-soft p-3.5 text-sm">
      <p>{scan.message ?? (filled > 0 ? `We pre-filled ${filled} field${filled > 1 ? "s" : ""} from your photos. They're marked "From photo". Check them on the next step.` : "We couldn't read anything useful from these photos. You can add the facts yourself.")}</p>
      {scan.visible.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-medium text-muted">Text we read on the photo. Tap to add it to your notes:</p>
          <div className="flex flex-wrap gap-1.5">{scan.visible.map((t) => <button key={t} type="button" onClick={() => onAdd(t)} className="min-h-9 rounded-full border border-border-strong bg-surface px-3 text-xs transition hover:bg-background">{t}</button>)}</div>
        </div>
      )}
      <Button variant="ghost" size="sm" onClick={onRescan}><ScanSearch className="size-4" />Scan again</Button>
    </div>
  );
}
