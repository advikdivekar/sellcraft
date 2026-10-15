"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Check, Download, ExternalLink, Film, Info, Loader2, Share2, Sparkles, Store } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { LISTING_SECTIONS, PLATFORMS, PLATFORM_FIELD_LABELS, SOCIAL_SECTIONS, TONES, VIDEO_SECTIONS, methodLabel, postText, type SectionDef } from "@/lib/options";
import { copyText } from "@/lib/image";
import { ApiError, api } from "@/lib/api";
import type { CopyOutput, GenerationJob, Platform, Tone } from "@/lib/types";
import { EditableField } from "./editable-field";
import { Button, Card, Chips, cx } from "./ui";

type Tab = "listing" | "social" | "video" | "photos" | Platform;

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
  const [copiedPost, setCopiedPost] = useState(false);
  const status = useQuery({ queryKey: ["status"], queryFn: api.status });
  const locked = job.stages.some((s) => s.name === "copy" && s.status === "running");
  const studio = job.assets.filter((a) => a.kind === "studio_image");
  const catalog = job.assets.filter((a) => a.kind === "catalog_image");
  const cutouts = job.assets.filter((a) => a.kind === "cutout_image");
  const photoNotes = job.stages.find((x) => x.name === "video")?.notes ?? [];
  const hasPhotos = studio.length + catalog.length + cutouts.length > 0;
  const shopify = useMutation({
    mutationFn: () => api.publishShopify(job.id),
    onError: (e) => setErr(e instanceof ApiError ? e.message : "Couldn't send to Shopify."),
  });

  const update = (j: GenerationJob) => qc.setQueryData(["job", job.id], j);
  const onError = (e: unknown) => setErr(e instanceof ApiError ? e.message : "Something went wrong.");

  const reassemble = useMutation({ mutationFn: () => api.reassemble(job.id), onSuccess: update, onError });
  const rendering = job.status === "generating_video" || job.status === "assembling_video";
  const videoUrl = (id: string) => api.assetUrl(job.id, id);
  async function shareVideo(id: string) {
    try {
      const blob = await (await fetch(videoUrl(id))).blob();
      const file = new File([blob], `${slug(job.product.name)}.mp4`, { type: "video/mp4" });
      if (navigator.canShare?.({ files: [file] })) await navigator.share({ files: [file], title: job.product.name });
      else window.open(videoUrl(id), "_blank");
    } catch (e) {
      if ((e as Error).name !== "AbortError") setErr("Couldn't open the share sheet. Use the Download link instead.");
    }
  }

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
      onCommit={setCore(s.key)} onRegenerate={() => regen.mutate({ section: s.key })} busy={busyKey === s.key} locked={locked} />
  );

  const tabs: { id: Tab; label: string }[] = [
    { id: "listing", label: "Listing" }, { id: "social", label: "Social" },
    ...platforms.map((p) => ({ id: p as Tab, label: PLATFORMS.find((x) => x.value === p)!.label })),
    { id: "video", label: "Video" },
    ...(hasPhotos ? [{ id: "photos" as Tab, label: "Photos" }] : []),
  ];

  async function shareKit() {
    const caption = postText(platforms[0], copy);
    await copyText(caption);
    if (!video) return;
    try {
      const blob = await (await fetch(videoUrl(video.id))).blob();
      const file = new File([blob], `${slug(job.product.name)}.mp4`, { type: "video/mp4" });
      if (navigator.canShare?.({ files: [file] })) await navigator.share({ files: [file], text: caption, title: job.product.name });
      else window.open(videoUrl(video.id), "_blank");
    } catch (e) {
      if ((e as Error).name !== "AbortError") setErr("Couldn't open the share sheet. Use Download everything instead.");
    }
  }

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
        <Button variant="secondary" busy={busyKey === "__all"} disabled={locked} onClick={() => regen.mutate({ tone })}>
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
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" onClick={async () => { if (await copyText(postText(tab as Platform, copy))) { setCopiedPost(true); setTimeout(() => setCopiedPost(false), 1500); } }}>
                  {copiedPost ? <Check className="size-4 text-ok" /> : <Share2 className="size-4" />}{copiedPost ? "Copied" : "Copy post"}
                </Button>
                {!locked && <Button variant="secondary" size="sm" busy={busyKey === `platform:${tab}`} onClick={() => regen.mutate({ section: `platform:${tab}` })}>Regenerate all</Button>}
              </div>
            </div>
            {PLATFORM_FIELD_LABELS[tab as Platform].map((f) => (
              <EditableField key={f.key} label={f.label} kind={f.kind} rows={f.rows} value={copy.platform_outputs[tab]?.[f.key]} onCommit={setPlat(tab as Platform, f.key)} locked={locked} />
            ))}
          </>
        )}
        {tab === "photos" && (
          <>
            {photoNotes.length > 0 && (
              <div className="rounded-xl border border-warn/50 bg-warn/10 p-3 text-sm">
                <p className="mb-1 flex items-center gap-2 font-medium"><Info className="size-4 text-warn" />What we noticed in your photos</p>
                <ul className="list-disc space-y-0.5 pl-5 text-muted">{photoNotes.map((n) => <li key={n}>{n}</li>)}</ul>
              </div>
            )}
            <PhotoGroup title="Studio photos" blurb="Cleaned product on a designed backdrop, in the 4:5 feed shape." kind="Studio photo" assets={studio} jobId={job.id} name={slug(job.product.name)} ext="jpg" />
            <PhotoGroup title="White background" blurb="Pure white, centred: the style marketplaces like Etsy, Amazon and Shopify expect." kind="White background photo" assets={catalog} jobId={job.id} name={slug(job.product.name)} ext="jpg" />
            <PhotoGroup title="Transparent cut-outs" blurb="PNG with the background removed, for your own designs." kind="Cut-out" assets={cutouts} jobId={job.id} name={slug(job.product.name)} ext="png" checker />
          </>
        )}
        {tab === "video" && (
          <>
            <div className="rounded-xl border border-border bg-background p-4">
              {video ? (
                <>
                  <video key={video.id} className="mx-auto max-h-[70dvh] rounded-lg" src={`${videoUrl(video.id)}#t=0.1`} controls playsInline preload="metadata" />
                  <p className="mt-2 text-center text-xs text-muted">
                    {methodLabel(video.method)}
                    {video.duration_seconds ? ` ${video.duration_seconds.toFixed(0)}s, vertical 9:16.` : ""}
                  </p>
                  <div className="mt-3 flex flex-wrap justify-center gap-2">
                    <Button variant="secondary" size="sm" onClick={() => shareVideo(video.id)}><Share2 className="size-4" />Save / Share</Button>
                    <Button variant="secondary" size="sm" busy={reassemble.isPending || job.status === "assembling_video"} onClick={() => reassemble.mutate()}>
                      <Film className="size-4" />Update video text
                    </Button>
                  </div>
                  <p className="mt-2 text-center text-xs text-muted">Edited the hook, feature or CTA? Update video text re-renders the words only. The motion isn&apos;t re-made.</p>
                </>
              ) : rendering ? (
                <p className="flex items-center justify-center gap-2 py-6 text-sm text-muted"><Loader2 className="size-4 animate-spin" />Rendering your video…</p>
              ) : (
                <p className="text-sm text-muted">No video yet. See the message above to retry.</p>
              )}
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

      <Card className="space-y-3">
        <h3 className="font-medium">Share &amp; publish</h3>
        <div className="flex flex-wrap gap-2">
          {video && (
            <Button size="sm" onClick={() => shareKit()}><Share2 className="size-4" />Share video + caption</Button>
          )}
          <a className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-border bg-surface px-3.5 text-sm hover:bg-accent-soft" href={api.kitUrl(job.id)} download>
            <Download className="size-4" />Download everything (.zip)
          </a>
          <Button variant="secondary" size="sm" onClick={() => copyText(asText(copy, platforms))}>Copy everything</Button>
          <Button variant="secondary" size="sm" onClick={() => download(`${slug(job.product.name)}-listing.txt`, asText(copy, platforms), "text/plain")}>Listing .txt</Button>
        </div>
        <p className="text-xs text-muted">Share opens your phone&apos;s share sheet with the video and your caption, so you can post to Instagram, WhatsApp, Facebook and more in a tap. The caption is also copied.</p>
        <div className="rounded-xl border border-border p-3">
          <p className="mb-2 flex items-center gap-2 text-sm font-medium"><Store className="size-4" />Shopify</p>
          {status.data?.shopify.configured ? (
            shopify.data ? (
              <p className="text-sm"><Check className="mr-1 inline size-4 text-ok" />Draft created with {shopify.data.media_attached} media. <a className="inline-flex items-center gap-1 text-accent underline" href={shopify.data.admin_url} target="_blank" rel="noreferrer">Open in Shopify<ExternalLink className="size-3.5" /></a></p>
            ) : (
              <Button variant="secondary" size="sm" busy={shopify.isPending} onClick={() => { if (window.confirm(`Create a DRAFT product in ${status.data?.shopify.store}? Nothing goes live until you publish it in Shopify.`)) shopify.mutate(); }}>
                Send to Shopify as draft
              </Button>
            )
          ) : (
            <p className="text-sm text-muted">Not connected. <Link href="/connections" className="text-accent underline">Connect your Shopify store</Link> to send this kit to it as a draft in one tap.</p>
          )}
        </div>
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

function PhotoGroup({ title, blurb, kind, assets, jobId, name, ext, checker }: {
  title: string; blurb: string; kind: string; assets: { id: string }[]; jobId: string; name: string; ext: string; checker?: boolean;
}) {
  if (assets.length === 0) return null;
  return (
    <section className="space-y-2">
      <div><h4 className="font-medium">{title}</h4><p className="text-xs text-muted">{blurb}</p></div>
      <ul className="grid grid-cols-2 gap-3">
        {assets.map((a, i) => (
          <li key={a.id} className="space-y-1">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={api.assetUrl(jobId, a.id)} alt={`${kind} ${i + 1}`} loading="lazy"
              className={cx("w-full rounded-xl border border-border", checker && "bg-[conic-gradient(#d4d0c8_25%,#fff_0_50%,#d4d0c8_0_75%,#fff_0)] bg-[length:16px_16px]")} />
            <a href={api.assetUrl(jobId, a.id)} download={`${name}-${title.toLowerCase().replace(/\W+/g, "-")}-${i + 1}.${ext}`}
              className="inline-flex min-h-11 items-center gap-1.5 text-sm text-accent"><Download className="size-4" />Download</a>
          </li>
        ))}
      </ul>
    </section>
  );
}
