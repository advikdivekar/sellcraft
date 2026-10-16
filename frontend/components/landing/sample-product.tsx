/** An original illustration of the sample product (a candle jar), drawn in SVG. It stands in for a product photograph:
 *  there are no stock photos in this repo, and the page labels it as a sample. */
export function SampleProduct({ className, tint = "amber", id = "sp" }: { className?: string; tint?: "amber" | "stone"; id?: string }) {
  const glass = tint === "amber" ? ["#e0a14a", "#a96a1c", "#5d3510"] : ["#d8d4c8", "#a9a496", "#6f6b5f"];
  return (
    <svg viewBox="0 0 400 500" role="img" aria-label="Sample product: an amber glass candle jar" className={className} preserveAspectRatio="xMidYMid slice">
      <defs>
        <linearGradient id={`${id}-bg`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#ece6d8" /><stop offset="1" stopColor="#cfc6b2" /></linearGradient>
        <linearGradient id={`${id}-glass`} x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor={glass[2]} /><stop offset=".28" stopColor={glass[0]} /><stop offset=".6" stopColor={glass[1]} /><stop offset="1" stopColor={glass[2]} /></linearGradient>
        <linearGradient id={`${id}-wax`} x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor="#d9cfb8" /><stop offset=".5" stopColor="#f3ecd9" /><stop offset="1" stopColor="#cbbfa2" /></linearGradient>
        <radialGradient id={`${id}-glow`} cx=".5" cy=".4" r=".6"><stop offset="0" stopColor="#fff6d6" stopOpacity=".9" /><stop offset="1" stopColor="#fff6d6" stopOpacity="0" /></radialGradient>
        <filter id={`${id}-blur`}><feGaussianBlur stdDeviation="9" /></filter>
      </defs>
      <rect width="400" height="500" fill={`url(#${id}-bg)`} />
      <ellipse cx="200" cy="418" rx="118" ry="16" fill="#000" opacity=".28" filter={`url(#${id}-blur)`} />
      <rect x="0" y="410" width="400" height="90" fill="#bdb29a" opacity=".35" />
      <path d="M96 190 Q96 178 108 178 H292 Q304 178 304 190 V396 Q304 416 284 416 H116 Q96 416 96 396 Z" fill={`url(#${id}-glass)`} />
      <ellipse cx="200" cy="178" rx="104" ry="14" fill={`url(#${id}-wax)`} />
      <ellipse cx="200" cy="180" rx="92" ry="9" fill="#efe7d0" />
      <rect x="198" y="150" width="4" height="30" rx="2" fill="#2a2118" />
      <ellipse cx="200" cy="136" rx="26" ry="34" fill={`url(#${id}-glow)`} />
      <path d="M200 118 Q211 136 200 152 Q189 136 200 118 Z" fill="#ffb938" /><path d="M200 130 Q205 140 200 150 Q195 140 200 130 Z" fill="#fff4c9" />
      <rect x="132" y="262" width="136" height="96" rx="6" fill="#f4efe2" opacity=".94" />
      <text x="200" y="298" textAnchor="middle" fontFamily="Georgia, serif" fontStyle="italic" fontSize="22" fill="#2a2118">Cedar &amp; Fig</text>
      <line x1="156" y1="312" x2="244" y2="312" stroke="#2a2118" strokeWidth="1" opacity=".5" />
      <text x="200" y="334" textAnchor="middle" fontFamily="Arial, sans-serif" fontSize="9.5" letterSpacing="2.4" fill="#5b4f3d">SOY WAX CANDLE</text>
      <rect x="112" y="196" width="14" height="196" rx="7" fill="#fff" opacity=".22" />
    </svg>
  );
}
