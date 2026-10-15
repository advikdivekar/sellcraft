"use client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Download, Info, Sparkles } from "lucide-react";
import { useState } from "react";
import { LISTING_SECTIONS, PLATFORMS, PLATFORM_FIELD_LABELS, SOCIAL_SECTIONS, TONES, VIDEO_SECTIONS, type SectionDef } from "@/lib/options";
import { copyText } from "@/lib/image";
import { ApiError, api } from "@/lib/api";
import type { CopyOutput, GenerationJob, Platform, Tone } from "@/lib/types";
import { EditableField } from "./editable-field";
import { Button, Card, Chips, cx } from "./ui";

type Tab = "listing" | "social" | "video" | Platform;

function download(name: string, text: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function asText(c: CopyOutput, platforms: Platform[]) {
  const out: string[] = [];
  const add = (title: string, s: SectionDef[], get: (k: string) => string | string[] | undefined) => {
    out.push(`# ${title}`);
    for (const f of s) { const v = get(f.key); out.push(`\n## ${f.label}\n${Array.isArray(v) ? v.map((x) => `- ${x}`).join("\n") : (v ?? "")}`); }
    out.push("");
  };
  add("Listing", LISTING_SECTIONS, (k) => c[k as keyof CopyOutput] as string | string[]);
  add("Social", SOCIAL_SECTIONS, (k) => c[k as keyof CopyOutput] as string | string[]);
  for (const p of platforms) add(p, PLATFORM_FIELD_LABELS[p], (k) => c.platform_outputs[p]?.[k]);
  add("Video brief", VIDEO_SECTIONS, (k) => c[k as keyof CopyOutput] as string | string[]);
  return out.join("\n");
}

export function Results({ job }: { job: GenerationJob }) {
  const qc = useQueryClient();
  const copy = job.copy_output!;
  const platforms = job.settings.platforms;
  const [tab, setTab] = useState<Tab>("listing");
  const [tone, setTone] = useState<Tone>(job.settings.tone);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const update = (j: GenerationJob) => qc.setQueryData(["job", job.id], j);
  const onError = (e: unknown) => setErr(e instanceof ApiError ? e.message : "Something went wrong.");

  const save = useMutation({ mutationFn: (c: CopyOutput) => api.saveCopy(job.id, c), onSuccess: update, onError });
  const regen = useMutation({
    mutationFn: (v: { section?: string; tone?: Tone }) => api.regenerate(job.id, { section: v.section ?? null, tone: v.tone ?? null }),
    onMutate: (v) => { setErr(null); setBusyKey(v.section ?? "__all"); },
    onSuccess: update, onError, onSettled: () => setBusyKey(null),
  });

  const setCore = (key: string) => (v: string | string[]) => save.mutate({ ...copy, [key]: v } as CopyOutput);
  const setPlat = (p: Platform, key: string) => (v: string | string[]) =>
    save.mutate({ ...copy, platform_outputs: { ...copy.platform_outputs, [p]: { ...copy.platform_outputs[p], [key]: v } } });

  const core = (s: SectionDef) => (
    <EditableField key={s.key} label={s.label} kind={s.kind} rows={s.rows} value={copy[s.key as keyof CopyOutput] as string | string[]}
      onCommit={setCore(s.key)} onRegenerate={() => regen.mutate({ section: s.key })} busy={busyKey === s.key} />
  );

  const tabs: { id: Tab; label: string }[] = [
    { id: "listing", label: "Listing" }, { id: "social", label: "Social" },
    ...platforms.map((p) => ({ id: p as Tab, label: PLATFORMS.find((x) => x.value === p)!.label })),
    { id: "video", label: "Video" },
  ];

  const words = copy.voiceover_script.trim().split(/\s+/).filter(Boolean).length;
  const secs = Math.round((words / 2.5) * 10) / 10;
  const video = job.assets.find((a) => a.kind === "video");

  return (
    <div className="space-y-5">
      <SourceBanner source={job.copy_source} />

      {(copy.missing_information.length > 0 || copy.claims_requiring_review.length > 0) && (
        <Card className="space-y-3 border-warn/50">
          {copy.missing_information.length > 0 && (
            <div>
              <h3 className="mb-1 flex items-center gap-2 text-sm font-medium"><Info className="size-4 text-warn" />Not provided, so left out of the copy</h3>
              <p className="text-sm text-muted">{copy.missing_information.join(" · ")}</p>
            </div>
          )}
          {copy.claims_requiring_review.length > 0 && (
            <div>
              <h3 className="mb-1 flex items-center gap-2 text-sm font-medium"><AlertTriangle className="size-4 text-warn" />Double-check before posting</h3>
              <ul className="list-disc space-y-0.5 pl-5 text-sm text-muted">{copy.claims_requiring_review.map((c) => <li key={c}>{c}</li>)}</ul>
            </div>
          )}
        </Card>
      )}

      <Card className="space-y-3">
        <h3 className="text-sm font-medium">Rewrite all copy in a different tone</h3>
        <Chips label="Tone" options={TONES} value={tone} onChange={setTone} />
        <Button variant="secondary" busy={busyKey === "__all"} onClick={() => regen.mutate({ tone })}>
          <Sparkles className="size-4" />Rewrite copy
        </Button>
        <p className="text-xs text-muted">Your product facts stay the same and the video is not re-made. This replaces your manual edits to the copy.</p>
      </Card>

      {err && <div role="alert" className="rounded-xl border border-danger/40 bg-danger/10 p-3 text-sm text-danger">{err}</div>}

      <div role="tablist" aria-label="Result sections" className="-mx-4 flex gap-1 overflow-x-auto px-4 pb-1 sm:mx-0 sm:px-0">
        {tabs.map((t) => (
          <button key={t.id} role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)}
            className={cx("min-h-11 shrink-0 rounded-full px-4 text-sm font-medium", tab === t.id ? "bg-foreground text-background" : "text-muted hover:bg-accent-soft")}>
            {t.label}
          </button>
        ))}
      </div>

      <Card className="space-y-5" >
        {tab === "listing" && LISTING_SECTIONS.map(core)}
        {tab === "social" && SOCIAL_SECTIONS.map(core)}
        {platforms.includes(tab as Platform) && (
          <>
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-medium">{PLATFORMS.find((x) => x.value === tab)!.label} copy</h3>
              <Button variant="secondary" size="sm" busy={busyKey === `platform:${tab}`} onClick={() => regen.mutate({ section: `platform:${tab}` })}>Regenerate all</Button>
            </div>
            {PLATFORM_FIELD_LABELS[tab as Platform].map((f) => (
              <EditableField key={f.key} label={f.label} kind={f.kind} rows={f.rows} value={copy.platform_outputs[tab]?.[f.key]} onCommit={setPlat(tab as Platform, f.key)} />
            ))}
          </>
        )}
        {tab === "video" && (
          <>
            <div className="rounded-xl border border-border bg-background p-4">
              {video ? (
                <video className="mx-auto max-h-[70dvh] rounded-lg" src={api.assetUrl(job.id, video.id)} controls playsInline preload="metadata" />
              ) : (
                <p className="text-sm text-muted">The video isn&apos;t generated yet. The brief below is ready for it.</p>
              )}
              {video && <p className="mt-2 text-center text-xs text-muted">{video.method === "animated_photo" ? "Animated-photo ad (your photo with motion and text, not AI-generated footage)" : `AI-generated video (${video.method})`}</p>}
            </div>
            {VIDEO_SECTIONS.map(core)}
            <p className={cx("-mt-3 text-xs", secs > 10 ? "text-danger" : "text-muted")}>
              Voiceover: {words} words, about {secs}s spoken{secs > 10 ? ". Too long for a 10-second ad, so please shorten it." : "."}
            </p>
            <div>
              <h4 className="mb-2 text-sm font-medium">Storyboard</h4>
              <ol className="space-y-2">
                {copy.video_storyboard.map((b, i) => (
                  <li key={i} className="rounded-xl border border-border p-3 text-sm">
                    <span className="font-medium text-accent">{b.time}</span> {b.visual}
                    {b.on_screen_text && <span className="mt-0.5 block text-muted">On screen: &ldquo;{b.on_screen_text}&rdquo;</span>}
                  </li>
                ))}
              </ol>
            </div>
          </>
        )}
      </Card>

      <Card className="flex flex-wrap gap-2">
        <Button variant="secondary" onClick={() => copyText(asText(copy, platforms))}>Copy everything</Button>
        <Button variant="secondary" onClick={() => download(`${slug(job.product.name)}-listing.txt`, asText(copy, platforms), "text/plain")}><Download className="size-4" />Listing .txt</Button>
        <Button variant="secondary" onClick={() => download(`${slug(job.product.name)}-listing.json`, JSON.stringify(copy, null, 2), "application/json")}><Download className="size-4" />Listing .json</Button>
        {video && <a className="inline-flex min-h-12 items-center gap-2 rounded-xl border border-border bg-surface px-5 hover:bg-accent-soft" href={api.assetUrl(job.id, video.id)} download><Download className="size-4" />Video .mp4</a>}
      </Card>
    </div>
  );
}

const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "product";

function SourceBanner({ source }: { source: string | null }) {
  if (!source) return null;
  const demo = source === "demo";
  return (
    <p className={cx("rounded-xl px-3.5 py-2.5 text-sm", demo ? "bg-warn/15 text-warn" : "bg-accent-soft")}>
      {demo ? <><strong>Demo Mode.</strong> This is deterministic sample output built from your facts, not a live model response.</>
        : <>Written by <strong>{source.replace("ollama:", "")}</strong>, an open-weight model running locally through Ollama.</>}
    </p>
  );
}
