"use client";
import { Check, Copy, RefreshCw } from "lucide-react";
import { useState } from "react";
import { copyText } from "@/lib/image";
import { Button } from "./ui";

type Value = string | string[];
const toText = (v: Value | undefined) => (Array.isArray(v) ? v.join("\n") : (v ?? ""));

export function EditableField({ label, value, kind, rows = 3, onCommit, onRegenerate, busy }: {
  label: string; value: Value | undefined; kind: "str" | "list"; rows?: number;
  onCommit: (v: Value) => void; onRegenerate?: () => void; busy?: boolean;
}) {
  const [text, setText] = useState(toText(value));
  const [seen, setSeen] = useState(toText(value));
  const [copied, setCopied] = useState(false);
  // Sync from the server value when it changes (regenerate / save), without an effect.
  if (toText(value) !== seen) { setSeen(toText(value)); setText(toText(value)); }

  const commit = () => {
    if (text === toText(value)) return;
    onCommit(kind === "list" ? text.split("\n").map((s) => s.trim()).filter(Boolean) : text);
  };
  const lineRows = kind === "list" ? Math.max(rows, Math.min(text.split("\n").length + 1, 10)) : rows;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between gap-2">
        <label htmlFor={`f-${label}`} className="text-sm font-medium">{label}{kind === "list" && <span className="ml-1.5 text-xs font-normal text-muted">one per line</span>}</label>
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" aria-label={`Copy ${label}`} onClick={async () => { if (await copyText(text)) { setCopied(true); setTimeout(() => setCopied(false), 1500); } }}>
            {copied ? <Check className="size-4 text-ok" /> : <Copy className="size-4" />}<span className="hidden sm:inline">{copied ? "Copied" : "Copy"}</span>
          </Button>
          {onRegenerate && (
            <Button variant="ghost" size="sm" aria-label={`Regenerate ${label}`} busy={busy} onClick={onRegenerate}>
              {!busy && <RefreshCw className="size-4" />}<span className="hidden sm:inline">Regenerate</span>
            </Button>
          )}
        </div>
      </div>
      <textarea
        id={`f-${label}`} value={text} rows={lineRows} onChange={(e) => setText(e.target.value)} onBlur={commit}
        className="w-full resize-y rounded-xl border border-border bg-background px-3.5 py-3 leading-relaxed focus:border-accent"
      />
    </div>
  );
}
