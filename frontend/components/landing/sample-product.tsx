/** An abstract sample "product" (a matte ceramic sphere on a plinth with a terracotta band), drawn in SVG. It stands in for a product
 *  photograph: there are no stock photos in this repo, and the page labels it as a sample. */
export function SampleProduct({ className, id = "sp" }: { className?: string; tint?: "amber" | "stone"; id?: string }) {
  const u = (n: string) => `${id}-${n}`;
  return (
    <svg viewBox="0 0 400 500" role="img" aria-label="Sample product: a matte ceramic sphere on a plinth" className={className} preserveAspectRatio="xMidYMid slice">
      <defs>
        <radialGradient id={u("bg")} cx=".5" cy=".42" r=".8"><stop offset="0" stopColor="#F2F9FA" /><stop offset=".7" stopColor="#CFE6EA" /><stop offset="1" stopColor="#A9CDD3" /></radialGradient>
        <radialGradient id={u("sph")} cx=".34" cy=".28" r=".85"><stop offset="0" stopColor="#ffffff" /><stop offset=".22" stopColor="#e3f3f5" /><stop offset=".55" stopColor="#a7d3da" /><stop offset=".85" stopColor="#5b9ea9" /><stop offset="1" stopColor="#2e7580" /></radialGradient>
        <radialGradient id={u("shade")} cx=".72" cy=".78" r=".7"><stop offset="0" stopColor="#003135" stopOpacity=".5" /><stop offset=".7" stopColor="#003135" stopOpacity="0" /></radialGradient>
        <linearGradient id={u("rim")} x1="0" y1="0" x2="1" y2="0"><stop offset=".7" stopColor="#0FA4AF" stopOpacity="0" /><stop offset="1" stopColor="#0FA4AF" stopOpacity=".55" /></linearGradient>
        <linearGradient id={u("plinth")} x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor="#01363b" /><stop offset=".35" stopColor="#0b6a74" /><stop offset=".7" stopColor="#035560" /><stop offset="1" stopColor="#012a2e" /></linearGradient>
        <linearGradient id={u("band")} x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor="#6e3223" /><stop offset=".4" stopColor="#b55a43" /><stop offset=".75" stopColor="#964734" /><stop offset="1" stopColor="#5f2b1e" /></linearGradient>
        <filter id={u("soft")}><feGaussianBlur stdDeviation="3" /></filter>
        <filter id={u("blur")}><feGaussianBlur stdDeviation="9" /></filter>
      </defs>
      <rect width="400" height="500" fill={`url(#${u("bg")})`} />
      <rect y="410" width="400" height="90" fill="#9CC4CB" opacity=".5" />
      <ellipse cx="200" cy="416" rx="120" ry="12" fill="#003135" opacity=".3" filter={`url(#${u("blur")})`} />
      <g transform="translate(32 -27) scale(1.4)">
        <path d="M44 262 V300 Q44 313 120 313 Q196 313 196 300 V262 Z" fill={`url(#${u("plinth")})`} />
        <path d="M44 289 V298 Q44 311 120 311 Q196 311 196 298 V289 Q196 300 120 300 Q44 300 44 289 Z" fill={`url(#${u("band")})`} />
        <ellipse cx="120" cy="262" rx="76" ry="15" fill="#0b6a74" /><ellipse cx="120" cy="262" rx="76" ry="15" fill="none" stroke="#AFDDE5" strokeOpacity=".35" strokeWidth="1" />
        <ellipse cx="124" cy="258" rx="46" ry="8" fill="#001d21" opacity=".55" filter={`url(#${u("soft")})`} />
        <circle cx="120" cy="170" r="86" fill={`url(#${u("sph")})`} />
        <circle cx="120" cy="170" r="86" fill={`url(#${u("shade")})`} />
        <circle cx="120" cy="170" r="86" fill={`url(#${u("rim")})`} />
        <ellipse cx="92" cy="122" rx="26" ry="15" fill="#fff" opacity=".7" transform="rotate(-32 92 122)" filter={`url(#${u("soft")})`} />
      </g>
    </svg>
  );
}
