"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Lock, Share2, Store, Unplug } from "lucide-react";
import { useState } from "react";
import { Badge, Button, Card, Field, inputCls } from "@/components/ui";
import { ApiError, api } from "@/lib/api";

export default function ConnectionsPage() {
  const qc = useQueryClient();
  const conns = useQuery({ queryKey: ["connections"], queryFn: api.connections });
  const shopify = conns.data?.find((c) => c.provider === "shopify");
  const [domain, setDomain] = useState("");
  const [token, setToken] = useState("");

  const refresh = () => { qc.invalidateQueries({ queryKey: ["connections"] }); qc.invalidateQueries({ queryKey: ["status"] }); };
  const connect = useMutation({ mutationFn: () => api.connectShopify(domain, token), onSuccess: () => { setToken(""); setDomain(""); refresh(); } });
  const disconnect = useMutation({ mutationFn: api.disconnectShopify, onSuccess: refresh });
  const err = (connect.error ?? disconnect.error) as ApiError | null;

  return (
    <main className="mx-auto w-full max-w-2xl flex-1 space-y-5 px-4 pb-safe pt-6 sm:px-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Connect your stores</h1>
        <p className="mt-1 text-muted">Connect once, then send finished kits to your store from the results page. Nothing is ever published without you tapping a button.</p>
      </header>

      <Card className="space-y-4">
        <div className="flex items-center gap-3">
          <Store className="size-5 text-accent-text" aria-hidden />
          <h2 className="font-medium">Shopify</h2>
          {shopify?.connected && <Badge tone="ok" className="ml-auto"><Check className="size-3.5" />Connected</Badge>}
        </div>

        {shopify?.connected ? (
          <div className="space-y-3">
            <p className="text-sm">{shopify.label}</p>
            {shopify.source === "env"
              ? <p className="text-xs text-muted">Connected through the server settings (<code>backend/.env</code>). Remove it there to disconnect.</p>
              : <Button variant="secondary" size="sm" busy={disconnect.isPending} onClick={() => { if (window.confirm("Disconnect this Shopify store?")) disconnect.mutate(); }}><Unplug className="size-4" />Disconnect</Button>}
          </div>
        ) : (
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); connect.mutate(); }}>
            <Field label="Store address" hint="Your .myshopify.com address, like my-store.myshopify.com">
              <input className={inputCls} value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="my-store.myshopify.com" autoCapitalize="off" autoCorrect="off" autoComplete="off" inputMode="url" />
            </Field>
            <Field label="Admin API access token" hint="Starts with shpat_. It's encrypted on this computer and never shown again.">
              <input className={inputCls} type="password" value={token} onChange={(e) => setToken(e.target.value)} autoComplete="off" autoCapitalize="off" placeholder="shpat_…" />
            </Field>
            <Button type="submit" busy={connect.isPending} disabled={!domain.trim() || !token.trim()}><Lock className="size-4" />Connect Shopify</Button>
            <details className="rounded-xl border border-border px-3.5 py-2 text-sm">
              <summary className="min-h-11 cursor-pointer list-none py-2.5 font-medium">How to get the token (about 2 minutes, free)</summary>
              <ol className="list-decimal space-y-1.5 pb-3 pl-5 text-muted">
                <li>No store yet? Create a free development store at partners.shopify.com.</li>
                <li>In your store admin: <strong>Settings &gt; Apps and sales channels &gt; Develop apps &gt; Create an app</strong>.</li>
                <li>Open <strong>Configuration</strong> and under Admin API integration select the scope <strong>write_products</strong>, then save.</li>
                <li>Click <strong>Install app</strong>, then reveal and copy the <strong>Admin API access token</strong> (shown once).</li>
                <li>Paste the store address and token above.</li>
              </ol>
            </details>
          </form>
        )}
        {err && <p role="alert" className="rounded-xl border border-danger/40 bg-danger/10 p-3 text-sm text-danger">{err.message}</p>}
        <p className="text-xs text-muted">Products are created as <strong>drafts</strong> with your studio photos and video, description, tags and SEO. You review and publish them in Shopify.</p>
      </Card>

      <Card className="space-y-2">
        <div className="flex items-center gap-3"><Share2 className="size-5 text-accent-text" aria-hidden /><h2 className="font-medium">Instagram, Facebook, WhatsApp, Pinterest</h2></div>
        <p className="text-sm text-muted">No connection needed. On the results page, <strong>Share video + caption</strong> opens your phone&apos;s share sheet with the video and the caption ready, and <strong>Copy post</strong> copies the text formatted for each platform.</p>
        <p className="text-xs text-muted">Direct posting to these platforms and to Etsy requires each platform&apos;s developer approval, so it isn&apos;t available yet.</p>
      </Card>
    </main>
  );
}
