"use client";
import { Check, Copy } from "lucide-react";
import type { Kit } from "./demo";
import { SampleProduct } from "./sample-product";

/** Small output "panels" used by the hero, the transformation and the package. They show real generated sample copy. */
export function ListingPanel({ kit }: { kit: Kit }) {
  return (
    <div className="panel p-3.5 text-left">
      <p className="label muted">Listing · SEO title</p>
      <p className="mt-1.5 text-[1.05em] font-medium leading-snug">{kit.title}</p>
      <p className="desc mt-1.5 line-clamp-2 text-[.82em] leading-snug muted">{kit.description}</p>
    </div>
  );
}
export function CaptionPanel({ kit }: { kit: Kit }) {
  return (
    <div className="panel p-3.5 text-left">
      <p className="label muted">Instagram caption</p>
      <p className="mt-1.5 line-clamp-3 text-[.9em] leading-snug">{kit.caption}</p>
      <p className="desc mt-1.5 text-[.78em] text-[var(--lime)]">{kit.hashtags.slice(0, 3).join(" ")}</p>
    </div>
  );
}
export function TagsPanel({ kit, max = 7 }: { kit: Kit; max?: number }) {
  return (
    <div className="panel p-3.5 text-left">
      <p className="label muted">Search tags</p>
      <div className="mt-2 flex flex-wrap gap-1.5">{kit.tags.slice(0, max).map((t) => <span key={t} className="chip !min-h-0 py-[3px] text-[.8em]">{t}</span>)}</div>
    </div>
  );
}
export function StoryboardPanel({ kit }: { kit: Kit }) {
  return (
    <div className="panel p-3.5 text-left">
      <p className="label muted">Video ad · 10 s concept</p>
      <div className="mt-2 flex gap-1" aria-hidden>{kit.beats.map((b, i) => <span key={b.label} className={`h-1.5 rounded-full ${i === 3 ? "bg-[var(--lime)]" : "bg-white/35"}`} style={{ flex: [2, 3, 3, 2][i] }} />)}</div>
      <p className="mt-2 text-[.82em] leading-snug">{kit.beats.map((b) => b.label).join(" · ")}</p>
    </div>
  );
}
export function PinPanel({ kit }: { kit: Kit }) {
  return (
    <div className="panel flex gap-3 p-3 text-left">
      <div className="w-[34%] shrink-0 overflow-hidden rounded-lg"><SampleProduct id="pin" className="aspect-[3/4] w-full" /></div>
      <div className="min-w-0"><p className="label muted">Pinterest pin</p><p className="mt-1 text-[.9em] font-medium leading-snug">{kit.title}</p><p className="mt-1 text-[.76em] text-[var(--lime)]">Save for later</p></div>
    </div>
  );
}

export function CopyButton({ id, text, done, onCopy, light, label = "Copy" }: { id: string; text: string; done: string | null; onCopy: (id: string, t: string) => void; light?: boolean; label?: string }) {
  const ok = done === id;
  return (
    <button type="button" onClick={() => onCopy(id, text)} aria-label={`${label} ${id}`}
      className={`inline-flex min-h-11 min-w-11 items-center justify-center gap-1.5 rounded-full px-3 text-[13px] transition ${light ? "hover:bg-black/5" : "hover:bg-white/10"}`}>
      {ok ? <Check className="size-4 tick anim-copied" aria-hidden /> : <Copy className="size-4" aria-hidden />}
      <span aria-live="polite">{ok ? "Copied" : label}</span>
    </button>
  );
}
