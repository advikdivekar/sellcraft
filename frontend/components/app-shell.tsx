"use client";
import { Layers, Sparkles, Store } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cx } from "./ui";

const NAV = [
  { href: "/create", label: "Create", icon: Sparkles },
  { href: "/connections", label: "Stores", icon: Store },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <>
      <header className="pt-safe sticky top-0 z-30 border-b border-border/80 bg-background/85 backdrop-blur-md">
        <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex min-h-11 items-center gap-2.5 font-semibold tracking-tight" aria-label="SellCraft home">
            <span className="grid size-8 place-items-center rounded-[10px] bg-accent text-accent-fg shadow-card"><Layers className="size-4" aria-hidden /></span>
            <span>SellCraft<span className="text-accent"> AI</span></span>
          </Link>
          <nav aria-label="Main" className="flex items-center gap-1">
            {NAV.map(({ href, label, icon: Icon }) => (
              <Link key={href} href={href} aria-current={path.startsWith(href) ? "page" : undefined}
                className={cx("inline-flex min-h-11 items-center gap-1.5 rounded-xl px-3 text-sm font-medium transition-colors",
                  path.startsWith(href) ? "bg-accent-soft text-accent" : "text-muted hover:bg-surface-2 hover:text-foreground")}>
                <Icon className="size-4" aria-hidden />{label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <div className="flex flex-1 flex-col">{children}</div>
    </>
  );
}
