// Plain (non-client) module so server components can use the same classes as <Button>.
export function cx(...c: (string | false | null | undefined)[]) {
  return c.filter(Boolean).join(" ");
}

export type Variant = "primary" | "secondary" | "ghost" | "danger" | "accent";
export type Size = "lg" | "md" | "sm";

/** Class string shared by <Button> and anchors styled as buttons, so every action looks the same. */
export function buttonClass(variant: Variant = "primary", size: Size = "md", extra?: string) {
  return cx(
    "inline-flex select-none items-center justify-center gap-2 rounded-[10px] font-medium tracking-[-0.01em] transition duration-150 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-45 disabled:active:scale-100",
    size === "lg" && "min-h-13 px-6 text-base",
    size === "md" && "min-h-12 px-5 text-[15px]",
    size === "sm" && "min-h-11 px-3.5 text-sm",
    variant === "primary" && "bg-primary text-primary-fg shadow-card hover:opacity-90",
    variant === "accent" && "bg-accent text-accent-fg shadow-card hover:brightness-105",
    variant === "secondary" && "bg-surface text-foreground shadow-card ring-1 ring-border-strong hover:bg-surface-2",
    variant === "ghost" && "text-muted hover:bg-surface-2 hover:text-foreground",
    variant === "danger" && "bg-danger text-white hover:brightness-110",
    extra,
  );
}

