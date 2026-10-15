"use client";
import { AlertTriangle, Check } from "lucide-react";
import { createContext, useCallback, useContext, useRef, useState } from "react";
import { Button, Sheet } from "./ui";

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
  const seq = useRef(0);

  const toast = useCallback((text: string, tone: "ok" | "error" = "ok") => {
    const id = ++seq.current;
    setToasts((t) => [...t.slice(-2), { id, text, tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), tone === "error" ? 5000 : 2200);
  }, []);
  const confirm = useCallback((o: ConfirmOpts) => new Promise<boolean>((resolve) => setDlg({ ...o, resolve })), []);

  const close = (v: boolean) => { dlg?.resolve(v); setDlg(null); };

  return (
    <FeedbackCtx.Provider value={{ toast, confirm }}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex flex-col items-center gap-2 px-4 pb-[max(5.5rem,env(safe-area-inset-bottom))] md:pb-8">
        {toasts.map((t) => (
          <div key={t.id} role="status" style={{ animation: "toast-in 0.2s ease-out both" }}
            className="pointer-events-auto flex max-w-sm items-center gap-2.5 rounded-full bg-primary px-4 py-2.5 text-sm font-medium text-primary-fg shadow-float">
            {t.tone === "ok" ? <Check className="size-4 text-ok" aria-hidden /> : <AlertTriangle className="size-4 text-danger" aria-hidden />}{t.text}
          </div>
        ))}
      </div>
      <Sheet open={!!dlg} onClose={() => close(false)} title={dlg?.title ?? ""}>
        {dlg && (
          <div className="space-y-5">
            {dlg.body && <p className="text-[15px] text-muted">{dlg.body}</p>}
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Button variant="secondary" onClick={() => close(false)}>Cancel</Button>
              <Button variant={dlg.danger ? "danger" : "primary"} onClick={() => close(true)}>{dlg.confirmLabel ?? "Confirm"}</Button>
            </div>
          </div>
        )}
      </Sheet>
    </FeedbackCtx.Provider>
  );
}
