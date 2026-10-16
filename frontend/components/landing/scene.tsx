/** The hero landscape: still teal water, layered mountains, a low sun, and the product standing in still water. Pure SVG, no image
 *  files. The product is an abstract sample object; nothing here pretends to be a photograph. */
export function HeroScene({ portrait = false, className = "" }: { portrait?: boolean; className?: string }) {
  const sunX = portrait ? 900 : 560;
  const i = portrait ? "p" : "d"; // unique gradient ids per instance: hidden SVGs do not render their <defs>
  return (
    <svg className={`mochi-scene absolute inset-0 size-full ${className}`} viewBox={portrait ? "700 120 680 780" : "0 0 1600 900"} preserveAspectRatio="xMidYMax slice" aria-hidden>
      <defs>
        <linearGradient id={`hs-sky-${i}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#06545c" /><stop offset=".45" stopColor="#2a9aa5" /><stop offset=".78" stopColor="#8fd3da" /><stop offset="1" stopColor="#cdeaee" /></linearGradient>
        <radialGradient id={`hs-sun-${i}`} cx=".5" cy=".5" r=".5"><stop offset="0" stopColor="#F5F8F8" stopOpacity=".95" /><stop offset=".25" stopColor="#E6F6F8" stopOpacity=".5" /><stop offset="1" stopColor="#AFDDE5" stopOpacity="0" /></radialGradient>
        <linearGradient id={`hs-far-${i}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#5bb4be" /><stop offset="1" stopColor="#8ccfd6" /></linearGradient>
        <linearGradient id={`hs-mid-${i}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#1d8791" /><stop offset="1" stopColor="#3fa3ad" /></linearGradient>
        <linearGradient id={`hs-near-${i}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#0a5963" /><stop offset="1" stopColor="#0b6a73" /></linearGradient>
        <linearGradient id={`hs-rock-${i}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#043c43" /><stop offset="1" stopColor="#012c31" /></linearGradient>
        <linearGradient id={`hs-water-${i}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#3b9aa4" /><stop offset=".25" stopColor="#0d6a74" /><stop offset=".7" stopColor="#024049" /><stop offset="1" stopColor="#002a2f" /></linearGradient>
        <linearGradient id={`hs-fade-${i}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#fff" stopOpacity=".5" /><stop offset="1" stopColor="#fff" stopOpacity="0" /></linearGradient>
        <mask id={`hs-refl-${i}`}><rect x="840" y="716" width="400" height="190" fill={`url(#hs-fade-${i})`} /></mask>
        <filter id={`hs-soft-${i}`}><feGaussianBlur stdDeviation="2.2" /></filter>
        <filter id={`hs-blur-${i}`}><feGaussianBlur stdDeviation="14" /></filter>
      </defs>
      <rect width="1600" height="900" fill={`url(#hs-sky-${i})`} />
      <circle cx={sunX} cy="190" r="190" fill={`url(#hs-sun-${i})`} />
      <circle cx={sunX} cy="190" r="20" fill="#F5F8F8" />
      <path d="M0 520 L120 470 L210 500 L330 430 L450 505 L560 470 L700 520 L860 480 L1000 515 L1180 470 L1330 510 L1480 450 L1600 500 V560 H0 Z" fill={`url(#hs-far-${i})`} opacity=".7" />
      <path d="M0 560 L150 440 L230 480 L330 400 L430 470 L520 520 L640 560 L800 575 L960 560 L1100 520 L1230 560 V600 H0 Z" fill={`url(#hs-mid-${i})`} opacity=".92" />
      <path d="M0 600 L0 380 L80 330 L160 410 L260 360 L380 470 L520 560 L640 600 Z" fill={`url(#hs-near-${i})`} />
      <path d="M1600 600 L1600 120 L1500 20 L1420 140 L1340 200 L1250 330 L1130 470 L1010 560 L920 600 Z" fill={`url(#hs-near-${i})`} />
      <path d="M1600 600 L1600 300 L1520 360 L1440 330 L1370 420 L1290 470 L1200 560 L1130 600 Z" fill="#075a64" opacity=".85" />
      <rect y="590" width="1600" height="310" fill={`url(#hs-water-${i})`} />
      <g opacity=".5" filter={`url(#hs-soft-${i})`} transform="translate(0 1190) scale(1 -1)"><path d="M0 600 L0 380 L80 330 L160 410 L260 360 L380 470 L520 560 L640 600 Z" fill="#0a5963" opacity=".6" /><path d="M1600 600 L1600 120 L1500 20 L1420 140 L1340 200 L1250 330 L1130 470 L1010 560 L920 600 Z" fill="#0a5963" opacity=".6" /></g>
      <rect y="590" width="1600" height="310" fill={`url(#hs-water-${i})`} opacity=".55" />
      <rect x={sunX - 30} y="600" width="60" height="300" fill="#E6F6F8" opacity=".18" filter={`url(#hs-blur-${i})`} />
      <path d="M0 900 L0 760 L110 720 L230 770 L330 740 L420 800 L520 900 Z" fill={`url(#hs-rock-${i})`} />
      <path d="M1600 900 L1600 740 L1500 700 L1400 760 L1290 740 L1190 810 L1100 900 Z" fill={`url(#hs-rock-${i})`} />
      <g fill="none" stroke="#AFDDE5" strokeWidth="1.4">
        <ellipse cx="1040" cy="715" rx="140" ry="22" opacity=".5" /><ellipse cx="1040" cy="715" rx="210" ry="33" opacity=".34" />
        <ellipse cx="1040" cy="715" rx="290" ry="46" opacity=".22" /><ellipse cx="1040" cy="715" rx="380" ry="60" opacity=".12" />
      </g>
      <ellipse cx="1040" cy="712" rx="112" ry="12" fill="#00282C" opacity=".6" filter={`url(#hs-soft-${i})`} />
      <g mask={`url(#hs-refl-${i})`}><image href="/sample-product-cutout.svg" x="890" y="411" width="300" height="305" transform="translate(0 1432) scale(1 -1)" opacity=".5" /></g>
      <image href="/sample-product-cutout.svg" x="890" y="411" width="300" height="305" />
    </svg>
  );
}
