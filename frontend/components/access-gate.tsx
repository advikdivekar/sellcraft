"use client";
import { useEffect, useState } from "react";
import { Button, Card, inputCls } from "./ui";

type State = "loading" | "open" | "needcode";
const DEMO_ONLY = process.env.NEXT_PUBLIC_DEMO_ONLY === "1"; // public landing build: there is no backend to ask

/** When the backend has an ACCESS_CODE (phone/tunnel mode), ask for it once. A `#k=code` in the URL (from the QR) signs in automatically. */
export function AccessGate({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<State>(DEMO_ONLY ? "open" : "loading");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (DEMO_ONLY) return;
    (async () => {
      const m = window.location.hash.match(/[#&]k=([^&]+)/);
      if (m) {
        await fetch("/api/access", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code: decodeURIComponent(m[1]) }) }).catch(() => {});
        window.history.replaceState(null, "", window.location.pathname + window.location.search);
      }
      const r = await fetch("/api/access").then((x) => x.json()).catch(() => null);
      // The public landing page never asks for the code; only the app screens do (the API itself stays locked either way).
      setState(window.location.pathname === "/" || !r || !r.required || r.granted ? "open" : "needcode");
    })();
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const r = await fetch("/api/access", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code }) });
    if (r.ok) setState("open"); else setError("That code isn't right.");
  }

  if (state === "loading") return <p className="p-6 text-muted">Loading…</p>;
  if (state === "needcode")
    return (
      <main className="mx-auto w-full max-w-sm flex-1 px-4 pt-16">
        <Card>
          <form onSubmit={submit} className="space-y-4">
            <h1 className="text-xl font-semibold">Enter access code</h1>
            <p className="text-sm text-muted">This SellCraft is shared over the internet, so it needs the code shown where it was started (or scan its QR code).</p>
            <input className={inputCls} value={code} onChange={(e) => setCode(e.target.value)} autoComplete="off" autoCapitalize="off" aria-label="Access code" />
            {error && <p role="alert" className="text-sm text-danger">{error}</p>}
            <Button type="submit" className="w-full">Continue</Button>
          </form>
        </Card>
      </main>
    );
  return <>{children}</>;
}
