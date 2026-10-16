"use client";
import { Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { GenerationJob } from "@/lib/types";

/** The live "your kit is being built" header: your own photo with a scan line, a running clock, and the title as soon as it's written. */
export function BuildingHero({ job, startedAt }: { job: GenerationJob; startedAt: number }) {
  const [now, setNow] = useState(startedAt);
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(t);
  }, []);
  const secs = Math.max(0, Math.round((now - startedAt) / 1000));
  const fast = (job.settings.quality ?? "fast") === "fast";
  const photo = job.product.image_asset_ids[0];
  const title = job.copy_output?.product_title?.trim();
  const hook = job.copy_output?.video_hook?.trim();
  return (
    <div className="flex items-center gap-4 sm:gap-5">
      <div className="relative aspect-[4/5] w-24 shrink-0 overflow-hidden rounded-2xl bg-surface-2 ring-1 ring-border-strong shadow-float sm:w-32">
        {photo && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={api.assetUrl(job.id, photo)} alt="" className="size-full object-cover" />
        )}
        <span className="scan-line absolute inset-x-0 top-0 h-10 bg-gradient-to-b from-transparent via-accent/50 to-transparent" aria-hidden />
        <span className="absolute inset-0 ring-1 ring-inset ring-accent/30" aria-hidden />
      </div>
      <div className="min-w-0 flex-1">
        <p className="eyebrow flex items-center gap-1.5 text-accent-text"><Sparkles className="size-3.5" aria-hidden />{fast ? "Fast mode" : "Best quality"}</p>
        <h1 className="mt-1 text-xl font-semibold tracking-tight sm:text-2xl">Building your kit</h1>
        <p className="mt-1 font-mono text-sm tabular-nums text-muted" aria-live="off">{secs}s<span className="text-muted/70"> · usually {fast ? "about 20 s" : "about a minute"}</span></p>
        {title && <p key={title} className="rise-in mt-2 truncate text-[15px] font-medium" title={title}>{title}</p>}
        {hook && <p key={hook} className="rise-in serif-it mt-0.5 truncate text-[15px] text-accent-text">{hook}</p>}
      </div>
    </div>
  );
}
