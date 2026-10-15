"use client";
import { AlertTriangle, Check } from "lucide-react";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { Button } from "./ui";

type Toast = { id: number; text: string; tone: "ok" | "error" };
type Ctx = { toast: (text: string, tone?: "ok" | "error") => void; confirm: (o: ConfirmOpts) => Promise<boolean> };
type ConfirmOpts = { title: string; body?: string; confirmLabel?: string; danger?: boolean };

const FeedbackCtx = createContext<Ctx | null>(null);
export const useFeedback = () => {
  const c = useContext(FeedbackCtx);
  if (!c) throw new Error("useFeedback must be used inside <FeedbackProvider>");
  return c;
};

export function FeedbackProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [dlg, setDlg] = useState<(ConfirmOpts & { resolve: (v: boolean) => void }) | null>(null);
  const ref = useRef<HTMLDialogElement>(null);
  const seq = useRef(0);

  const toast = useCallback((text: string, tone: "ok" | "error" = "ok") => {
    const id = ++seq.current;
    setToasts((t) => [...t.slice(-2), { id, text, tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), tone === "error" ? 5000 : 2200);
  }, []);
  const confirm = useCallback((o: ConfirmOpts) => new Promise<boolean>((resolve) => setDlg({ ...o, resolve })), []);

  useEffect(() => { if (dlg) ref.current?.showModal(); }, [dlg]);
  const close = (v: boolean) => { ref.current?.close(); dlg?.resolve(v); setDlg(null); };

  return (
    <FeedbackCtx.Provider value={{ toast, confirm }}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex flex-col items-center gap-2 px-4 pb-[max(5.5rem,env(safe-area-inset-bottom))] md:pb-8">
        {toasts.map((t) => (
          <div key={t.id} role="status" style={{ animation: "toast-in 0.2s ease-out both" }}
            className="pointer-events-auto flex max-w-sm items-center gap-2.5 rounded-full border border-border-strong bg-foreground px-4 py-2.5 text-sm font-medium text-background shadow-float">
            {t.tone === "ok" ? <Check className="size-4 text-ok" /> : <AlertTriangle className="size-4 text-danger" />}{t.text}
          </div>
        ))}
      </div>
      <dialog ref={ref} onCancel={() => close(false)} className="m-auto w-[calc(100%-2rem)] max-w-sm rounded-2xl border border-border bg-surface p-0 text-foreground shadow-float">
        {dlg && (
          <div className="space-y-4 p-5">
            <h2 className="text-lg font-semibold">{dlg.title}</h2>
            {dlg.body && <p className="text-sm text-muted">{dlg.body}</p>}
            <div className="flex justify-end gap-2 pt-1">
              <Button variant="ghost" size="sm" onClick={() => close(false)}>Cancel</Button>
              <Button variant={dlg.danger ? "danger" : "primary"} size="sm" onClick={() => close(true)} autoFocus>{dlg.confirmLabel ?? "Confirm"}</Button>
            </div>
          </div>
        )}
      </dialog>
    </FeedbackCtx.Provider>
  );
}
