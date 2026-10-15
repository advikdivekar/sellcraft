"use client";
import { Loader2, X } from "lucide-react";
import { useEffect, useRef } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { buttonClass, cx, type Size, type Variant } from "@/lib/styles";
export { buttonClass, cx };

type BtnProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; busy?: boolean; size?: Size };

export function Button({ variant = "primary", busy, size = "md", className, children, disabled, ...p }: BtnProps) {
  return (
    <button {...p} disabled={disabled || busy} className={buttonClass(variant, size, className)}>
      {busy && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function Card({ children, className, pad = true, bleed }: { children: ReactNode; className?: string; pad?: boolean; bleed?: boolean }) {
  return (
    <section className={cx("bg-surface",
      bleed ? "max-sm:-mx-4 max-sm:border-y max-sm:border-border sm:rounded-xl sm:shadow-card sm:ring-1 sm:ring-border" : "rounded-xl shadow-card ring-1 ring-border",
      pad && "p-4 sm:p-6", className)}>{children}</section>
  );
}

export function SectionTitle({ children, hint, action }: { children: ReactNode; hint?: string; action?: ReactNode }) {
  return (
    <div className="mb-4 flex items-start justify-between gap-3">
      <div><h2 className="text-[15px] font-semibold tracking-tight">{children}</h2>{hint && <p className="mt-0.5 text-[13px] leading-snug text-muted">{hint}</p>}</div>
      {action}
    </div>
  );
}

export function Badge({ children, tone = "neutral", className }: { children: ReactNode; tone?: "neutral" | "accent" | "ok" | "warn" | "danger"; className?: string }) {
  return (
    <span className={cx("inline-flex items-center gap-1 rounded-full px-2.5 py-[3px] text-xs font-medium",
      tone === "neutral" && "bg-surface-2 text-muted ring-1 ring-border", tone === "accent" && "bg-accent-soft text-accent-text",
      tone === "ok" && "bg-ok/12 text-ok", tone === "warn" && "bg-warn/12 text-warn", tone === "danger" && "bg-danger/12 text-danger", className)}>
      {children}
    </span>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cx("skeleton rounded-lg", className)} aria-hidden />;
}

export function Field({ label, hint, optional, error, suggested, children }: {
  label: string; hint?: string; optional?: boolean; error?: string; suggested?: boolean; children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 flex items-center justify-between gap-2 text-[13px] font-medium">
        <span>{label}</span>
        {suggested ? <Badge tone="accent">From photo · check it</Badge> : optional && <span className="text-xs font-normal text-muted">optional</span>}
      </span>
      {children}
      {hint && !error && <span className="mt-1.5 block text-xs text-muted">{hint}</span>}
      {error && <span role="alert" className="mt-1.5 block text-xs font-medium text-danger">{error}</span>}
    </label>
  );
}

export const inputCls =
  "w-full rounded-[10px] bg-surface px-3.5 py-3 text-foreground shadow-card ring-1 ring-border-strong transition placeholder:text-muted/55 hover:ring-foreground/30 focus:outline-none focus:ring-2 focus:ring-foreground";

export function Chips<T extends string>({ options, value, onChange, label, multi }: {
  options: { value: T; label: string }[]; value: T | T[]; onChange: (v: T) => void; label: string; multi?: boolean;
}) {
  const sel = (v: T) => (Array.isArray(value) ? value.includes(v) : value === v);
  return (
    <div role={multi ? "group" : "radiogroup"} aria-label={label} className="flex flex-wrap gap-2">
      {options.map((o) => (
        <button key={o.value} type="button" role={multi ? "checkbox" : "radio"} aria-checked={sel(o.value)} onClick={() => onChange(o.value)}
          className={cx("min-h-11 rounded-full px-4 text-sm font-medium transition duration-150 active:scale-[0.96]",
            sel(o.value) ? "bg-primary text-primary-fg shadow-card" : "bg-surface text-foreground ring-1 ring-border-strong hover:ring-foreground/40")}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Underline tabs; a scrollable strip on small screens. */
export function Tabs<T extends string>({ tabs, value, onChange, label, variant = "underline" }: {
  tabs: { id: T; label: string; badge?: string | number }[]; value: T; onChange: (v: T) => void; label: string; variant?: "underline" | "segment";
}) {
  if (variant === "segment")
    return (
      <div role="tablist" aria-label={label} className="no-scrollbar flex gap-1 overflow-x-auto rounded-[12px] bg-surface-2 p-1 ring-1 ring-border">
        {tabs.map((t) => (
          <button key={t.id} role="tab" aria-selected={value === t.id} onClick={() => onChange(t.id)}
            className={cx("inline-flex min-h-10 min-w-fit flex-1 items-center justify-center gap-1.5 whitespace-nowrap rounded-[9px] px-3.5 text-sm font-medium transition",
              value === t.id ? "bg-surface text-foreground shadow-card ring-1 ring-border" : "text-muted hover:text-foreground")}>
            {t.label}{t.badge !== undefined && <span className="rounded-full bg-border px-1.5 text-[11px] tabular-nums">{t.badge}</span>}
          </button>
        ))}
      </div>
    );
  return (
    <div role="tablist" aria-label={label} className="no-scrollbar -mx-4 flex gap-1 overflow-x-auto border-b border-border px-4 sm:mx-0 sm:px-0">
      {tabs.map((t) => (
        <button key={t.id} role="tab" aria-selected={value === t.id} onClick={() => onChange(t.id)}
          className={cx("relative inline-flex min-h-12 shrink-0 items-center gap-1.5 px-3.5 text-sm font-medium transition-colors", value === t.id ? "text-foreground" : "text-muted hover:text-foreground")}>
          {t.label}
          {t.badge !== undefined && <span className="rounded-full bg-surface-2 px-1.5 text-[11px] tabular-nums ring-1 ring-border">{t.badge}</span>}
          <span className={cx("absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-foreground transition-opacity", value === t.id ? "opacity-100" : "opacity-0")} />
        </button>
      ))}
    </div>
  );
}

/** Bottom sheet on phones, centred modal on larger screens. Closes on backdrop tap and Escape. */
export function Sheet({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog ref={ref} onClose={onClose} onClick={(e) => { if (e.target === ref.current) onClose(); }}
      className="sheet m-0 mt-auto w-full max-w-none rounded-t-[20px] bg-surface p-0 text-foreground shadow-float ring-1 ring-border sm:m-auto sm:max-w-md sm:rounded-xl">
      <div className="mx-auto mt-2 h-1 w-9 rounded-full bg-border-strong sm:hidden" aria-hidden />
      <div className="flex items-center justify-between gap-3 px-5 pb-2 pt-3">
        <h2 className="text-base font-semibold tracking-tight">{title}</h2>
        <button type="button" onClick={onClose} aria-label="Close" className="grid size-9 place-items-center rounded-full text-muted transition hover:bg-surface-2"><X className="size-4" /></button>
      </div>
      <div className="px-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-1">{children}</div>
    </dialog>
  );
}
