/** Demo-mode copy for the landing page. Deterministic templates over the facts the visitor typed: no model is called and
 *  nothing is invented. Anything not in the facts is listed as "not provided", mirroring what the real app does. */
export type Platform = "instagram" | "facebook" | "pinterest" | "etsy" | "shopify";
export type Tone = "luxury" | "persuasive" | "emotional" | "playful" | "minimal" | "professional";

export const PLATFORMS: { value: Platform; label: string }[] = [
  { value: "instagram", label: "Instagram" }, { value: "facebook", label: "Facebook" }, { value: "pinterest", label: "Pinterest" },
  { value: "etsy", label: "Etsy" }, { value: "shopify", label: "Shopify" },
];
export const TONES: { value: Tone; label: string }[] = [
  { value: "luxury", label: "Luxury" }, { value: "persuasive", label: "Persuasive" }, { value: "emotional", label: "Emotional" },
  { value: "playful", label: "Playful" }, { value: "minimal", label: "Minimal" }, { value: "professional", label: "Professional" },
];

export const SAMPLE = {
  name: "Orb Desk Object",
  details: "Matte ceramic sphere\n9 cm diameter\nTerracotta band on the base\nSold as a single piece",
};

export interface Beat { t: string; label: string; text: string }
export interface Kit {
  title: string; description: string; tags: string[]; caption: string; hashtags: string[]; cta: string;
  beats: Beat[]; hook: string; missing: string[]; facts: string[];
}

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const strip = (s: string) => s.replace(/[.\s]+$/, "");
const lc = (s: string) => (s.length > 1 && s[1] === s[1].toLowerCase() ? s.charAt(0).toLowerCase() + s.slice(1) : s);

export function parseFacts(details: string): string[] {
  return details.split(/[\n;]|,(?!\d)/).map((s) => strip(s.trim())).filter(Boolean).slice(0, 8);
}
function words(s: string) { return s.toLowerCase().replace(/[^a-z0-9\s-]/g, " ").split(/\s+/).filter((w) => w.length > 2); }
const STOP = new Set(["and", "the", "for", "with", "has", "are", "our", "your", "made", "from"]);

export function generate(name: string, details: string, platform: Platform, tone: Tone): Kit {
  const n = name.trim() || "Your product";
  const facts = parseFacts(details);
  const [a, b, c, d] = facts;
  const list = (k: number) => facts.slice(0, k).map((f) => cap(f) + ".").join(" ");
  const hasPrice = /[$£€₹]|\b\d+(\.\d+)?\s?(usd|eur|gbp|inr)\b/i.test(details);
  const missing = [...(hasPrice ? [] : ["Price"]), ...(facts.length < 2 ? ["More facts (materials, size, who it's for)"] : [])];

  const description: Record<Tone, string> = {
    luxury: `${n}. Quietly considered. ${list(4) || "Add a few facts to see the copy take shape."}`,
    persuasive: `${n} is the one to pick up first. ${a ? `${cap(a)}.` : ""} ${b ? `${cap(b)}.` : ""} ${c ? `${cap(c)}.` : ""} Add it to your cart before it sells out of your day.`.replace(" Add it to your cart before it sells out of your day.", " Add it to your cart today."),
    emotional: `Some things are made to be held. ${n}: ${[a, b, c].filter(Boolean).map(lc).join(", ") || "tell us a little about it"}. Yours to enjoy, or to give.`,
    playful: `Meet ${n}! ${a ? `${cap(a)}.` : ""} ${b ? `${cap(b)}.` : ""} ${c ? `Plus: ${lc(c)}.` : ""} Small thing, big smile.`,
    minimal: `${n}. ${[a, b, c, d].filter(Boolean).map(cap).join(". ")}${facts.length ? "." : ""}`,
    professional: `${n} is described below using the details supplied. ${list(5) || "No product details supplied."}`,
  };
  const caption: Record<Tone, string> = {
    luxury: `${n}. ${a ? cap(a) + "." : ""} ${b ? cap(b) + "." : ""}`,
    persuasive: `Why wait? ${n}: ${[a, b].filter(Boolean).map(lc).join(" and ") || "see details"}. Link in bio.`,
    emotional: `For the moments you want to keep. ${n}. ${a ? cap(a) + "." : ""}`,
    playful: `New in: ${n}! ${a ? cap(a) + "." : ""} ${b ? cap(b) + "." : ""} Tell us your favourite.`,
    minimal: `${n}. ${a ? cap(a) + "." : ""}`,
    professional: `Now available: ${n}. ${[a, b].filter(Boolean).map(cap).join(". ")}${a ? "." : ""}`,
  };
  const ctaByPlatform: Record<Platform, string> = {
    instagram: "Link in bio", facebook: "Shop now", pinterest: "Save for later", etsy: "Add to cart", shopify: "Add to cart",
  };
  const base = [...new Set([...words(n), ...facts.flatMap(words)])].filter((w) => !STOP.has(w));
  const tagMax: Record<Platform, number> = { instagram: 8, facebook: 5, pinterest: 10, etsy: 13, shopify: 8 };
  const tags = base.slice(0, tagMax[platform]);
  const title: Record<Platform, string> = {
    instagram: n, facebook: n, pinterest: `${n}${a ? `, ${lc(a)}` : ""}`,
    etsy: [n, a && cap(a), b && cap(b)].filter(Boolean).join(" | "), shopify: `${n}${a ? `: ${lc(a)}` : ""}`,
  };
  const first = (s?: string) => (s ? cap(s) : "Add your facts");
  return {
    title: title[platform], description: description[tone].replace(/\s+/g, " ").trim(), tags,
    caption: caption[tone].replace(/\s+/g, " ").trim(), hashtags: tags.slice(0, 6).map((t) => "#" + t.replace(/-/g, "")),
    cta: ctaByPlatform[platform], hook: tone === "playful" ? `Meet ${n}!` : tone === "luxury" ? `${n}.` : `${n}, up close`,
    beats: [
      { t: "0–2s", label: "Hook", text: tone === "playful" ? `Meet ${n}!` : n },
      { t: "2–5s", label: "Showcase", text: first(a) },
      { t: "5–8s", label: "Feature", text: first(b ?? a) },
      { t: "8–10s", label: "Call to action", text: ctaByPlatform[platform] },
    ],
    missing, facts,
  };
}

export function platformBlurb(p: Platform): string {
  return { instagram: "Reel caption, hook and hashtags", facebook: "Primary text, headline and CTA", pinterest: "Pin title, description and keywords",
    etsy: "Keyword title, description and 13 tags", shopify: "Product title, description, tags and SEO" }[p];
}
