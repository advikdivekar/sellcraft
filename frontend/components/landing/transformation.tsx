"use client";
import { useMemo } from "react";
import { CaptionPanel, ListingPanel, PinPanel, StoryboardPanel, TagsPanel } from "./parts";
import { generate, SAMPLE } from "./demo";
import { ease, seg, useMounted, useReducedMotion, useScrollProgress } from "./hooks";
import { SampleProduct } from "./sample-product";

const PLATS = ["Instagram", "Etsy", "Shopify"] as const;

/** Scroll-linked camera sequence. Scroll position drives everything through CSS variables (no per-frame React work):
 *  A push in on the photo · B it becomes a listing · C pull back to the whole package · D hand off to the next section. */
export function Transformation() {
  const reduced = useReducedMotion();
  const mounted = useMounted();
  const kit = useMemo(() => generate(SAMPLE.name, SAMPLE.details, "instagram", "luxury"), []);
  const etsy = useMemo(() => generate(SAMPLE.name, SAMPLE.details, "etsy", "luxury"), []);
  const enhanced = mounted && !reduced;

  const ref = useScrollProgress<HTMLElement>((p, el) => {
    const set = (k: string, v: number) => el.style.setProperty(k, v.toFixed(4));
    set("--wa", ease(seg(p, 0.02, 0.26))); set("--wb", ease(seg(p, 0.28, 0.4))); set("--wc", ease(seg(p, 0.64, 0.88))); set("--wd", ease(seg(p, 0.92, 1)));
    const b = seg(p, 0.36, 0.6);
    set("--k-title", seg(b, 0, 0.28)); set("--k-1", seg(b, 0.25, 0.5)); set("--k-2", seg(b, 0.45, 0.7)); set("--k-3", seg(b, 0.65, 0.9)); set("--k-tags", seg(b, 0.8, 1));
    const stage = el.querySelector<HTMLElement>(".tf-stage");
    if (stage) {
      stage.dataset.ph = p < 0.28 ? "a" : p < 0.64 ? "b" : "c";
      const plat = p < 0.44 ? "0" : p < 0.54 ? "1" : "2";
      if (stage.dataset.plat !== plat) stage.dataset.plat = plat;
      stage.querySelectorAll<HTMLElement>(".tf-stat").forEach((s, i) => s.classList.toggle("on", b > [0.02, 0.22, 0.5][i]));
    }
  }, enhanced);

  if (!enhanced) return <TransformStatic kit={kit} />;
  return (
    <section ref={ref} className="tf" id="transformation" aria-label="How one photo becomes a marketing package">
      <div className="tf-stage" data-ph="a" data-plat="0">
        <div className="tf-bar" aria-hidden />
        <div className="tf-caption">
          <div className="c-a"><p className="label tick">01 · Your photo</p><p className="tf-cap">Start with the photo you already have.</p></div>
          <div className="c-b"><p className="label tick">02 · A few facts</p><p className="tf-cap">Facts become a listing, written for the platform.</p></div>
          <div className="c-c"><p className="label tick">03 · The whole package</p><p className="tf-cap">One input. Every deliverable.</p></div>
        </div>

        <div className="tf-out" style={{ left: "4%", top: "26%", ["--ox" as string]: "-30vw", ["--oy" as string]: "-8vh", ["--fd" as string]: "0s", fontSize: 12 }} aria-hidden><ListingPanel kit={kit} /></div>
        <div className="tf-out" style={{ right: "4%", top: "30%", ["--ox" as string]: "30vw", ["--oy" as string]: "-6vh", ["--fd" as string]: "-2s", fontSize: 12 }} aria-hidden><CaptionPanel kit={kit} /></div>
        <div className="tf-out" style={{ left: "6%", bottom: "12%", ["--ox" as string]: "-30vw", ["--oy" as string]: "10vh", ["--fd" as string]: "-4s", fontSize: 12 }} aria-hidden><TagsPanel kit={kit} /></div>
        <div className="tf-out" style={{ right: "6%", bottom: "10%", ["--ox" as string]: "30vw", ["--oy" as string]: "10vh", ["--fd" as string]: "-1s", fontSize: 12 }} aria-hidden><StoryboardPanel kit={kit} /></div>

        <div className="tf-ph"><SampleProduct id="tf" className="h-full w-full" /><span className="label absolute left-2 top-2 rounded-full bg-black/60 px-2 py-1 text-[9px] text-white backdrop-blur">Sample photo</span></div>

        <div className="tf-list" aria-hidden={false}>
          <div className="panel">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex gap-1.5" role="group" aria-label="Platform preview">
                {PLATS.map((p, i) => <span key={p} className={`chip pl-${i} text-[12px] transition`}>{p}</span>)}
              </div>
              <span className="label muted">Illustration of the flow</span>
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1"><span className="tf-stat"><i />Reading photo</span><span className="tf-stat"><i />Using your facts</span><span className="tf-stat"><i />Drafting copy</span></div>
            <p className="tf-type text-[clamp(1.05rem,2.4vw,1.5rem)] font-medium leading-tight" style={{ ["--k" as string]: "var(--k-title)" }}>{etsy.title}</p>
            <div className="space-y-1.5 text-[13px] leading-snug muted">
              <p className="tf-line" style={{ ["--k" as string]: "var(--k-1)" }}>{kit.description.split(". ")[0]}.</p>
              <p className="tf-line" style={{ ["--k" as string]: "var(--k-2)" }}>{kit.facts.slice(0, 2).map((f) => f.replace(/^./, (c) => c.toUpperCase())).join(". ")}.</p>
              <p className="tf-line" style={{ ["--k" as string]: "var(--k-3)" }}>Not provided, so left out: {kit.missing.join(", ") || "nothing"}.</p>
            </div>
            <div className="tf-line flex flex-wrap gap-1.5" style={{ ["--k" as string]: "var(--k-tags)" }}>{etsy.tags.slice(0, 8).map((t) => <span key={t} className="chip !min-h-0 py-[3px] text-[11.5px]">{t}</span>)}</div>
          </div>
        </div>

        <div className="tf-pack">
          {[<ListingPanel key="l" kit={kit} />, <TagsPanel key="t" kit={kit} max={5} />, <CaptionPanel key="c" kit={kit} />, <StoryboardPanel key="s" kit={kit} />, <PinPanel key="p" kit={kit} />,
            <div key="m" className="panel p-3.5 text-left"><p className="label muted">Checked</p><p className="mt-1.5 text-[.9em] leading-snug">Missing facts are flagged, not invented.</p></div>]
            .map((n, i) => <div key={i} className="tf-tile" style={{ ["--i" as string]: i, fontSize: 12 }}>{n}</div>)}
        </div>
        <p className="tf-hint label muted">Scroll</p>
      </div>
    </section>
  );
}

/** The finished state without motion: same content, ordinary flow. Also what shows before scripts run. */
function TransformStatic({ kit }: { kit: ReturnType<typeof generate> }) {
  return (
    <section className="tf-static wrap" id="transformation" aria-label="How one photo becomes a marketing package">
      <p className="label tick">The transformation</p>
      <h2 className="h2 mt-3 max-w-3xl">One input. Every deliverable.</h2>
      <div className="mt-10 grid items-start gap-6 md:grid-cols-[minmax(0,320px)_1fr]">
        <div className="relative overflow-hidden rounded-2xl ring-1 ring-white/15"><SampleProduct id="ts" className="aspect-[4/5] w-full" /><span className="label absolute left-2 top-2 rounded-full bg-black/60 px-2 py-1 text-[9px] text-white">Sample photo</span></div>
        <div className="grid gap-3 sm:grid-cols-2" style={{ fontSize: 13 }}>
          <ListingPanel kit={kit} /><CaptionPanel kit={kit} /><TagsPanel kit={kit} /><StoryboardPanel kit={kit} /><PinPanel kit={kit} />
        </div>
      </div>
    </section>
  );
}
