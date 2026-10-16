"use client";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";

export const clamp01 = (n: number) => Math.min(1, Math.max(0, n));
/** Progress of v through [a, b], clamped to 0..1. */
export const seg = (v: number, a: number, b: number) => clamp01((v - a) / (b - a));
export const ease = (t: number) => t * t * (3 - 2 * t);

function subscribeMedia(query: string) {
  return (cb: () => void) => { const m = window.matchMedia(query); m.addEventListener("change", cb); return () => m.removeEventListener("change", cb); };
}
export function useMedia(query: string, server = false) {
  return useSyncExternalStore(subscribeMedia(query), () => window.matchMedia(query).matches, () => server);
}
/** True when the visitor asked for less motion. Re-evaluates if the setting changes. */
export const useReducedMotion = () => useMedia("(prefers-reduced-motion: reduce)");
/** False during server render and hydration, true afterwards. */
export const useMounted = () => useSyncExternalStore(() => () => {}, () => true, () => false);

/**
 * Scroll-linked progress for a tall section. Writes `--p` (0..1) and calls `apply` with it, from ONE passive scroll
 * listener throttled by requestAnimationFrame, and only while the section is near the viewport. No React state, so no re-renders.
 * `p` is 0 when the section's top reaches the viewport top and 1 when its bottom reaches the viewport bottom.
 */
export function useScrollProgress<T extends HTMLElement>(apply: (p: number, el: T) => void, enabled = true) {
  const ref = useRef<T>(null);
  const fn = useRef(apply);
  useEffect(() => { fn.current = apply; });
  useEffect(() => {
    const el = ref.current;
    if (!el || !enabled) return;
    let raf = 0, live = false;
    const tick = () => {
      raf = 0;
      const r = el.getBoundingClientRect();
      const total = r.height - window.innerHeight;
      const p = total > 0 ? clamp01(-r.top / total) : 0;
      el.style.setProperty("--p", p.toFixed(4));
      fn.current(p, el);
    };
    const onScroll = () => { if (!raf) raf = requestAnimationFrame(tick); };
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !live) { live = true; window.addEventListener("scroll", onScroll, { passive: true }); window.addEventListener("resize", onScroll); onScroll(); }
      else if (!e.isIntersecting && live) { live = false; window.removeEventListener("scroll", onScroll); window.removeEventListener("resize", onScroll); onScroll(); }
    }, { rootMargin: "200px 0px" });
    io.observe(el); tick();
    return () => { io.disconnect(); window.removeEventListener("scroll", onScroll); window.removeEventListener("resize", onScroll); if (raf) cancelAnimationFrame(raf); };
  }, [enabled]);
  return ref;
}

/** Adds `.in` to every `.reveal` inside the root once it scrolls into view. */
export function useReveal() {
  useEffect(() => {
    const root = document.querySelector(".lp");
    if (!root) return;
    root.classList.add("js");
    const els = root.querySelectorAll<HTMLElement>(".reveal");
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  }, []);
}

export function useCopy() {
  const [done, setDone] = useState<string | null>(null);
  const t = useRef<ReturnType<typeof setTimeout>>(undefined);
  async function copy(id: string, text: string) {
    try { await navigator.clipboard.writeText(text); }
    catch {
      const a = document.createElement("textarea"); a.value = text; a.style.position = "fixed"; a.style.opacity = "0";
      document.body.appendChild(a); a.select(); try { document.execCommand("copy"); } catch { /* ignore */ } a.remove();
    }
    setDone(id); clearTimeout(t.current); t.current = setTimeout(() => setDone(null), 1600);
  }
  return { done, copy };
}
