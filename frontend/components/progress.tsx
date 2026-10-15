"use client";
import { AlertTriangle, Check, Circle, Loader2, MinusCircle, RotateCw } from "lucide-react";
import type { GenerationJob } from "@/lib/types";
import { Button, cx } from "./ui";

const STEPS = [
  { key: "copy", label: "Writing product copy" },
  { key: "video", label: "Creating video" },
  { key: "voiceover", label: "Generating voiceover" },
  { key: "assembly", label: "Assembling final video" },
];

export function Progress({ job, onRetry, retrying }: { job: GenerationJob; onRetry: () => void; retrying: boolean }) {
  const steps = STEPS.filter((s) => s.key !== "voiceover" || job.settings.voiceover);
  return (
    <div className="space-y-5">
      <ol className="space-y-3" aria-live="polite">
        {steps.map((s) => {
          const st = job.stages.find((x) => x.name === s.key)?.status;
          return (
            <li key={s.key} className="flex items-center gap-3">
              {st === "done" ? <Check className="size-5 text-ok" aria-label="done" />
                : st === "running" ? <Loader2 className="size-5 animate-spin text-accent" aria-label="in progress" />
                : st === "failed" ? <AlertTriangle className="size-5 text-danger" aria-label="failed" />
                : st === "skipped" ? <MinusCircle className="size-5 text-muted" aria-label="skipped" />
                : <Circle className="size-5 text-border" aria-label="waiting" />}
              <span className={cx(st === "running" && "font-medium", (!st || st === "skipped") && "text-muted")}>
                {s.label}{st === "skipped" && " (not enabled yet)"}
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
