"use client";
import { Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function cx(...c: (string | false | null | undefined)[]) {
  return c.filter(Boolean).join(" ");
}

type BtnProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  busy?: boolean;
  size?: "md" | "sm";
};
export function Button({ variant = "primary", busy, size = "md", className, children, disabled, ...p }: BtnProps) {
  return (
    <button
      {...p}
      disabled={disabled || busy}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        size === "md" ? "min-h-12 px-5 text-base" : "min-h-11 px-3.5 text-sm",
        variant === "primary" && "bg-accent text-white hover:opacity-90 dark:text-black",
        variant === "secondary" && "border border-border bg-surface hover:bg-accent-soft",
        variant === "ghost" && "text-muted hover:bg-accent-soft hover:text-foreground",
        className,
      )}
    >
      {busy && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={cx("rounded-2xl border border-border bg-surface p-4 sm:p-5", className)}>{children}</section>;
}

export function Field({ label, hint, optional, error, children }: {
  label: string; hint?: string; optional?: boolean; error?: string; children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 flex items-baseline justify-between gap-2 text-sm font-medium">
        <span>{label}</span>
        {optional && <span className="text-xs font-normal text-muted">optional</span>}
      </span>
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-muted">{hint}</span>}
      {error && <span role="alert" className="mt-1 block text-xs text-danger">{error}</span>}
    </label>
  );
}

export const inputCls =
  "w-full rounded-xl border border-border bg-background px-3.5 py-3 text-foreground placeholder:text-muted/70 focus:border-accent";

export function Chips<T extends string>({ options, value, onChange, label, multi }: {
  options: { value: T; label: string }[];
  value: T | T[];
  onChange: (v: T) => void;
  label: string;
  multi?: boolean;
}) {
  const sel = (v: T) => (Array.isArray(value) ? value.includes(v) : value === v);
  return (
    <div role={multi ? "group" : "radiogroup"} aria-label={label} className="flex flex-wrap gap-2">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role={multi ? "checkbox" : "radio"}
          aria-checked={sel(o.value)}
          onClick={() => onChange(o.value)}
          className={cx(
            "min-h-11 rounded-full border px-4 text-sm font-medium transition-colors",
            sel(o.value) ? "border-accent bg-accent text-white dark:text-black" : "border-border bg-surface hover:bg-accent-soft",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
