"use client";
import { Check, Copy, RefreshCw } from "lucide-react";
import { useLayoutEffect, useRef, useState } from "react";
import { copyText } from "@/lib/image";
import { Button } from "./ui";

type Value = string | string[];
const toText = (v: Value | undefined) => (Array.isArray(v) ? v.join("\n") : (v ?? ""));

export function EditableField({ label, value, kind, onCommit, onRegenerate, busy, locked }: {
  label: string; value: Value | undefined; kind: "str" | "list"; rows?: number; locked?: boolean;
  onCommit: (v: Value) => void; onRegenerate?: () => void; busy?: boolean;
}) {
  const [text, setText] = useState(toText(value));
  const [seen, setSeen] = useState(toText(value));
  const [copied, setCopied] = useState(false);
  const ref = useRef<HTMLTextAreaElement>(null);
  // Sync from the server value when it changes (regenerate / save), without an effect.
  if (toText(value) !== seen) { setSeen(toText(value)); setText(toText(value)); }

  // Grow to fit the content so nothing is clipped (matters on narrow phone screens).
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight + 2}px`;
  }, [text]);

  const commit = () => {
    if (text === toText(value)) return;
    onCommit(kind === "list" ? text.split("\n").map((s) => s.trim()).filter(Boolean) : text);
  };

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between gap-2">
        <label htmlFor={`f-${label}`} className="text-sm font-medium">{label}{kind === "list" && <span className="ml-1.5 text-xs font-normal text-muted">one per line</span>}</label>
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" aria-label={`Copy ${label}`} onClick={async () => { if (await copyText(text)) { setCopied(true); setTimeout(() => setCopied(false), 1500); } }}>
            {copied ? <Check className="size-4 text-ok" /> : <Copy className="size-4" />}<span className="hidden sm:inline">{copied ? "Copied" : "Copy"}</span>
          </Button>
          {onRegenerate && !locked && (
            <Button variant="ghost" size="sm" aria-label={`Regenerate ${label}`} busy={busy} onClick={onRegenerate}>
              {!busy && <RefreshCw className="size-4" />}<span className="hidden sm:inline">Regenerate</span>
            </Button>
          )}
        </div>
      </div>
      <textarea
        id={`f-${label}`} ref={ref} value={text} rows={2} readOnly={locked} placeholder={locked ? "Writing…" : undefined} aria-busy={locked && !text} onChange={(e) => setText(e.target.value)} onBlur={commit}
        className={`w-full resize-none rounded-[10px] bg-surface px-3.5 py-3 leading-relaxed shadow-card ring-1 ring-border-strong transition hover:ring-foreground/30 focus:outline-none focus:ring-2 focus:ring-foreground ${locked && !text ? "animate-pulse" : ""}`}
      />
    </div>
  );
}
