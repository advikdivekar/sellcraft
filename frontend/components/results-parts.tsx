"use client";
import { AlertTriangle, Check, Download, ExternalLink, Info, Share2, Store } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { PLATFORMS, postText } from "@/lib/options";
import { copyText } from "@/lib/image";
import { downloadText, shareFiles, slug } from "@/lib/share";
import type { CopyOutput, GeneratedAsset, GenerationJob, Platform } from "@/lib/types";
import { useFeedback } from "./feedback";
import { Badge, Button, Card, SectionTitle, cx } from "./ui";

export function Insights({ copy, photoNotes, deckNotes }: { copy: CopyOutput; photoNotes: string[]; deckNotes: string[] }) {
  const blocks = [
    { show: copy.missing_information.length > 0, icon: Info, title: "Not provided, so left out of the copy", items: copy.missing_information, hint: "Add these on the Facts step to improve the result." },
    { show: copy.claims_requiring_review.length > 0, icon: AlertTriangle, title: "Double-check before posting", items: copy.claims_requiring_review },
    { show: photoNotes.length + deckNotes.length > 0, icon: Info, title: "About your photos", items: [...photoNotes, ...deckNotes] },
  ].filter((b) => b.show);
  if (blocks.length === 0) return null;
  return (
    <Card className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
      {blocks.map(({ icon: Icon, title, items, hint }) => (
        <div key={title}>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold"><Icon className="size-4 text-warn" aria-hidden />{title}</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted">{items.map((c) => <li key={c}>{c}</li>)}</ul>
          {hint && <p className="mt-2 text-xs text-muted">{hint}</p>}
        </div>
      ))}
    </Card>
  );
}

export function PhotoGroup({ title, blurb, kind, assets, jobId, name, ext, checker }: {
  title: string; blurb: string; kind: string; assets: GeneratedAsset[]; jobId: string; name: string; ext: string; checker?: boolean;
}) {
  if (assets.length === 0) return null;
  return (
    <section className="space-y-3">
      <div><h3 className="font-semibold">{title}</h3><p className="text-sm text-muted">{blurb}</p></div>
      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {assets.map((a, i) => (
          <li key={a.id} className="space-y-1.5">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={api.assetUrl(jobId, a.id)} alt={`${kind} ${i + 1}`} loading="lazy"
              className={cx("w-full rounded-xl border border-border object-cover shadow-card", checker && "bg-[conic-gradient(#d9d4ca_25%,#fff_0_50%,#d9d4ca_0_75%,#fff_0)] bg-[length:16px_16px]")} />
            <a href={api.assetUrl(jobId, a.id)} download={`${name}-${slug(title)}-${i + 1}.${ext}`} className="inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-accent-text"><Download className="size-4" />Download</a>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function SharePanel({ job, copy, platforms, video, slides, shopifyConfigured, shopifyStore, onPublish, publishing, published, asText }: {
  job: GenerationJob; copy: CopyOutput; platforms: Platform[]; video?: GeneratedAsset; slides: GeneratedAsset[];
  shopifyConfigured: boolean; shopifyStore?: string | null; onPublish: () => void; publishing: boolean;
  published?: { admin_url: string; media_attached: number }; asText: string;
}) {
  const { toast, confirm } = useFeedback();
  const [openPlat, setOpenPlat] = useState<Platform | null>(null);
  const name = slug(job.product.name);

  async function shareKit(p: Platform) {
    const text = postText(p, copy);
    await copyText(text);
    toast("Caption copied. Paste it in your post.");
    const files = [
      ...(video ? [{ url: api.assetUrl(job.id, video.id), name: `${name}.mp4`, type: "video/mp4" }] : []),
    ];
    if (files.length) await shareFiles(files, { text, title: job.product.name });
  }
  async function publish() {
    const ok = await confirm({ title: "Send to Shopify as a draft?", body: `A draft product is created in ${shopifyStore ?? "your store"} with your photos, video and copy. Nothing goes live until you publish it in Shopify.`, confirmLabel: "Create draft" });
    if (ok) onPublish();
  }

  return (
    <div className="space-y-5">
      <Card className="space-y-4">
        <SectionTitle hint="Pick where you'll post. We copy the caption and open your phone's share sheet with the video.">Post to a platform</SectionTitle>
        <ul className="divide-y divide-border">
          {platforms.map((p) => {
            const label = PLATFORMS.find((x) => x.value === p)!.label;
            return (
              <li key={p} className="py-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <button type="button" onClick={() => setOpenPlat(openPlat === p ? null : p)} aria-expanded={openPlat === p} className="min-h-11 text-left font-medium">{label}<span className="ml-2 text-xs font-normal text-muted">{openPlat === p ? "Hide post" : "Preview post"}</span></button>
                  <div className="flex gap-2">
                    <Button variant="secondary" size="sm" onClick={async () => { await copyText(postText(p, copy)); toast(`${label} post copied`); }}>Copy post</Button>
                    {video && <Button size="sm" onClick={() => shareKit(p)}><Share2 className="size-4" />Share</Button>}
                  </div>
                </div>
                {openPlat === p && <pre className="anim-in mt-2 max-h-56 overflow-auto whitespace-pre-wrap rounded-xl bg-surface-2 p-3 font-sans text-sm text-muted">{postText(p, copy)}</pre>}
              </li>
            );
          })}
        </ul>
      </Card>

      <Card className="space-y-3">
        <SectionTitle hint="Everything in one file: video, deck, photos and the listing text.">Download</SectionTitle>
        <div className="flex flex-wrap gap-2">
          <a href={api.kitUrl(job.id)} download className="inline-flex min-h-12 items-center gap-2 rounded-xl bg-accent px-5 text-[15px] font-medium text-accent-fg shadow-card transition hover:brightness-110"><Download className="size-4" />Download kit (.zip)</a>
          <Button variant="secondary" onClick={async () => { await copyText(asText); toast("Everything copied"); }}>Copy all text</Button>
          <Button variant="secondary" onClick={() => downloadText(`${name}-listing.txt`, asText)}>Listing .txt</Button>
          <Button variant="secondary" onClick={() => downloadText(`${name}-listing.json`, JSON.stringify(copy, null, 2), "application/json")}>Listing .json</Button>
          {slides.length > 0 && <Button variant="secondary" onClick={async () => { await shareFiles(slides.map((s, i) => ({ url: api.assetUrl(job.id, s.id), name: `${name}-slide-${i + 1}.jpg`, type: "image/jpeg" })), { title: job.product.name }); }}><Share2 className="size-4" />Share deck</Button>}
        </div>
      </Card>

      <Card className="space-y-3">
        <SectionTitle hint="Creates a draft product. You review and publish it in Shopify.">Your store</SectionTitle>
        <div className="flex items-center gap-3"><Store className="size-5 text-accent-text" aria-hidden /><span className="font-medium">Shopify</span>{shopifyConfigured && <Badge tone="ok">Connected</Badge>}</div>
        {shopifyConfigured ? (
          published
            ? <p className="text-sm"><Check className="mr-1 inline size-4 text-ok" />Draft created with {published.media_attached} media. <a className="inline-flex items-center gap-1 font-medium text-accent-text underline" href={published.admin_url} target="_blank" rel="noreferrer">Open in Shopify<ExternalLink className="size-3.5" /></a></p>
            : <Button variant="secondary" busy={publishing} onClick={publish}>Send to Shopify as draft</Button>
        ) : (
          <p className="text-sm text-muted">Not connected. <Link href="/connections" className="font-medium text-accent-text underline">Connect your Shopify store</Link> to send this kit to it in one tap.</p>
        )}
      </Card>
    </div>
  );
}
