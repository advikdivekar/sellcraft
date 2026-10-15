"use client";
import { Check } from "lucide-react";
import { cx } from "./ui";

export function Stepper({ steps, current, onGo, maxReached }: { steps: string[]; current: number; onGo: (i: number) => void; maxReached: number }) {
  return (
    <ol className="flex items-center" aria-label="Progress">
      {steps.map((label, i) => {
        const done = i < current, active = i === current, reachable = i <= maxReached;
        return (
          <li key={label} className={cx("flex items-center", i < steps.length - 1 && "flex-1")}>
            <button type="button" disabled={!reachable} onClick={() => onGo(i)} aria-current={active ? "step" : undefined}
              className="group flex min-h-11 items-center gap-2 rounded-xl pr-2 disabled:cursor-default">
              <span className={cx("grid size-8 place-items-center rounded-full text-sm font-semibold transition",
                active && "bg-accent text-accent-fg shadow-card", done && "bg-accent-soft text-accent", !active && !done && "border border-border-strong bg-surface text-muted")}>
                {done ? <Check className="size-4" aria-hidden /> : i + 1}
              </span>
              <span className={cx("text-sm font-medium transition-colors", active ? "text-foreground" : "text-muted", "max-sm:hidden", active && "max-sm:inline")}>{label}</span>
            </button>
            {i < steps.length - 1 && <span className={cx("mx-1 h-px flex-1 transition-colors", i < current ? "bg-accent" : "bg-border-strong")} />}
          </li>
        );
      })}
    </ol>
  );
}
