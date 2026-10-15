import type { Objective, Platform, Tone, VisualStyle } from "./types";

export const PLATFORMS: { value: Platform; label: string }[] = [
  { value: "instagram", label: "Instagram" }, { value: "facebook", label: "Facebook" },
  { value: "pinterest", label: "Pinterest" }, { value: "etsy", label: "Etsy" }, { value: "shopify", label: "Shopify" },
];
export const TONES: { value: Tone; label: string }[] = [
  { value: "straightforward", label: "Straightforward" }, { value: "persuasive", label: "Persuasive" },
  { value: "emotional", label: "Emotional" }, { value: "friendly", label: "Friendly" },
  { value: "luxury", label: "Luxury" }, { value: "playful", label: "Playful" },
];
export const STYLES: { value: VisualStyle; label: string }[] = [
  { value: "premium_studio", label: "Premium studio" }, { value: "ugc", label: "UGC-style" },
  { value: "minimal", label: "Minimal" }, { value: "warm_cozy", label: "Warm & cozy" }, { value: "bold_colorful", label: "Bold & colorful" },
];
export const OBJECTIVES: { value: Objective; label: string }[] = [
  { value: "sales", label: "Drive sales" }, { value: "awareness", label: "Brand awareness" },
  { value: "gift", label: "Gift appeal" }, { value: "features", label: "Explain features" },
];


export type FieldKind = "str" | "list";
export interface SectionDef { key: string; label: string; kind: FieldKind; rows?: number }

export const LISTING_SECTIONS: SectionDef[] = [
  { key: "product_title", label: "Product title", kind: "str", rows: 2 },
  { key: "short_description", label: "Short description", kind: "str", rows: 3 },
  { key: "full_description", label: "Full description", kind: "str", rows: 7 },
  { key: "key_features", label: "Feature bullets", kind: "list" },
  { key: "benefits", label: "Benefits", kind: "list" },
  { key: "keywords", label: "Keywords", kind: "list" },
  { key: "tags", label: "Tags", kind: "list" },
  { key: "seo_title", label: "SEO title", kind: "str", rows: 2 },
  { key: "meta_description", label: "Meta description", kind: "str", rows: 3 },
];
export const SOCIAL_SECTIONS: SectionDef[] = [
  { key: "social_caption", label: "Social caption", kind: "str", rows: 5 },
  { key: "hashtags", label: "Hashtags", kind: "list" },
  { key: "ad_headline", label: "Headline", kind: "str", rows: 2 },
  { key: "call_to_action", label: "Call to action", kind: "str", rows: 2 },
];
export const VIDEO_SECTIONS: SectionDef[] = [
  { key: "video_hook", label: "Video hook", kind: "str", rows: 2 },
  { key: "voiceover_script", label: "Voiceover script", kind: "str", rows: 3 },
  { key: "video_generation_prompt", label: "Motion prompt", kind: "str", rows: 3 },
];

export const PLATFORM_FIELD_LABELS: Record<Platform, { key: string; label: string; kind: FieldKind; rows?: number }[]> = {
  instagram: [
    { key: "hook", label: "Hook", kind: "str", rows: 2 }, { key: "reel_caption", label: "Reel caption", kind: "str", rows: 5 },
    { key: "hashtags", label: "Hashtags", kind: "list" }, { key: "video_on_screen_text", label: "Video on-screen text", kind: "list" },
  ],
  facebook: [
    { key: "primary_text", label: "Primary text", kind: "str", rows: 5 }, { key: "headline", label: "Headline", kind: "str", rows: 2 },
    { key: "description", label: "Description", kind: "str", rows: 2 }, { key: "cta", label: "CTA", kind: "str", rows: 1 },
  ],
  pinterest: [
    { key: "pin_title", label: "Pin title", kind: "str", rows: 2 }, { key: "pin_description", label: "Pin description", kind: "str", rows: 5 },
    { key: "keyword_phrases", label: "Keyword phrases", kind: "list" },
  ],
  etsy: [
    { key: "title", label: "Listing title", kind: "str", rows: 2 }, { key: "item_description", label: "Item description", kind: "str", rows: 8 },
    { key: "tags", label: "Tags", kind: "list" }, { key: "attributes", label: "Attributes", kind: "list" },
  ],
  shopify: [
    { key: "page_copy", label: "Product page copy", kind: "str", rows: 8 }, { key: "feature_bullets", label: "Feature bullets", kind: "list" },
    { key: "seo_title", label: "SEO title", kind: "str", rows: 2 }, { key: "meta_description", label: "Meta description", kind: "str", rows: 3 },
  ],
};

export function methodLabel(method?: string | null): string {
  if (method === "studio_cutout")
    return "Studio-enhanced ad: your photos with the background replaced, re-lit and animated with camera moves. Not AI-generated footage.";
  if (method === "animated_photo")
    return "Animated-photo ad: your own photo on a designed backdrop with motion. Not AI-generated footage.";
  return method ? `AI-generated video (${method})` : "";
}

type Copy = import("./types").CopyOutput;
const s1 = (v: string | string[] | undefined) => (Array.isArray(v) ? v.join(" ") : (v ?? ""));
/** The post, exactly as a seller would paste it on that platform. */
export function postText(p: Platform, c: Copy): string {
  const o = c.platform_outputs[p] ?? {};
  const tags = (xs: string | string[] | undefined) => (Array.isArray(xs) ? xs.map((t) => (t.startsWith("#") ? t : `#${t}`)).join(" ") : "");
  switch (p) {
    case "instagram": return [s1(o.reel_caption) || c.social_caption, tags(o.hashtags as string[]) || tags(c.hashtags)].filter(Boolean).join("\n\n");
    case "facebook": return [s1(o.primary_text), s1(o.cta)].filter(Boolean).join("\n\n");
    case "pinterest": return [s1(o.pin_title), s1(o.pin_description), s1(o.keyword_phrases)].filter(Boolean).join("\n\n");
    case "etsy": return [s1(o.title), s1(o.item_description), "Tags: " + s1(o.tags)].filter(Boolean).join("\n\n");
    default: return [s1(o.page_copy), (Array.isArray(o.feature_bullets) ? o.feature_bullets.map((b) => `- ${b}`).join("\n") : "")].filter(Boolean).join("\n\n");
  }
}
