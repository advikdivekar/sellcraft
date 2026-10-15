"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cx } from "./ui";

export function StatusBadge() {
  const { data, isError, isLoading } = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: 15000 });
  if (isLoading) return <div className="skeleton h-5 w-64 rounded-full" aria-label="Checking AI engine" />;
  if (isError || !data)
    return <Pill tone="bad" text="Backend offline" detail="Start the API: cd backend && .venv/bin/uvicorn app.main:app --port 8000" />;
  const l = data.llm;
  if (data.demo_mode) return <Pill tone="warn" text="Demo Mode" detail="Deterministic sample output, not a live model." />;
  if (!l.reachable) return <Pill tone="bad" text="Ollama not running" detail={l.hint} />;
  if (!l.model_available) return <Pill tone="warn" text={`Model ${l.model} not installed`} detail={l.hint} />;
  return <Pill tone="ok" text={`Open model ready: ${l.model}`} detail="Running locally through Ollama" />;
}

function Pill({ tone, text, detail }: { tone: "ok" | "warn" | "bad"; text: string; detail?: string }) {
  return (
    <div className="flex items-start gap-2.5 text-[13px]" role="status">
      <span className="relative mt-1.5 flex size-2 shrink-0">
        {tone === "ok" && <span className="absolute inline-flex size-full animate-ping rounded-full bg-ok opacity-50" />}
        <span className={cx("relative inline-flex size-2 rounded-full", tone === "ok" && "bg-ok", tone === "warn" && "bg-warn", tone === "bad" && "bg-danger")} />
      </span>
      <span className="min-w-0"><span className="font-medium">{text}</span>{detail && <span className="text-muted"> · {detail}</span>}</span>
    </div>
  );
}
