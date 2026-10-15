from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class Platform(str, Enum):
    instagram = "instagram"
    facebook = "facebook"
    pinterest = "pinterest"
    etsy = "etsy"
    shopify = "shopify"


class Tone(str, Enum):
    straightforward = "straightforward"
    persuasive = "persuasive"
    emotional = "emotional"
    friendly = "friendly"
    luxury = "luxury"
    playful = "playful"


class VisualStyle(str, Enum):
    premium_studio = "premium_studio"
    ugc = "ugc"
    minimal = "minimal"
    warm_cozy = "warm_cozy"
    bold_colorful = "bold_colorful"


class Objective(str, Enum):
    sales = "sales"
    awareness = "awareness"
    gift = "gift"
    features = "features"


class JobStatus(str, Enum):
    queued = "queued"
    generating_copy = "generating_copy"
    generating_video = "generating_video"
    generating_voiceover = "generating_voiceover"
    assembling_video = "assembling_video"
    completed = "completed"
    failed = "failed"


def _clean_list(v: list[str]) -> list[str]:
    return [s.strip() for s in v if s and s.strip()]


MAX_IMAGES = 5


class ProductInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    image_asset_ids: list[str] = Field(min_length=1, max_length=MAX_IMAGES)  # first = hero image
    summary: str | None = Field(default=None, max_length=1000)
    price: str | None = Field(default=None, max_length=40)
    currency: str | None = Field(default=None, max_length=8)
    materials: str | None = Field(default=None, max_length=500)
    dimensions: str | None = Field(default=None, max_length=300)
    features: list[str] = Field(default_factory=list, max_length=20)
    benefits: list[str] = Field(default_factory=list, max_length=20)
    audience: str | None = Field(default=None, max_length=300)
    brand_name: str | None = Field(default=None, max_length=80)
    brand_voice: str | None = Field(default=None, max_length=500)
    care_instructions: str | None = Field(default=None, max_length=500)
    extra_notes: str | None = Field(default=None, max_length=1000)
    forbidden_words: list[str] = Field(default_factory=list, max_length=30)

    @model_validator(mode="before")
    @classmethod
    def _legacy_single_image(cls, data):
        if isinstance(data, dict) and "image_asset_ids" not in data and data.get("image_asset_id"):
            data = {**data, "image_asset_ids": [data["image_asset_id"]]}
        return data

    @field_validator("image_asset_ids")
    @classmethod
    def _unique_ids(cls, v: list[str]) -> list[str]:
        if len(set(v)) != len(v) or any(not i or len(i) > 64 for i in v):
            raise ValueError("Each photo can only be used once")
        return v

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Product name is required")
        return v

    @field_validator("features", "benefits", "forbidden_words")
    @classmethod
    def _lists(cls, v: list[str]) -> list[str]:
        return _clean_list(v)

    @field_validator(
        "summary", "price", "currency", "materials", "dimensions", "audience",
        "brand_name", "brand_voice", "care_instructions", "extra_notes",
    )
    @classmethod
    def _blank_to_none(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None


class CreativeSettings(BaseModel):
    platforms: list[Platform] = Field(default_factory=lambda: [Platform.instagram], min_length=1)
    tone: Tone = Tone.friendly
    visual_style: VisualStyle = VisualStyle.minimal
    objective: Objective = Objective.sales
    duration_seconds: int = Field(default=10, ge=5, le=15)
    aspect_ratio: str = Field(default="9:16", pattern=r"^\d{1,2}:\d{1,2}$")
    voiceover: bool = False
    voice_id: str | None = None

    @field_validator("platforms")
    @classmethod
    def _dedupe(cls, v: list[Platform]) -> list[Platform]:
        return list(dict.fromkeys(v))


class StoryBeat(BaseModel):
    time: str = ""
    visual: str = ""
    on_screen_text: str = ""


class CopyOutput(BaseModel):
    product_title: str = ""
    short_description: str = ""
    full_description: str = ""
    key_features: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    target_audience: str = ""
    call_to_action: str = ""
    seo_title: str = ""
    meta_description: str = ""
    keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    social_caption: str = ""
    hashtags: list[str] = Field(default_factory=list)
    ad_headline: str = ""
    voiceover_script: str = ""
    video_hook: str = ""
    video_storyboard: list[StoryBeat] = Field(default_factory=list)
    video_generation_prompt: str = ""
    missing_information: list[str] = Field(default_factory=list)
    claims_requiring_review: list[str] = Field(default_factory=list)
    platform_outputs: dict[str, dict[str, str | list[str]]] = Field(default_factory=dict)


class JobError(BaseModel):
    code: str
    message: str
    retryable: bool = False


class StageEntry(BaseModel):
    name: str
    status: str  # running | done | skipped | failed
    progress: float = 0.0  # 0..1 within this stage
    notes: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    detail: str | None = None


class GeneratedAsset(BaseModel):
    id: str
    kind: str  # image | studio_image | catalog_image | cutout_image | deck_slide | video | audio | clip/product_src(internal)
    mime: str
    method: str | None = None  # upload | studio_cutout | animated_photo | ltx | elevenlabs
    duration_seconds: float | None = None
    created_at: datetime


class GenerationJob(BaseModel):
    id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    product: ProductInput
    settings: CreativeSettings
    copy_output: CopyOutput | None = None
    copy_source: str | None = None  # "ollama:<model>" or "demo"
    error: JobError | None = None
    stages: list[StageEntry] = Field(default_factory=list)
    assets: list[GeneratedAsset] = Field(default_factory=list)
    progress: float = 0.0  # overall 0..1, computed from the real stage states
    phase: str | None = None  # what is happening right now


class CreateGenerationRequest(BaseModel):
    product: ProductInput
    settings: CreativeSettings = Field(default_factory=CreativeSettings)


class RegenerateCopyRequest(BaseModel):
    section: str | None = None  # a CopyOutput field, or "platform:<name>"; None = everything
    tone: Tone | None = None
    instructions: str | None = Field(default=None, max_length=300)


class AnalyzePhotosRequest(BaseModel):
    asset_ids: list[str] = Field(min_length=1, max_length=MAX_IMAGES)


class PublishRequest(BaseModel):
    confirm: bool = False


# Share of the overall bar each stage owns (copy and video run at the same time, so both advance together).
STAGE_WEIGHTS = {"copy": 0.48, "video": 0.30, "deck": 0.05, "voiceover": 0.04, "assembly": 0.13}
STAGE_PHASE = {"copy": "Writing your copy", "video": "Refining photos and building the video", "deck": "Designing your image deck",
               "voiceover": "Generating voiceover", "assembly": "Adding text to the video"}


def overall_progress(stages: list[StageEntry], settings: CreativeSettings, status: JobStatus) -> tuple[float, str | None]:
    if status == JobStatus.completed:
        return 1.0, None
    active = {k: w for k, w in STAGE_WEIGHTS.items() if k != "voiceover" or settings.voiceover}
    by = {s.name: s for s in stages}
    total = sum(active.values())
    got = 0.0
    for k, w in active.items():
        s = by.get(k)
        if s is None:
            continue
        got += w * (1.0 if s.status in ("done", "skipped") else min(max(s.progress, 0.0), 0.98) if s.status == "running" else 0.0)
    running = [STAGE_PHASE[s.name] for s in stages if s.status == "running" and s.name in STAGE_PHASE]
    return round(got / total, 3), (" + ".join(running) if running else ("Getting started" if status == JobStatus.queued else None))


class ConnectShopifyRequest(BaseModel):
    domain: str = Field(min_length=1, max_length=200)
    token: str = Field(min_length=1, max_length=500)


class AccessRequest(BaseModel):
    code: str = Field(min_length=1, max_length=200)
