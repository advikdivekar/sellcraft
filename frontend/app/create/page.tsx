"use client";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ImageDropzone, type UploadedImage } from "@/components/image-dropzone";
import { Button, Card, Chips, Field, cx, inputCls } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { OBJECTIVES, PLATFORMS, STYLES, TONES } from "@/lib/options";
import type { CreativeSettings, Objective, Platform, ProductInput, Tone, VisualStyle } from "@/lib/types";

const lines = (s: string) => s.split("\n").map((x) => x.trim()).filter(Boolean);

export default function CreatePage() {
  const router = useRouter();
  const status = useQuery({ queryKey: ["status"], queryFn: api.status });
  const [step, setStep] = useState<1 | 2>(1);
  const [image, setImage] = useState<UploadedImage | null>(null);
  const [f, setF] = useState({
    name: "", summary: "", price: "", currency: "USD", materials: "", dimensions: "", features: "", benefits: "",
    audience: "", brand_name: "", brand_voice: "", care: "", forbidden: "",
  });
  const [platforms, setPlatforms] = useState<Platform[]>(["instagram"]);
  const [tone, setTone] = useState<Tone>("friendly");
  const [style, setStyle] = useState<VisualStyle>("minimal");
  const [objective, setObjective] = useState<Objective>("sales");
  const [voiceover, setVoiceover] = useState(false);
  const [touched, setTouched] = useState(false);

  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setF({ ...f, [k]: e.target.value });
  const nameErr = touched && !f.name.trim() ? "Product name is required." : undefined;
  const imageErr = touched && !image ? "Add a product photo." : undefined;

  const create = useMutation({
    mutationFn: () => {
      const product: ProductInput = {
        name: f.name.trim(), image_asset_id: image!.assetId,
        summary: f.summary || null, price: f.price || null, currency: f.price ? f.currency || null : null,
        materials: f.materials || null, dimensions: f.dimensions || null,
        features: lines(f.features), benefits: lines(f.benefits), audience: f.audience || null,
        brand_name: f.brand_name || null, brand_voice: f.brand_voice || null, care_instructions: f.care || null,
        forbidden_words: f.forbidden.split(/[,\n]/).map((x) => x.trim()).filter(Boolean),
      };
      const settings: CreativeSettings = {
        platforms, tone, visual_style: style, objective, duration_seconds: 10, aspect_ratio: "9:16", voiceover,
      };
      return api.createJob(product, settings);
    },
    onSuccess: (job) => router.push(`/jobs/${job.id}`),
  });

  function next() {
    setTouched(true);
    if (!f.name.trim() || !image) return;
    setStep(2);
    window.scrollTo({ top: 0 });
  }
  function submit() {
    setTouched(true);
    if (!f.name.trim() || !image) { setStep(1); return; }
    create.mutate();
  }

  const allSelected = platforms.length === PLATFORMS.length;
  const togglePlatform = (p: Platform) =>
    setPlatforms((cur) => (cur.includes(p) ? (cur.length > 1 ? cur.filter((x) => x !== p) : cur) : [...cur, p]));
  const canVoice = status.data?.voiceover.configured;

  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-4 pb-32 pt-6 sm:px-6 md:pb-12">
      <div className="mb-6 flex items-center justify-between">
        <Link href="/" className="inline-flex min-h-11 items-center gap-1.5 text-sm text-muted hover:text-foreground"><ArrowLeft className="size-4" />Home</Link>
        <p className="text-sm text-muted md:hidden" aria-live="polite">Step {step} of 2</p>
      </div>
      <h1 className="mb-6 text-2xl font-semibold tracking-tight sm:text-3xl">Create a marketing kit</h1>

      <div className="grid gap-5 md:grid-cols-2 md:items-start">
        {/* ---------- Product ---------- */}
        <div className={cx("space-y-5", step === 1 ? "block" : "hidden md:block")}>
          <Card>
            <h2 className="mb-3 font-medium">Product photo</h2>
            <ImageDropzone value={image} onChange={setImage} />
            {imageErr && <p role="alert" className="mt-2 text-sm text-danger">{imageErr}</p>}
          </Card>
          <Card className="space-y-4">
            <h2 className="font-medium">Product facts</h2>
            <p className="-mt-2 text-xs text-muted">Only add what is true. Blank fields are never guessed. They are flagged as missing.</p>
            <Field label="Product name" error={nameErr}>
              <input className={inputCls} value={f.name} onChange={set("name")} maxLength={120} autoComplete="off" placeholder="e.g. Silver moon necklace" />
            </Field>
            <Field label="Short summary" optional><textarea className={inputCls} rows={2} value={f.summary} onChange={set("summary")} maxLength={1000} /></Field>
            <div className="grid grid-cols-[1fr_6rem] gap-3">
              <Field label="Price" optional><input className={inputCls} inputMode="decimal" value={f.price} onChange={set("price")} maxLength={40} placeholder="29.00" /></Field>
              <Field label="Currency" optional><input className={inputCls} value={f.currency} onChange={set("currency")} maxLength={8} autoCapitalize="characters" /></Field>
            </div>
            <Field label="Materials / ingredients" optional><input className={inputCls} value={f.materials} onChange={set("materials")} maxLength={500} /></Field>
            <Field label="Dimensions / size" optional><input className={inputCls} value={f.dimensions} onChange={set("dimensions")} maxLength={300} /></Field>
            <Field label="Main features" optional hint="One per line"><textarea className={inputCls} rows={3} value={f.features} onChange={set("features")} /></Field>
            <Field label="Verified benefits" optional hint="One per line. Only benefits you can stand behind."><textarea className={inputCls} rows={3} value={f.benefits} onChange={set("benefits")} /></Field>
            <Field label="Care / usage" optional><input className={inputCls} value={f.care} onChange={set("care")} maxLength={500} /></Field>
            <details className="group rounded-xl border border-border px-3.5 py-2">
              <summary className="min-h-11 cursor-pointer list-none py-2.5 text-sm font-medium">Brand &amp; audience details <span className="text-muted">(optional)</span></summary>
              <div className="space-y-4 pb-3">
                <Field label="Target audience" optional><input className={inputCls} value={f.audience} onChange={set("audience")} maxLength={300} /></Field>
                <Field label="Brand name" optional><input className={inputCls} value={f.brand_name} onChange={set("brand_name")} maxLength={80} /></Field>
                <Field label="Brand voice" optional><textarea className={inputCls} rows={2} value={f.brand_voice} onChange={set("brand_voice")} maxLength={500} /></Field>
                <Field label="Words or claims to avoid" optional hint="Separate with commas"><input className={inputCls} value={f.forbidden} onChange={set("forbidden")} placeholder="cheap, best, guaranteed" /></Field>
              </div>
            </details>
          </Card>
        </div>

        {/* ---------- Creative ---------- */}
        <div className={cx("space-y-5", step === 2 ? "block" : "hidden md:block")}>
          <Card className="space-y-5">
            <div>
              <div className="mb-2 flex items-center justify-between">
                <h2 className="font-medium">Platform</h2>
                <button type="button" className="min-h-11 text-sm text-accent" onClick={() => setPlatforms(allSelected ? ["instagram"] : PLATFORMS.map((p) => p.value))}>
                  {allSelected ? "Just one" : "Select all five"}
                </button>
              </div>
              <Chips multi label="Platforms" options={PLATFORMS} value={platforms} onChange={togglePlatform} />
              {platforms.length > 1 && <p className="mt-2 text-xs text-muted">One video is shared across platforms; copy is written separately for each.</p>}
            </div>
            <div><h2 className="mb-2 font-medium">Writing tone</h2><Chips label="Tone" options={TONES} value={tone} onChange={setTone} /></div>
            <div><h2 className="mb-2 font-medium">Visual style</h2><Chips label="Visual style" options={STYLES} value={style} onChange={setStyle} /></div>
            <div><h2 className="mb-2 font-medium">Marketing goal</h2><Chips label="Marketing goal" options={OBJECTIVES} value={objective} onChange={setObjective} /></div>
          </Card>
          <Card>
            <h2 className="mb-1 font-medium">Video</h2>
            <p className="text-sm text-muted">10 seconds, vertical 9:16.</p>
            <label className={cx("mt-3 flex min-h-11 items-start gap-3", !canVoice && "opacity-60")}>
              <input type="checkbox" className="mt-1 size-5 accent-[var(--accent)]" checked={voiceover && !!canVoice} disabled={!canVoice} onChange={(e) => setVoiceover(e.target.checked)} />
              <span className="text-sm"><span className="font-medium">Add AI voiceover</span>
                <span className="block text-xs text-muted">{canVoice ? "Uses ElevenLabs. Your script is sent to their service." : "Needs an ElevenLabs key on the server. The script is still written for you."}</span></span>
            </label>
          </Card>
          {create.isError && (
            <div role="alert" className="rounded-xl border border-danger/40 bg-danger/10 p-3 text-sm text-danger">
              {(create.error as ApiError).message}
            </div>
          )}
          <div className="hidden md:block">
            <Button className="w-full" busy={create.isPending} onClick={submit}><Sparkles className="size-5" />Generate marketing kit</Button>
          </div>
        </div>
      </div>

      {/* Sticky mobile action bar */}
      <div className="pb-safe fixed inset-x-0 bottom-0 z-10 border-t border-border bg-background/95 px-4 pt-3 backdrop-blur md:hidden">
        {step === 1 ? (
          <Button className="w-full" onClick={next}>Next: choose style</Button>
        ) : (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setStep(1)} aria-label="Back to product details"><ArrowLeft className="size-5" /></Button>
            <Button className="flex-1" busy={create.isPending} onClick={submit}><Sparkles className="size-5" />Generate</Button>
          </div>
        )}
      </div>
    </main>
  );
}
