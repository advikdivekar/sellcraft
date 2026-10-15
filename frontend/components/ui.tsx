"use client";
import { Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function cx(...c: (string | false | null | undefined)[]) {
  return c.filter(Boolean).join(" ");
}

type BtnProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  busy?: boolean;
  size?: "lg" | "md" | "sm";
};

export function Button({ variant = "primary", busy, size = "md", className, children, disabled, ...p }: BtnProps) {
  return (
    <button
      {...p}
      disabled={disabled || busy}
      className={cx(
        "inline-flex select-none items-center justify-center gap-2 rounded-xl font-medium transition duration-150 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100",
        size === "lg" && "min-h-13 px-6 text-base",
        size === "md" && "min-h-12 px-5 text-[15px]",
        size === "sm" && "min-h-11 px-3.5 text-sm",
        variant === "primary" && "bg-accent text-accent-fg shadow-card hover:brightness-110",
        variant === "secondary" && "border border-border-strong bg-surface text-foreground shadow-card hover:bg-surface-2",
        variant === "ghost" && "text-muted hover:bg-accent-soft hover:text-foreground",
        variant === "danger" && "bg-danger text-white hover:brightness-110",
        className,
      )}
    >
      {busy && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function Card({ children, className, pad = true }: { children: ReactNode; className?: string; pad?: boolean }) {
  return <section className={cx("rounded-2xl border border-border bg-surface shadow-card", pad && "p-4 sm:p-6", className)}>{children}</section>;
}

export function SectionTitle({ children, hint, action }: { children: ReactNode; hint?: string; action?: ReactNode }) {
  return (
    <div className="mb-3 flex items-start justify-between gap-3">
      <div><h2 className="text-base font-semibold">{children}</h2>{hint && <p className="mt-0.5 text-sm text-muted">{hint}</p>}</div>
      {action}
    </div>
  );
}

export function Badge({ children, tone = "neutral", className }: { children: ReactNode; tone?: "neutral" | "accent" | "ok" | "warn" | "danger"; className?: string }) {
  return (
    <span className={cx("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
      tone === "neutral" && "bg-border/60 text-muted", tone === "accent" && "bg-accent-soft text-accent",
      tone === "ok" && "bg-ok/15 text-ok", tone === "warn" && "bg-warn/15 text-warn", tone === "danger" && "bg-danger/15 text-danger", className)}>
      {children}
    </span>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cx("skeleton rounded-xl", className)} aria-hidden />;
}

export function Field({ label, hint, optional, error, suggested, children }: {
  label: string; hint?: string; optional?: boolean; error?: string; suggested?: boolean; children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 flex items-center justify-between gap-2 text-sm font-medium">
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
  "w-full rounded-xl border border-border-strong bg-surface px-3.5 py-3 text-foreground shadow-card transition placeholder:text-muted/60 hover:border-foreground/30 focus:border-accent focus:outline-none focus:ring-4 focus:ring-accent/15";

export function Chips<T extends string>({ options, value, onChange, label, multi }: {
  options: { value: T; label: string }[]; value: T | T[]; onChange: (v: T) => void; label: string; multi?: boolean;
}) {
  const sel = (v: T) => (Array.isArray(value) ? value.includes(v) : value === v);
  return (
    <div role={multi ? "group" : "radiogroup"} aria-label={label} className="flex flex-wrap gap-2">
      {options.map((o) => (
        <button key={o.value} type="button" role={multi ? "checkbox" : "radio"} aria-checked={sel(o.value)} onClick={() => onChange(o.value)}
          className={cx("min-h-11 rounded-full border px-4 text-sm font-medium transition duration-150 active:scale-[0.97]",
            sel(o.value) ? "border-accent bg-accent text-accent-fg shadow-card" : "border-border-strong bg-surface hover:border-foreground/40")}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Underline tabs with a horizontally scrollable strip on small screens. */
export function Tabs<T extends string>({ tabs, value, onChange, label }: {
  tabs: { id: T; label: string; badge?: string | number }[]; value: T; onChange: (v: T) => void; label: string;
}) {
  return (
    <div role="tablist" aria-label={label} className="no-scrollbar -mx-4 flex gap-1 overflow-x-auto border-b border-border px-4 sm:mx-0 sm:px-0">
      {tabs.map((t) => (
        <button key={t.id} role="tab" aria-selected={value === t.id} onClick={() => onChange(t.id)}
          className={cx("relative inline-flex min-h-12 shrink-0 items-center gap-1.5 px-3.5 text-sm font-medium transition-colors",
            value === t.id ? "text-foreground" : "text-muted hover:text-foreground")}>
          {t.label}
          {t.badge !== undefined && <span className="rounded-full bg-border/70 px-1.5 text-[11px] tabular-nums">{t.badge}</span>}
          <span className={cx("absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-accent transition-opacity", value === t.id ? "opacity-100" : "opacity-0")} />
        </button>
      ))}
    </div>
  );
}
