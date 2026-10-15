export type Platform = "instagram" | "facebook" | "pinterest" | "etsy" | "shopify";
export type Tone = "straightforward" | "persuasive" | "emotional" | "friendly" | "luxury" | "playful";
export type VisualStyle = "premium_studio" | "ugc" | "minimal" | "warm_cozy" | "bold_colorful";
export type Objective = "sales" | "awareness" | "gift" | "features";
export type JobStatus =
  | "queued" | "generating_copy" | "generating_video" | "generating_voiceover"
  | "assembling_video" | "completed" | "failed";

export interface ProductInput {
  name: string;
  image_asset_ids: string[];
  summary?: string | null;
  price?: string | null;
  currency?: string | null;
  materials?: string | null;
  dimensions?: string | null;
  features: string[];
  benefits: string[];
  audience?: string | null;
  brand_name?: string | null;
  brand_voice?: string | null;
  care_instructions?: string | null;
  extra_notes?: string | null;
  forbidden_words: string[];
}

export interface CreativeSettings {
  platforms: Platform[];
  tone: Tone;
  visual_style: VisualStyle;
  objective: Objective;
  duration_seconds: number;
  aspect_ratio: string;
  voiceover: boolean;
  voice_id?: string | null;
}

export interface StoryBeat { time: string; visual: string; on_screen_text: string }

export interface CopyOutput {
  product_title: string;
  short_description: string;
  full_description: string;
  key_features: string[];
  benefits: string[];
  target_audience: string;
  call_to_action: string;
  seo_title: string;
  meta_description: string;
  keywords: string[];
  tags: string[];
  social_caption: string;
  hashtags: string[];
  ad_headline: string;
  voiceover_script: string;
  video_hook: string;
  video_storyboard: StoryBeat[];
  video_generation_prompt: string;
  missing_information: string[];
  claims_requiring_review: string[];
  platform_outputs: Record<string, Record<string, string | string[]>>;
}

export interface StageEntry { name: string; status: "running" | "done" | "skipped" | "failed"; detail?: string | null; notes: string[]; progress: number }
export interface GeneratedAsset { id: string; kind: string; mime: string; method?: string | null; duration_seconds?: number | null }

export interface GenerationJob {
  id: string;
  status: JobStatus;
  product: ProductInput;
  settings: CreativeSettings;
  copy_output: CopyOutput | null;
  copy_source: string | null;
  error: { code: string; message: string; retryable: boolean } | null;
  stages: StageEntry[];
  assets: GeneratedAsset[];
  progress: number;
  phase: string | null;
}

export interface ProviderStatus {
  llm: { mode: string; reachable: boolean; model: string; model_available: boolean; hint?: string };
  ffmpeg: { available: boolean };
  video: { provider: string; method: string };
  voiceover: { configured: boolean };
  shopify: { configured: boolean; store: string | null };
  demo_mode: boolean;
}

export interface PhotoAnalysis {
  source: string;
  note?: string;
  fields: { name?: string; brand_name?: string; summary?: string; materials?: string; dimensions?: string; features?: string[]; visible_text?: string[] };
}

export interface ConnectionState { provider: "shopify"; connected: boolean; label: string | null; source: "app" | "env" | null }
