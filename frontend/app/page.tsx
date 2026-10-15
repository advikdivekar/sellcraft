import Link from "next/link";
import { Camera, FileText, Film, ShieldCheck } from "lucide-react";
import { StatusBadge } from "@/components/status-badge";

const points = [
  { icon: Camera, title: "One photo, a few facts", body: "Add what you know. Anything you leave blank is flagged, never invented." },
  { icon: FileText, title: "Platform-ready copy", body: "Instagram, Facebook, Pinterest, Etsy or Shopify, each written for how that platform works." },
  { icon: Film, title: "A 10-second video ad", body: "Vertical 9:16, honestly labelled by how it was made." },
  { icon: ShieldCheck, title: "Runs on an open model", body: "Copy is written by Gemma on your own machine. Your product data stays with you." },
];

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-4 pb-safe pt-10 sm:px-6 sm:pt-16">
      <header className="space-y-4">
        <p className="text-sm font-semibold tracking-wide text-accent">SellCraft AI</p>
        <h1 className="text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
          One product photo.<br />A few facts.<br />A complete marketing kit.
        </h1>
        <p className="max-w-xl text-lg text-muted">
          Built for small sellers who are tired of rewriting the same product details for every platform.
        </p>
        <Link
          href="/create"
          className="inline-flex min-h-12 items-center justify-center rounded-xl bg-accent px-6 text-base font-medium text-white hover:opacity-90 dark:text-black"
        >
          Create marketing kit
        </Link>
      </header>

      <ul className="grid gap-3 sm:grid-cols-2">
        {points.map(({ icon: Icon, title, body }) => (
          <li key={title} className="rounded-2xl border border-border bg-surface p-4">
            <Icon className="mb-2 size-5 text-accent" aria-hidden />
            <h2 className="font-medium">{title}</h2>
            <p className="mt-1 text-sm text-muted">{body}</p>
          </li>
        ))}
      </ul>

      <div className="rounded-2xl border border-border bg-surface p-4">
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">AI engine</h2>
        <StatusBadge />
      </div>
    </main>
  );
}
