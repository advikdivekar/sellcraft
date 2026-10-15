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
