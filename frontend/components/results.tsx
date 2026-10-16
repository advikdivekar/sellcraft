"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Download, Loader2, Share2, Sparkles } from "lucide-react";
import { useState } from "react";
import { ApiError, api } from "@/lib/api";
import { copyText } from "@/lib/image";
import { LISTING_SECTIONS, PLATFORMS, PLATFORM_FIELD_LABELS, SOCIAL_SECTIONS, TONES, VIDEO_SECTIONS, postText, type SectionDef } from "@/lib/options";
import { shareFiles, slug } from "@/lib/share";
import type { CopyOutput, GenerationJob, Platform, Tone } from "@/lib/types";
import { EditableField } from "./editable-field";
import { useFeedback } from "./feedback";
import { DeckCarousel, VideoCard } from "./media";
import { Insights, PhotoGroup, SharePanel } from "./results-parts";
import { Badge, Button, Card, Chips, Sheet, Tabs, buttonClass, cx } from "./ui";

type Main = "overview" | "copy" | "photos" | "share";
type Sub = "listing" | "social" | "video" | Platform;

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
  const { toast } = useFeedback();
  const copy = job.copy_output!;
  const platforms = job.settings.platforms;
  const [main, setMain] = useState<Main>("overview");
  const [sub, setSub] = useState<Sub>("listing");
  const [tone, setTone] = useState<Tone>(job.settings.tone);
  const [showTone, setShowTone] = useState(false);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [savedOnce, setSavedOnce] = useState(false);
  const status = useQuery({ queryKey: ["status"], queryFn: api.status });

  const stage = (n: string) => job.stages.find((s) => s.name === n);
  const locked = stage("copy")?.status === "running";
  const rendering = job.status === "generating_video" || job.status === "assembling_video" || stage("video")?.status === "running" || stage("assembly")?.status === "running";
  const video = job.assets.find((a) => a.kind === "video");
  const slides = job.assets.filter((a) => a.kind === "deck_slide");
  const studio = job.assets.filter((a) => a.kind === "studio_image");
  const catalog = job.assets.filter((a) => a.kind === "catalog_image");
  const cutouts = job.assets.filter((a) => a.kind === "cutout_image");
  const photoCount = studio.length + catalog.length + cutouts.length;
  const name = slug(job.product.name);

  const update = (j: GenerationJob) => qc.setQueryData(["job", job.id], j);
  const onError = (e: unknown) => toast(e instanceof ApiError ? e.message : "Something went wrong.", "error");

  const save = useMutation({ mutationFn: (c: CopyOutput) => api.saveCopy(job.id, c), onSuccess: (j) => { update(j); setSavedOnce(true); }, onError });
  const regen = useMutation({
    mutationFn: (v: { section?: string; tone?: Tone }) => api.regenerate(job.id, { section: v.section ?? null, tone: v.tone ?? null }),
    onMutate: (v) => setBusyKey(v.section ?? "__all"),
    onSuccess: (j) => { update(j); toast("Rewritten"); }, onError, onSettled: () => setBusyKey(null),
  });
  const reassemble = useMutation({ mutationFn: () => api.reassemble(job.id), onSuccess: (j) => { update(j); toast("Updating your video and deck…"); }, onError });
  const shopify = useMutation({ mutationFn: () => api.publishShopify(job.id), onError });

  const setCore = (key: string) => (v: string | string[]) => save.mutate({ ...copy, [key]: v } as CopyOutput);
  const setPlat = (p: Platform, key: string) => (v: string | string[]) =>
    save.mutate({ ...copy, platform_outputs: { ...copy.platform_outputs, [p]: { ...copy.platform_outputs[p], [key]: v } } });
  const core = (s: SectionDef) => (
    <EditableField key={s.key} label={s.label} kind={s.kind} rows={s.rows} value={copy[s.key as keyof CopyOutput] as string | string[]}
      onCommit={setCore(s.key)} onRegenerate={() => regen.mutate({ section: s.key })} busy={busyKey === s.key} locked={locked} />
  );

  async function shareAll() {
    const files = video ? [{ url: api.assetUrl(job.id, video.id), name: `${name}.mp4`, type: "video/mp4" }] : [];
    const text = postText(platforms[0], copy);
    await copyText(text);
    toast("Caption copied. Paste it in your post.");
    if (files.length) await shareFiles(files, { text, title: job.product.name });
  }

  const subTabs = [{ id: "listing" as Sub, label: "Listing" }, { id: "social" as Sub, label: "Social" },
    ...platforms.map((p) => ({ id: p as Sub, label: PLATFORMS.find((x) => x.value === p)!.label })), { id: "video" as Sub, label: "Video brief" }];
  const words = copy.voiceover_script.trim().split(/\s+/).filter(Boolean).length;
  const secs = Math.round((words / 2.5) * 10) / 10;
  const mainTabs = [{ id: "overview" as Main, label: "Overview" }, { id: "copy" as Main, label: "Copy" },
    ...(photoCount ? [{ id: "photos" as Main, label: "Photos", badge: photoCount }] : []), { id: "share" as Main, label: "Share" }];

  return (
    <div className="space-y-6 max-sm:pb-24">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 space-y-2">
          <h1 className="truncate text-[1.7rem] font-semibold sm:text-3xl">{job.product.name}</h1>
          <div className="flex flex-wrap items-center gap-2">
            {platforms.map((p) => <Badge key={p} tone="accent">{PLATFORMS.find((x) => x.value === p)!.label}</Badge>)}
            <Badge>{TONES.find((t) => t.value === job.settings.tone)?.label}</Badge>
            <SourceChip source={job.copy_source} />
            <span className="inline-flex items-center gap-1 text-xs text-muted" aria-live="polite">
              {save.isPending ? <><Loader2 className="size-3 animate-spin" />Saving…</> : savedOnce ? <><Check className="size-3 text-ok" />All changes saved</> : null}
            </span>
          </div>
          <p className="text-[13px] text-muted">{[slides.length ? `${slides.length} slides` : "", photoCount ? `${photoCount} studio photos` : "", video ? "10 s video" : "", `copy for ${platforms.length} platform${platforms.length > 1 ? "s" : ""}`].filter(Boolean).join(" · ")}</p>
        </div>
        <div className="flex gap-2 max-sm:hidden">
          {video && <Button onClick={shareAll}><Share2 className="size-4" />Share</Button>}
          <a href={api.kitUrl(job.id)} download className={buttonClass("secondary")}><Download className="size-4" />Download kit</a>
        </div>
      </header>

      <div className="sticky top-[calc(3.25rem+env(safe-area-inset-top))] z-20 -mx-4 bg-glass px-4 py-2 backdrop-blur-xl backdrop-saturate-150 sm:static sm:mx-0 sm:bg-transparent sm:p-0 sm:backdrop-blur-none"><Tabs variant="segment" label="Kit sections" tabs={mainTabs} value={main} onChange={setMain} /></div>

      <div key={main} className="anim-in">
        {main === "overview" && (
          <div className="space-y-5">
            <div className="grid gap-5 lg:grid-cols-[minmax(0,380px)_1fr]">
              <VideoCard job={job} video={video} rendering={rendering} updating={reassemble.isPending || job.status === "assembling_video"} onUpdate={() => reassemble.mutate()} />
              <DeckCarousel job={job} slides={slides} building={stage("deck")?.status === "running" || rendering || !stage("deck")} />
            </div>
            <Insights jobId={job.id} copy={copy} photoNotes={stage("video")?.notes ?? []} deckNotes={stage("deck")?.notes ?? []} />
          </div>
        )}

        {main === "copy" && (
          <div className="space-y-5">
            <Card className="flex items-center justify-between gap-3">
              <div><p className="eyebrow">Writing tone</p><p className="font-medium">{TONES.find((t) => t.value === job.settings.tone)?.label}</p></div>
              <Button variant="secondary" size="sm" onClick={() => setShowTone(true)}>Change tone</Button>
            </Card>
            <Sheet open={showTone} onClose={() => setShowTone(false)} title="Rewrite in another tone">
              <div className="space-y-4">
                <p className="text-sm text-muted">Rewrites all your copy. Your facts and the video stay the same. This replaces your manual edits to the copy.</p>
                <Chips label="Tone" options={TONES} value={tone} onChange={setTone} />
                <Button className="w-full" size="lg" busy={busyKey === "__all"} disabled={locked} onClick={async () => { await regen.mutateAsync({ tone }).catch(() => {}); setShowTone(false); }}><Sparkles className="size-4" />Rewrite copy</Button>
              </div>
            </Sheet>
            <Tabs label="Copy sections" tabs={subTabs} value={sub} onChange={setSub} />
            <Card bleed className="space-y-5">
              {sub === "listing" && LISTING_SECTIONS.map(core)}
              {sub === "social" && SOCIAL_SECTIONS.map(core)}
              {platforms.includes(sub as Platform) && (
                <>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="font-semibold">{PLATFORMS.find((x) => x.value === sub)!.label}</h3>
                    <div className="flex gap-2">
                      <Button variant="secondary" size="sm" onClick={async () => { if (await copyText(postText(sub as Platform, copy))) toast("Post copied"); }}><Share2 className="size-4" />Copy post</Button>
                      {!locked && <Button variant="secondary" size="sm" busy={busyKey === `platform:${sub}`} onClick={() => regen.mutate({ section: `platform:${sub}` })}>Regenerate all</Button>}
                    </div>
                  </div>
                  {PLATFORM_FIELD_LABELS[sub as Platform].map((f) => (
                    <EditableField key={f.key} label={f.label} kind={f.kind} rows={f.rows} value={copy.platform_outputs[sub]?.[f.key]} onCommit={setPlat(sub as Platform, f.key)} locked={locked} />
                  ))}
                </>
              )}
              {sub === "video" && (
                <>
                  {VIDEO_SECTIONS.map(core)}
                  <p className={cx("-mt-3 text-xs", secs > 10 ? "font-medium text-danger" : "text-muted")}>Voiceover: {words} words, about {secs}s spoken{secs > 10 ? ". Too long for a 10-second ad, so please shorten it." : "."}</p>
                  <div>
                    <h4 className="mb-2 text-sm font-semibold">Storyboard</h4>
                    <ol className="space-y-2">{copy.video_storyboard.map((b, i) => (
                      <li key={i} className="rounded-xl border border-border bg-surface-2 p-3 text-sm">
                        <span className="font-semibold text-accent-text">{b.time}</span> {b.visual}
                        {b.on_screen_text && <span className="mt-0.5 block text-muted">On screen: &ldquo;{b.on_screen_text}&rdquo;</span>}
                      </li>))}</ol>
                  </div>
                  <p className="text-xs text-muted">Edited the hook or CTA? Open <strong>Overview</strong> and tap <strong>Update text</strong> to re-render the video and deck.</p>
                </>
              )}
            </Card>
          </div>
        )}

        {main === "photos" && (
          <Card className="space-y-8">
            <PhotoGroup title="Studio photos" blurb="Your refined product on a designed backdrop, in the 4:5 feed shape." kind="Studio photo" assets={studio} jobId={job.id} name={name} ext="jpg" />
            <PhotoGroup title="White background" blurb="Pure white and centred: the style marketplaces like Etsy, Amazon and Shopify expect." kind="White background photo" assets={catalog} jobId={job.id} name={name} ext="jpg" />
            <PhotoGroup title="Transparent cut-outs" blurb="PNG with the background removed, for your own designs." kind="Cut-out" assets={cutouts} jobId={job.id} name={name} ext="png" checker />
          </Card>
        )}

        {main === "share" && (
          <SharePanel job={job} copy={copy} platforms={platforms} video={video} slides={slides}
            shopifyConfigured={!!status.data?.shopify.configured} shopifyStore={status.data?.shopify.store}
            onPublish={() => shopify.mutate()} publishing={shopify.isPending} published={shopify.data} asText={asText(copy, platforms)} />
        )}
      </div>
      {video && (
        <div className="pb-safe fixed inset-x-0 bottom-0 z-20 border-t border-border/70 bg-glass px-4 pt-3 backdrop-blur-xl backdrop-saturate-150 sm:hidden">
          <div className="mx-auto flex max-w-xl gap-2">
            <Button className="flex-1" size="lg" onClick={shareAll}><Share2 className="size-5" />Share</Button>
            <a href={api.kitUrl(job.id)} download className={buttonClass("secondary", "lg")} aria-label="Download kit"><Download className="size-5" /></a>
          </div>
        </div>
      )}
    </div>
  );
}

function SourceChip({ source }: { source: string | null }) {
  if (!source) return null;
  return source === "demo"
    ? <Badge tone="warn">Demo Mode: sample output, not a live model</Badge>
    : <Badge>{source.replace("ollama:", "")} · local</Badge>;
}