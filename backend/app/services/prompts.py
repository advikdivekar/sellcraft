"""Prompt + schema construction. Concerns are kept in separate sections:
FACTS | PLATFORM | TONE | STYLE | OBJECTIVE | RULES | OUTPUT."""
import re

from ..schemas import CopyOutput, CreativeSettings, Objective, Platform, ProductInput, Tone, VisualStyle

# field -> kind ("str" | "list")
CORE_FIELDS: dict[str, str] = {
    "product_title": "str", "short_description": "str", "full_description": "str",
    "key_features": "list", "benefits": "list", "target_audience": "str",
    "call_to_action": "str", "seo_title": "str", "meta_description": "str",
    "keywords": "list", "tags": "list", "social_caption": "str", "hashtags": "list",
    "ad_headline": "str", "voiceover_script": "str", "video_hook": "str",
    "video_storyboard": "storyboard", "video_generation_prompt": "str",
    "missing_information": "list", "claims_requiring_review": "list",
}

# The kit is written as independent chunks so they can be generated concurrently (see CopyService.generate).
CORE_CHUNKS: list[list[str]] = [  # ~equal token cost each, so the parallel calls finish together
    ["product_title", "short_description", "full_description", "target_audience"],
    ["key_features", "benefits", "keywords", "tags", "seo_title", "meta_description"],
    ["social_caption", "hashtags", "ad_headline", "call_to_action", "missing_information", "claims_requiring_review"],
    ["video_hook", "voiceover_script", "video_storyboard", "video_generation_prompt"],
]
assert {k for c in CORE_CHUNKS for k in c} == set(CORE_FIELDS)

PLATFORM_FIELDS: dict[Platform, dict[str, str]] = {
    Platform.instagram: {"hook": "str", "reel_caption": "str", "hashtags": "list", "video_on_screen_text": "list"},
    Platform.facebook: {"primary_text": "str", "headline": "str", "description": "str", "cta": "str"},
    Platform.pinterest: {"pin_title": "str", "pin_description": "str", "keyword_phrases": "list"},
    Platform.etsy: {"title": "str", "item_description": "str", "tags": "list", "attributes": "list"},
    Platform.shopify: {"page_copy": "str", "feature_bullets": "list", "seo_title": "str", "meta_description": "str"},
}

PLATFORM_GUIDE: dict[Platform, str] = {
    Platform.instagram: "Short, scannable, hook in the first line, Reel caption, a few relevant hashtags. Max ~150 words.",
    Platform.facebook: "Primary ad text, a headline under 40 characters, a one-line description, and a clear CTA.",
    Platform.pinterest: "Descriptive, search-friendly pin title and description; keyword phrases people would search.",
    Platform.etsy: "Clear searchable title (no keyword stuffing), detailed item description, up to 13 short tags (max 20 chars each), attributes ONLY if stated in the facts.",
    Platform.shopify: "Product-page copy with useful sections, feature bullets, SEO title (<60 chars) and meta description (<160 chars).",
}

TONE_GUIDE = {
    Tone.straightforward: "Plain, direct, factual. No hype.",
    Tone.persuasive: "Benefit-led and confident, with a clear reason to buy. No false urgency.",
    Tone.emotional: "Warm, story-like, focused on how it feels to own or gift. Stay truthful.",
    Tone.friendly: "Conversational and approachable, like a helpful small-shop owner.",
    Tone.luxury: "Refined, understated, premium vocabulary. Short sentences.",
    Tone.playful: "Light, witty, energetic. Keep claims accurate.",
}
STYLE_GUIDE = {
    VisualStyle.premium_studio: "premium studio commercial: clean lighting, slow elegant camera moves",
    VisualStyle.ugc: "UGC-style social ad: handheld feel, natural, casual",
    VisualStyle.minimal: "minimal and clean: lots of negative space, simple motion",
    VisualStyle.warm_cozy: "warm and cozy lifestyle: soft light, inviting atmosphere",
    VisualStyle.bold_colorful: "bold and colorful: punchy colors, energetic motion",
}
OBJECTIVE_GUIDE = {
    Objective.sales: "Drive sales: end with a clear, honest call to action.",
    Objective.awareness: "Build brand awareness: memorable hook, brand-forward, softer CTA.",
    Objective.gift: "Gift appeal: who it suits and the occasions it fits, without inventing occasions as facts.",
    Objective.features: "Explain features: lead with verified specifics and what they mean for the buyer.",
}

SYSTEM_PROMPT = """You are SellCraft, a careful marketing copywriter for small online sellers.
Write ONLY from the PRODUCT FACTS. They are the single source of truth.
- Never invent properties, materials, sizes, prices, discounts, scarcity, reviews, awards, certifications or results.
- Never call a product eco-friendly, organic, handmade, hypoallergenic, vegan, waterproof, medical or certified unless the facts say so.
- Do not assume who the buyer is (gender, age, occasion) or claim fit, comfort, durability or quality the facts don't state.
- Tone changes wording, never facts. If useful information is missing, don't guess: put it in "missing_information".
- List risky claims in "claims_requiring_review". Never use the seller's FORBIDDEN WORDS. No fake urgency.
- Write final text only: no placeholders like {hook} or [name].
Reply with one JSON object matching the schema. No markdown."""

VIDEO_RULES = """- video_hook: max 8 words. voiceover_script: readable aloud in about 10 seconds (max 25 words).
- video_storyboard: exactly 4 beats at "0-2s" (hook), "2-6s" (product showcase), "6-8s" (one verified feature), "8-10s" (name + CTA). Each beat: visual max 10 words, on_screen_text max 6 words. Visuals may only describe camera movement, framing and lighting on the supplied product photo. Never invent actions, hands, people or objects.
- video_generation_prompt: max 25 words; subtle camera movement only; keep the product unchanged; add no labels, logos or text."""


_FILLER = re.compile(r"(?<!\w)(?:h+a+a*h*|haan|h?umm+|u+h+|hmm+|erm?)(?!\w)[,.]?\s*", re.IGNORECASE)


def clean_fact(text: str | None) -> str | None:
    """Drop spoken-style filler a seller may type ("haa", "umm") so small models don't echo it."""
    if not text:
        return text
    return re.sub(r"\s{2,}", " ", _FILLER.sub("", text)).strip() or None


def _facts(p: ProductInput) -> str:
    p = p.model_copy(update={
        "name": clean_fact(p.name) or p.name,
        **{k: clean_fact(getattr(p, k)) for k in ("summary", "materials", "dimensions", "audience", "brand_voice", "care_instructions", "extra_notes")},
        "features": [c for c in map(clean_fact, p.features) if c],
        "benefits": [c for c in map(clean_fact, p.benefits) if c],
    })
    rows = [("Product name", p.name), ("Brand", p.brand_name), ("Summary", p.summary),
            ("Price", f"{p.price} {p.currency or ''}".strip() if p.price else None),
            ("Materials / ingredients", p.materials), ("Dimensions / specs", p.dimensions),
            ("Main features", "; ".join(p.features) or None), ("Verified benefits", "; ".join(p.benefits) or None),
            ("Target audience", p.audience), ("Brand voice", p.brand_voice),
            ("Care / usage", p.care_instructions), ("Extra notes from the seller", p.extra_notes)]
    lines = [f"- {k}: {v}" for k, v in rows if v]
    absent = [k for k, v in rows if not v and k not in ("Brand voice", "Brand", "Extra notes from the seller")]
    lines.append("- Not provided: " + (", ".join(absent) or "none"))
    return "\n".join(lines)


def _type(kind: str) -> dict:
    if kind == "str":
        return {"type": "string"}
    if kind == "list":
        return {"type": "array", "items": {"type": "string"}}
    return {"type": "array", "items": {"type": "object", "required": ["time", "visual", "on_screen_text"],
            "properties": {k: {"type": "string"} for k in ("time", "visual", "on_screen_text")}}}


def _obj(fields: dict[str, str]) -> dict:
    return {"type": "object", "required": list(fields), "properties": {k: _type(v) for k, v in fields.items()}}


def build_fields_schema(keys: list[str]) -> dict:
    return _obj({k: CORE_FIELDS[k] for k in keys})


def build_schema(platforms: list[Platform], *, section: str | None = None) -> dict:
    if section and section.startswith("platform:"):
        p = Platform(section.split(":", 1)[1])
        return {"type": "object", "required": [p.value], "properties": {p.value: _obj(PLATFORM_FIELDS[p])}}
    if section:
        return _obj({section: CORE_FIELDS[section]})
    schema = _obj(CORE_FIELDS)
    schema["required"].append("platform_outputs")
    schema["properties"]["platform_outputs"] = {
        "type": "object", "required": [p.value for p in platforms],
        "properties": {p.value: _obj(PLATFORM_FIELDS[p]) for p in platforms}}
    return schema


def build_user_prompt(product: ProductInput, settings: CreativeSettings, *, section: str | None = None,
                      current: CopyOutput | None = None, instructions: str | None = None,
                      fields: list[str] | None = None) -> str:
    """Only the sections a part of the kit needs: every extra token is re-read by every parallel call."""
    vid = bool(fields) and "video_hook" in fields
    plat = [Platform(section.split(":", 1)[1])] if section and section.startswith("platform:") else (
        [] if fields else settings.platforms)
    parts = [
        "## PRODUCT FACTS\n" + _facts(product),
        "## FORBIDDEN WORDS\n" + (", ".join(product.forbidden_words) or "none"),
    ]
    if plat:
        parts.append("## PLATFORMS\n" + "\n".join(f"- {p.value}: {PLATFORM_GUIDE[p]}\n  fields: {', '.join(PLATFORM_FIELDS[p])}" for p in plat))
    parts.append("## TONE\n" + TONE_GUIDE[settings.tone])
    if vid or not fields:
        parts.append("## VISUAL STYLE (for the video brief)\n" + STYLE_GUIDE[settings.visual_style])
    if not fields or "social_caption" in fields or vid or plat:
        parts.append("## MARKETING OBJECTIVE\n" + OBJECTIVE_GUIDE[settings.objective])
    if vid or not (fields or section):
        parts.append("## VIDEO RULES\n" + VIDEO_RULES)
    if fields:
        parts.append("## TASK\nWrite ONLY these JSON fields, using the facts above: " + ", ".join(fields) + ".")
    elif section:
        verb = "Rewrite" if current else "Write"
        parts.append(f"## TASK\n{verb} ONLY \"{section}\" in the tone above, using the same facts. "
                     "Return a JSON object containing just that key.")
        if current:
            parts.append("## CURRENT COPY (for context; keep consistent)\n" + current.model_dump_json(exclude={"platform_outputs"}))
    else:
        parts.append("## TASK\nProduce the full marketing kit as JSON. Include platform_outputs for each platform listed.")
    if instructions:
        parts.append("## SELLER NOTE\n" + instructions)
    return "\n\n".join(parts)
