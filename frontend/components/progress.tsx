"use client";
import { AlertTriangle, Check, Circle, Loader2, MinusCircle, RotateCw } from "lucide-react";
import type { GenerationJob } from "@/lib/types";
import { Button, cx } from "./ui";

const STEPS = [
  { key: "copy", label: "Writing your copy", hint: "Several parts are written at once" },
  { key: "video", label: "Building studio video and photos", hint: "Background removal, lighting, camera moves" },
  { key: "voiceover", label: "Generating voiceover", hint: "" },
  { key: "assembly", label: "Adding text to the video", hint: "" },
];

export function ProgressBar({ value, label }: { value: number; label?: string | null }) {
  const pct = Math.round(Math.min(Math.max(value, 0), 1) * 100);
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <span className="min-w-0 truncate text-sm font-medium">{label ?? "Working"}</span>
        <span className="text-2xl font-semibold tabular-nums tracking-tight">{pct}<span className="text-base text-muted">%</span></span>
      </div>
      <div role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-label="Overall progress" className="h-3 overflow-hidden rounded-full bg-border">
        <div className="relative h-full rounded-full bg-accent transition-[width] duration-700 ease-out" style={{ width: `${Math.max(pct, 3)}%` }}>
          <span className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-white/30 to-transparent" style={{ backgroundSize: "200% 100%", animation: "shimmer 1.6s linear infinite" }} />
        </div>
      </div>
    </div>
  );
}

export function Progress({ job, onRetry, retrying }: { job: GenerationJob; onRetry: () => void; retrying: boolean }) {
  const steps = STEPS.filter((s) => s.key !== "voiceover" || job.settings.voiceover);
  const running = job.status !== "failed" && job.status !== "completed";
  return (
    <div className="space-y-5">
      {running && <ProgressBar value={job.progress} label={job.phase} />}
      <ol className="space-y-3" aria-live="polite">
        {steps.map((s) => {
          const entry = job.stages.find((x) => x.name === s.key);
          const st = entry?.status;
          return (
            <li key={s.key} className="flex items-center gap-3">
              {st === "done" ? <Check className="size-5 text-ok" aria-label="done" />
                : st === "running" ? <Loader2 className="size-5 animate-spin text-accent-text" aria-label="in progress" />
                : st === "failed" ? <AlertTriangle className="size-5 text-danger" aria-label="failed" />
                : st === "skipped" ? <MinusCircle className="size-5 text-muted" aria-label="skipped" />
                : <Circle className="size-5 text-border-strong" aria-label="waiting" />}
              <span className={cx("min-w-0", st === "running" && "font-medium", (!st || st === "skipped") && "text-muted")}>
                {s.label}
                {st === "skipped" && " (not enabled yet)"}
                {st === "running" && s.key === "copy" && entry?.detail?.includes("parts") && <span className="ml-1.5 font-normal text-muted">{entry.detail}</span>}
                {st === "running" && s.hint && <span className="block text-xs font-normal text-muted">{s.hint}</span>}
              </span>
            </li>
          );
        })}
      </ol>
      {job.status === "queued" && <p className="text-sm text-muted">Waiting to start…</p>}
      {job.status === "failed" && job.error && (
        <div role="alert" className="space-y-3 rounded-xl border border-danger/40 bg-danger/10 p-4">
          <p className="font-medium text-danger">Generation failed</p>
          <p className="text-sm">{job.error.message}</p>
          {job.error.retryable && <Button variant="secondary" busy={retrying} onClick={onRetry}><RotateCw className="size-4" />Try again</Button>}
        </div>
      )}
    </div>
  );
}
