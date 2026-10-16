"use client";
import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Logo } from "../logo";
import { APP, DEMO_ONLY } from "./config";
import { HeroScene } from "./scene";

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
    <header className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${solid || open ? "bg-[rgb(0_49_53/.86)] backdrop-blur-xl" : "bg-transparent"}`} style={{ paddingTop: "env(safe-area-inset-top)" }}>
      <div className="wrap flex h-16 items-center justify-between">
        <Link href="/" className="flex min-h-11 items-center" aria-label="Mochi home" onClick={() => setOpen(false)}><Logo size={32} /></Link>
        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {links.map(([l, h]) => <a key={l} href={h} className="inline-flex min-h-11 items-center rounded-full px-4 text-sm text-[var(--paper)]/80 transition hover:text-white">{l}</a>)}
          <Link href={APP} className="btn btn-turq ml-2 !min-h-11 !px-5 text-sm">{DEMO_ONLY ? "Try the demo" : "Open the studio"}</Link>
        </nav>
        <button type="button" className="grid size-11 place-items-center rounded-full md:hidden" aria-expanded={open} aria-controls="mnav" aria-label={open ? "Close menu" : "Open menu"} onClick={() => setOpen((o) => !o)}>
          <span className="relative block h-3.5 w-6" aria-hidden><span className={`absolute left-0 h-[2px] w-6 bg-current transition ${open ? "top-1.5 rotate-45" : "top-0"}`} /><span className={`absolute left-0 top-3 h-[2px] w-6 bg-current transition ${open ? "top-1.5 -rotate-45" : ""}`} /></span>
        </button>
      </div>
      {open && (
        <nav id="mnav" aria-label="Mobile" className="wrap flex h-[calc(100svh-4rem)] flex-col justify-between pb-[max(2rem,env(safe-area-inset-bottom))] pt-6">
          <ul className="divide-y divide-white/10">{links.map(([l, h]) => <li key={l}><a href={h} onClick={() => setOpen(false)} className="flex min-h-16 items-center justify-between text-3xl font-light tracking-tight">{l}<ArrowRight className="size-5 muted" aria-hidden /></a></li>)}</ul>
          <Link href={APP} onClick={() => setOpen(false)} className="btn btn-turq w-full">{DEMO_ONLY ? "Try the demo" : "Open the studio"}</Link>
        </nav>
      )}
    </header>
  );
}

export function Hero() {
  return (
    <section className="hero relative isolate flex min-h-[100svh] flex-col overflow-hidden" aria-labelledby="hero-h" style={{ background: "var(--ink)" }}>
      {/* landscape: tall crop on phones, full-bleed on larger screens */}
      <div className="absolute inset-x-0 top-0 h-[70svh] md:inset-0 md:h-auto">
        <div className="absolute inset-0 md:hidden"><HeroScene portrait /></div>
        <div className="absolute inset-0 hidden md:block"><HeroScene /></div>
      </div>
      <div className="pointer-events-none absolute inset-x-0 bottom-0 top-[40svh] md:top-[58%]" style={{ background: "linear-gradient(to bottom, transparent 0%, rgb(0 49 53 / .5) 40%, rgb(0 49 53 / .96) 100%)" }} aria-hidden />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-40" style={{ background: "linear-gradient(to bottom, rgb(0 49 53 / .55), transparent)" }} aria-hidden />

      <div className="pointer-events-none absolute inset-0 hidden md:block" style={{ background: "linear-gradient(to right, rgb(0 49 53 / .62) 0%, rgb(0 49 53 / .25) 38%, transparent 58%)" }} aria-hidden />
      <div className="wrap pointer-events-none absolute inset-x-0 top-24 z-10 hidden md:block" aria-hidden><p className="label flex items-center gap-2 text-white/55"><span className="tracking-[.3em]">++</span>Scroll</p></div>

      <div className="wrap relative z-10 mt-auto pb-10 pt-[52svh] md:pb-14 md:pt-0">
        <div className="grid items-end gap-7 md:max-w-[46rem]">
          <div>
            <p className="label tick reveal mb-4 flex items-center gap-2"><span className="size-1.5 rounded-full bg-[var(--turq-soft)]" style={{ animation: "lp-pulse 2s infinite" }} />Introducing mochi</p>
            <h1 id="hero-h" className="display-hero text-white">
              {["Your product.", "Your story.", "Ready to sell."].map((line, i) => (
                <span key={line} className="block"><span className="word"><span style={{ ["--d" as string]: `${0.1 + i * 0.12}s` }} className={i === 2 ? "text-[var(--ice)]" : ""}>{line}{i === 2 && <span aria-hidden className="ml-3 inline-block text-[.6em] text-[var(--turq-soft)]">→</span>}</span></span></span>
              ))}
            </h1>
          </div>
          <div className="reveal" style={{ ["--d" as string]: ".45s" }}>
            <p className="lede max-w-md text-[var(--paper)]/80">Turn a single product photo into compelling listings, on-brand captions, and scroll-stopping video ads.</p>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <Link href={APP} className="btn btn-turq w-full sm:w-auto">Create your first campaign <ArrowRight className="size-4" aria-hidden /></Link>
              <a href="#studio" className="btn btn-ghost w-full sm:w-auto">Explore the studio</a>
            </div>
            <p className="mt-4 text-[13px] text-[var(--paper)]/60">Open models. Runs on your computer. Nothing posts unless you tap it.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
