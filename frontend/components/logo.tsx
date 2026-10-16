/* eslint-disable @next/next/no-img-element */
/** The Mochi logo: the ribbon mark on its dark-teal tile, plus the wordmark as live text so it stays crisp and theme-aware. */
export function Logo({ size = 32, word = true, className = "", tone = "auto" }: { size?: number; word?: boolean; className?: string; tone?: "auto" | "light" }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <img src="/mochi-tile.png" alt="" width={size} height={size} className="shrink-0 rounded-[28%] shadow-[0_6px_18px_-8px_rgb(0_49_53/.6)]" style={{ width: size, height: size }} />
      {word && <span className={`wordmark leading-none ${tone === "light" ? "text-[#F5F8F8]" : ""}`} style={{ fontSize: size * 0.72 }}>mochi</span>}
    </span>
  );
}
