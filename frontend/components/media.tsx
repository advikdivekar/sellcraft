"use client";
import { ChevronLeft, ChevronRight, Download, Film, Info, Loader2, Share2 } from "lucide-react";
import { useRef, useState } from "react";
import { api } from "@/lib/api";
import { methodLabel } from "@/lib/options";
import { shareFiles, slug } from "@/lib/share";
import type { GeneratedAsset, GenerationJob } from "@/lib/types";
import { useFeedback } from "./feedback";
import { Badge, Button, Card, Skeleton, cx } from "./ui";

const SLIDE_LABEL: Record<string, string> = { hero: "Hero", benefits: "Benefits", detail: "Close-up", angle: "Another angle", cta: "Call to action" };

export function VideoCard({ job, video, rendering, updating, onUpdate }: {
  job: GenerationJob; video?: GeneratedAsset; rendering: boolean; updating: boolean; onUpdate: () => void;
}) {
  const { toast } = useFeedback();
  const [info, setInfo] = useState(false);
  const url = video ? api.assetUrl(job.id, video.id) : "";
  async function share() {
    const r = await shareFiles([{ url, name: `${slug(job.product.name)}.mp4`, type: "video/mp4" }], { title: job.product.name });
    if (r === "fallback") toast("Opened the video. Use your browser's save option.");
  }
  return (
    <Card pad={false} className="overflow-hidden">
      <div className="flex items-center justify-between gap-2 px-4 pt-4 sm:px-5">
        <h3 className="flex items-center gap-2 font-semibold"><Film className="size-4 text-accent" aria-hidden />Video ad</h3>
        {video && <Badge tone="accent">{video.method === "studio_cutout" ? "Studio-enhanced" : "Animated photo"}</Badge>}
      </div>
      <div className="p-4 sm:p-5">
        <div className="mx-auto aspect-[9/16] w-full max-w-[300px] overflow-hidden rounded-[26px] bg-black shadow-float ring-1 ring-black/10">
          {video ? (
            <video key={video.id} className="size-full object-contain" src={`${url}#t=0.1`} controls playsInline preload="metadata" />
          ) : (
            <div className="grid size-full place-items-center bg-surface-2 p-6 text-center text-sm text-muted">
              {rendering ? <span className="flex flex-col items-center gap-3"><Loader2 className="size-6 animate-spin text-accent" />Rendering your video…</span> : "No video yet. See the message above to retry."}
            </div>
          )}
        </div>
        {video && (
          <>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              <Button size="sm" onClick={share}><Share2 className="size-4" />Share video</Button>
              <a href={url} download={`${slug(job.product.name)}.mp4`} className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-border-strong bg-surface px-3.5 text-sm font-medium shadow-card transition hover:bg-surface-2"><Download className="size-4" />MP4</a>
              <Button variant="secondary" size="sm" busy={updating} onClick={onUpdate}>Update text</Button>
            </div>
            <button type="button" onClick={() => setInfo((v) => !v)} className="mx-auto mt-3 flex min-h-9 items-center gap-1.5 text-xs text-muted hover:text-foreground"><Info className="size-3.5" />How was this made?</button>
            {info && <p className="anim-in mt-1 rounded-xl bg-surface-2 p-3 text-xs text-muted">{methodLabel(video.method)} After editing the hook, feature or CTA, tap <strong>Update text</strong>: it re-renders the words only.</p>}
          </>
        )}
      </div>
    </Card>
  );
}

export function DeckCarousel({ job, slides, building }: { job: GenerationJob; slides: GeneratedAsset[]; building: boolean }) {
  const { toast } = useFeedback();
  const ref = useRef<HTMLUListElement>(null);
  const [idx, setIdx] = useState(0);

  const onScroll = () => {
    const el = ref.current;
    if (!el) return;
    const mid = el.scrollLeft + el.clientWidth / 2;
    let best = 0, bd = Infinity;
    Array.from(el.children).forEach((c, i) => { const d = Math.abs((c as HTMLElement).offsetLeft + (c as HTMLElement).clientWidth / 2 - mid); if (d < bd) { bd = d; best = i; } });
    setIdx(best);
  };
  const goTo = (i: number) => {
    const el = ref.current?.children[Math.max(0, Math.min(slides.length - 1, i))] as HTMLElement | undefined;
    el?.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
  };
  const name = slug(job.product.name);
  async function shareDeck() {
    const r = await shareFiles(slides.map((s, i) => ({ url: api.assetUrl(job.id, s.id), name: `${name}-slide-${i + 1}.jpg`, type: "image/jpeg" })), { title: job.product.name });
    if (r === "fallback") toast("Your browser can't share images directly. Use the zip download instead.");
  }

  return (
    <Card pad={false} className="overflow-hidden">
      <div className="flex items-center justify-between gap-2 px-4 pt-4 sm:px-5">
        <h3 className="font-semibold">Image deck</h3>
        <span className="text-xs text-muted tabular-nums">{slides.length ? `${idx + 1} / ${slides.length}` : ""}</span>
      </div>
      {slides.length === 0 ? (
        <div className="p-4 sm:p-5">{building ? <Skeleton className="mx-auto aspect-[4/5] w-3/4" /> : <p className="text-sm text-muted">No deck yet.</p>}</div>
      ) : (
        <>
          <div className="relative py-4">
            <ul ref={ref} onScroll={onScroll} className="no-scrollbar flex snap-x snap-mandatory gap-3 overflow-x-auto scroll-smooth px-[9%]" aria-label="Image deck slides">
              {slides.map((s, i) => (
                <li key={s.id} className="w-[82%] shrink-0 snap-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={api.assetUrl(job.id, s.id)} alt={`Slide ${i + 1}: ${SLIDE_LABEL[s.method ?? ""] ?? "Slide"}`} loading={i < 2 ? "eager" : "lazy"}
                    className="aspect-[4/5] w-full rounded-2xl border border-border object-cover shadow-float" />
                </li>
              ))}
            </ul>
            <button type="button" aria-label="Previous slide" onClick={() => goTo(idx - 1)} disabled={idx === 0}
              className="absolute left-2 top-1/2 hidden size-10 -translate-y-1/2 place-items-center rounded-full border border-border-strong bg-surface/95 shadow-card transition hover:bg-surface disabled:opacity-0 sm:grid"><ChevronLeft className="size-5" /></button>
            <button type="button" aria-label="Next slide" onClick={() => goTo(idx + 1)} disabled={idx === slides.length - 1}
              className="absolute right-2 top-1/2 hidden size-10 -translate-y-1/2 place-items-center rounded-full border border-border-strong bg-surface/95 shadow-card transition hover:bg-surface disabled:opacity-0 sm:grid"><ChevronRight className="size-5" /></button>
          </div>
          <div className="flex items-center justify-center gap-1.5 pb-1" role="tablist" aria-label="Choose slide">
            {slides.map((s, i) => <button key={s.id} role="tab" aria-selected={i === idx} aria-label={`Go to slide ${i + 1}`} onClick={() => goTo(i)} className="grid size-6 place-items-center"><span className={cx("h-1.5 rounded-full transition-all", i === idx ? "w-5 bg-accent" : "w-1.5 bg-border-strong")} /></button>)}
          </div>
          <p className="px-4 text-center text-sm font-medium">{SLIDE_LABEL[slides[idx]?.method ?? ""] ?? "Slide"}</p>
          <div className="flex flex-wrap justify-center gap-2 p-4 sm:p-5">
            <Button size="sm" onClick={shareDeck}><Share2 className="size-4" />Share deck</Button>
            <a href={api.assetUrl(job.id, slides[idx].id)} download={`${name}-slide-${idx + 1}.jpg`} className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-border-strong bg-surface px-3.5 text-sm font-medium shadow-card transition hover:bg-surface-2"><Download className="size-4" />This slide</a>
          </div>
        </>
      )}
    </Card>
  );
}
