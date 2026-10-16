"use client";
import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { CaptionPanel, ListingPanel, StoryboardPanel, TagsPanel, PinPanel } from "./parts";
import { APP, DEMO_ONLY } from "./config";
import { generate, SAMPLE } from "./demo";
import { useMedia, useReducedMotion } from "./hooks";
import { SampleProduct } from "./sample-product";

export function Navbar() {
  const [solid, setSolid] = useState(false);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const on = () => setSolid(window.scrollY > 24);
    on(); window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", esc);
    return () => { document.body.style.overflow = ""; window.removeEventListener("keydown", esc); };
  }, [open]);
  const links = [["Product", "#studio"], ["How it works", "#how"], ["Features", "#channels"]] as const;
  return (
    <header className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${solid || open ? "bg-[rgb(11_11_10/.82)] backdrop-blur-xl" : "bg-transparent"}`} style={{ paddingTop: "env(safe-area-inset-top)" }}>
      <div className="wrap flex h-16 items-center justify-between">
        <Link href="/" className="flex min-h-11 items-center gap-2 text-[17px] font-medium tracking-tight" aria-label="SellCraft AI home" onClick={() => setOpen(false)}>
          <span className="grid size-7 place-items-center rounded-lg bg-[var(--lime)] text-[var(--lime-ink)]" aria-hidden><svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round"><path d="M5 17 12 4l7 13M8.5 13h7" /></svg></span>
          SellCraft<span className="serif text-[var(--lime)]"> AI</span>
        </Link>
        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {links.map(([l, h]) => <a key={l} href={h} className="inline-flex min-h-11 items-center rounded-full px-4 text-sm muted transition hover:text-[var(--paper)]">{l}</a>)}
          <Link href={APP} className="btn btn-lime ml-2 !min-h-11 !px-5 text-sm">{DEMO_ONLY ? "Try the demo" : "Open the app"}</Link>
        </nav>
        <button type="button" className="grid size-11 place-items-center rounded-full md:hidden" aria-expanded={open} aria-controls="mnav" aria-label={open ? "Close menu" : "Open menu"} onClick={() => setOpen((o) => !o)}>
          <span className="relative block h-3.5 w-6" aria-hidden><span className={`absolute left-0 h-[2px] w-6 bg-current transition ${open ? "top-1.5 rotate-45" : "top-0"}`} /><span className={`absolute left-0 top-3 h-[2px] w-6 bg-current transition ${open ? "top-1.5 -rotate-45" : ""}`} /></span>
        </button>
      </div>
      {open && (
        <nav id="mnav" aria-label="Mobile" className="wrap flex h-[calc(100svh-4rem)] flex-col justify-between pb-[max(2rem,env(safe-area-inset-bottom))] pt-6">
          <ul className="divide-y divide-white/10">{links.map(([l, h]) => <li key={l}><a href={h} onClick={() => setOpen(false)} className="flex min-h-16 items-center justify-between text-3xl font-medium tracking-tight">{l}<ArrowRight className="size-5 muted" aria-hidden /></a></li>)}</ul>
          <Link href={APP} onClick={() => setOpen(false)} className="btn btn-lime w-full">{DEMO_ONLY ? "Try the demo" : "Open the app"}</Link>
        </nav>
      )}
    </header>
  );
}

const WORDS = [["From", "product", "photo"], ["to", "ready-to-sell."]];

export function Hero() {
  const reduced = useReducedMotion();
  const fine = useMedia("(hover: hover) and (pointer: fine) and (min-width: 1024px)");
  const kit = useMemo(() => generate(SAMPLE.name, SAMPLE.details, "instagram", "luxury"), []);
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = root.current;
    if (!el || reduced || !fine) return;
    let raf = 0;
    const move = (e: PointerEvent) => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const r = el.getBoundingClientRect();
        el.style.setProperty("--mx", String(((e.clientX - r.left) / r.width - 0.5) * 2));
        el.style.setProperty("--my", String(((e.clientY - r.top) / r.height - 0.5) * 2));
      });
    };
    const leave = () => { el.style.setProperty("--mx", "0"); el.style.setProperty("--my", "0"); };
    el.addEventListener("pointermove", move); el.addEventListener("pointerleave", leave);
    return () => { el.removeEventListener("pointermove", move); el.removeEventListener("pointerleave", leave); cancelAnimationFrame(raf); };
  }, [reduced, fine]);

  return (
    <section ref={root} className="relative flex min-h-[100svh] flex-col justify-start overflow-hidden pb-10 pt-24 md:justify-center md:pb-14" aria-labelledby="hero-h">
      <div className="pointer-events-none absolute inset-0" aria-hidden style={{ background: "radial-gradient(60% 50% at 70% 45%, rgb(198 244 50 / .09), transparent 70%), radial-gradient(50% 40% at 10% 90%, rgb(198 244 50 / .05), transparent 70%)", maskImage: "linear-gradient(to bottom, #000 55%, transparent 100%)", WebkitMaskImage: "linear-gradient(to bottom, #000 55%, transparent 100%)" }} />
      <div className="wrap relative grid items-center gap-8 lg:grid-cols-[1fr_1fr] lg:gap-10">
        <div className="order-1">
          <p className="label tick reveal mb-3 sm:mb-5 flex items-center gap-2"><span className="size-1.5 rounded-full bg-[var(--lime)]" style={{ animation: "lp-pulse 2s infinite" }} />Made for the people who sell</p>
          <h1 id="hero-h" className="display-hero">
            {WORDS.map((line, li) => (
              <span key={li} className="block">
                {line.map((w, wi) => { const last = li === 1 && w.startsWith("ready"); const d = 0.12 + (li * 3 + wi) * 0.08; return <span key={w} className="word mr-[.22em]"><span style={{ ["--d" as string]: `${d}s` }} className={last ? "serif text-[var(--lime)]" : ""}>{w}</span></span>; })}
              </span>
            ))}
          </h1>
          <p className="lede reveal mt-6 max-w-[34rem] muted" style={{ ["--d" as string]: ".5s" }}>Turn a single product photo into scroll-stopping ads, persuasive listings, and platform-ready content — all powered by AI.</p>
          <div className="reveal mt-8 flex flex-col gap-3 sm:flex-row" style={{ ["--d" as string]: ".6s" }}>
            <Link href={APP} className="btn btn-lime w-full sm:w-auto">Create your first listing <ArrowRight className="size-4" aria-hidden /></Link>
            <a href="#transformation" className="btn btn-ghost w-full sm:w-auto">See how it works</a>
          </div>
          <p className="mt-5 text-[13px] muted">Open models. Runs on your computer. Nothing posts unless you tap it.</p>
        </div>

        <div className="pp hero-c order-2 mx-auto mt-5 w-full max-w-[30rem] lg:mt-0 lg:max-w-none" aria-hidden>
          <div className="relative h-[min(21rem,44svh)] w-full lg:h-auto lg:aspect-[1/1.02]" style={{ fontSize: "clamp(9.5px, 2.5cqw, 13.5px)" }}>
            <div className="px absolute left-1/2 top-1/2 w-[50%] -translate-x-1/2 -translate-y-1/2 lg:w-[46%]" style={{ ["--k" as string]: 6 }}>
              <div className="relative overflow-hidden rounded-[18px] shadow-[0_40px_80px_-30px_#000] ring-1 ring-white/15"><SampleProduct id="hero" className="aspect-[4/5] w-full" /><span className="label absolute left-2 top-2 rounded-full bg-black/60 px-2 py-1 text-[8px] text-white backdrop-blur">Sample photo</span></div>
            </div>
            <div className="px absolute left-[-1%] top-[0%] w-[47%] lg:left-[-2%] lg:top-[4%] lg:w-[52%]" style={{ ["--k" as string]: 16 }}><div style={{ animation: "lp-float 7s ease-in-out infinite" }}><ListingPanel kit={kit} /></div></div>
            <div className="px absolute right-[-1%] top-[34%] w-[45%] lg:right-[-2%] lg:top-[10%] lg:w-[48%]" style={{ ["--k" as string]: 22 }}><div style={{ animation: "lp-float 6s ease-in-out -2s infinite" }}><CaptionPanel kit={kit} /></div></div>
            <div className="px absolute bottom-[2%] left-[-1%] w-[44%] lg:bottom-[8%] lg:left-[-3%] lg:w-[50%]" style={{ ["--k" as string]: 20 }}><div style={{ animation: "lp-float 8s ease-in-out -4s infinite" }}><TagsPanel kit={kit} max={5} /></div></div>
            <div className="px absolute bottom-[-2%] right-[-1%] hidden w-[46%] sm:block lg:bottom-[2%] lg:right-[-2%] lg:w-[50%]" style={{ ["--k" as string]: 14 }}><div style={{ animation: "lp-float 6.5s ease-in-out -1s infinite" }}><StoryboardPanel kit={kit} /></div></div>
            <div className="px absolute right-[8%] top-[46%] hidden w-[44%] lg:block" style={{ ["--k" as string]: 28 }}><div style={{ animation: "lp-float 7.5s ease-in-out -3s infinite" }}><PinPanel kit={kit} /></div></div>
          </div>
        </div>
      </div>
    </section>
  );
}
