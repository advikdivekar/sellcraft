"use client";
import { Check } from "lucide-react";
import { cx } from "./ui";

export function Stepper({ steps, current, onGo, maxReached }: { steps: string[]; current: number; onGo: (i: number) => void; maxReached: number }) {
  return (
    <>
      {/* Phone: segmented bar + "Step 1 of 3" (compact, like a native onboarding flow) */}
      <div className="sm:hidden" role="group" aria-label="Progress">
        <div className="flex gap-1.5">
          {steps.map((label, i) => (
            <button key={label} type="button" disabled={i > maxReached} onClick={() => onGo(i)} aria-label={`Step ${i + 1}: ${label}`} aria-current={i === current ? "step" : undefined}
              className="group h-6 flex-1 disabled:cursor-default"><span className={cx("block h-1 rounded-full transition-colors duration-300", i <= current ? "bg-foreground" : "bg-border-strong")} /></button>
          ))}
        </div>
        <p className="mt-1 flex items-baseline gap-2 text-[13px]"><span className="eyebrow">Step {current + 1} of {steps.length}</span><span className="font-medium">{steps[current]}</span></p>
      </div>
      {/* Tablet and up */}
      <ol className="hidden items-center sm:flex" aria-label="Progress">
        {steps.map((label, i) => {
          const done = i < current, active = i === current, reachable = i <= maxReached;
          return (
            <li key={label} className={cx("flex items-center", i < steps.length - 1 && "flex-1")}>
              <button type="button" disabled={!reachable} onClick={() => onGo(i)} aria-current={active ? "step" : undefined} className="flex min-h-11 items-center gap-2.5 rounded-lg pr-2 disabled:cursor-default">
                <span className={cx("grid size-7 place-items-center rounded-full text-[13px] font-semibold transition", active && "bg-primary text-primary-fg", done && "bg-accent-soft text-accent-text", !active && !done && "bg-surface text-muted ring-1 ring-border-strong")}>
                  {done ? <Check className="size-3.5" aria-hidden /> : i + 1}
                </span>
                <span className={cx("text-sm font-medium transition-colors", active ? "text-foreground" : "text-muted")}>{label}</span>
              </button>
              {i < steps.length - 1 && <span className={cx("mx-2 h-px flex-1 transition-colors", i < current ? "bg-foreground" : "bg-border-strong")} />}
            </li>
          );
        })}
      </ol>
    </>
  );
}
