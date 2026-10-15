"use client";
import { Home, Layers, Plus, Store } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cx } from "./ui";

const DESKTOP_NAV = [{ href: "/create", label: "Create" }, { href: "/connections", label: "Stores" }];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const showTabBar = path === "/" || path.startsWith("/connections");
  return (
    <>
      <header className="pt-safe sticky top-0 z-30 border-b border-border/70 bg-glass backdrop-blur-xl backdrop-saturate-150">
        <div className="mx-auto flex h-13 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex min-h-11 items-center gap-2 font-semibold tracking-tight" aria-label="SellCraft home">
            <span className="grid size-7 place-items-center rounded-[8px] bg-primary text-primary-fg"><Layers className="size-4" aria-hidden /></span>
            <span className="text-[15px]">SellCraft</span>
          </Link>
          <nav aria-label="Main" className="hidden items-center gap-1 sm:flex">
            {DESKTOP_NAV.map(({ href, label }) => (
              <Link key={href} href={href} aria-current={path.startsWith(href) ? "page" : undefined}
                className={cx("inline-flex min-h-10 items-center rounded-lg px-3 text-sm font-medium transition-colors", path.startsWith(href) ? "text-foreground" : "text-muted hover:text-foreground")}>{label}</Link>
            ))}
            <Link href="/create" className="ml-2 inline-flex min-h-10 items-center gap-1.5 rounded-[10px] bg-primary px-3.5 text-sm font-medium text-primary-fg transition hover:opacity-90 active:scale-[0.97]"><Plus className="size-4" aria-hidden />New kit</Link>
          </nav>
          <Link href="/connections" className="grid size-11 place-items-center rounded-full text-muted transition hover:bg-surface-2 sm:hidden" aria-label="Stores"><Store className="size-5" aria-hidden /></Link>
        </div>
      </header>
      <div className={cx("flex flex-1 flex-col", showTabBar && "pb-24 sm:pb-0")}>{children}</div>
      {showTabBar && (
        <nav aria-label="Primary" className="pb-safe fixed inset-x-0 bottom-0 z-30 border-t border-border/70 bg-glass px-6 pt-2 backdrop-blur-xl backdrop-saturate-150 sm:hidden">
          <ul className="mx-auto flex max-w-sm items-center justify-between">
            <TabItem href="/" icon={Home} label="Home" active={path === "/"} />
            <li><Link href="/create" aria-label="Create a kit" className="grid size-14 -translate-y-3 place-items-center rounded-full bg-primary text-primary-fg shadow-float ring-4 ring-background transition active:scale-95"><Plus className="size-6" aria-hidden /></Link></li>
            <TabItem href="/connections" icon={Store} label="Stores" active={path.startsWith("/connections")} />
          </ul>
        </nav>
      )}
    </>
  );
}

function TabItem({ href, icon: Icon, label, active }: { href: string; icon: typeof Home; label: string; active: boolean }) {
  return (
    <li>
      <Link href={href} aria-current={active ? "page" : undefined} className={cx("flex min-h-12 w-16 flex-col items-center justify-center gap-0.5 rounded-lg text-[11px] font-medium transition-colors", active ? "text-foreground" : "text-muted")}>
        <Icon className="size-5" aria-hidden />{label}
      </Link>
    </li>
  );
}
