"""Prompt + schema construction. Concerns are kept in separate sections:
FACTS | PLATFORM | TONE | STYLE | OBJECTIVE | RULES | OUTPUT."""
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
You write ONLY from the PRODUCT FACTS provided. The facts are the single source of truth.

Hard rules:
- Never invent product properties, materials, sizes, prices, discounts, scarcity, reviews, testimonials, awards, certifications or customer results.
- Never claim a product is eco-friendly, organic, handmade, hypoallergenic, vegan, waterproof, medical or certified unless the facts say so.
- Tone changes wording, never facts.
- If useful information is absent (e.g. materials, size, price), do NOT guess; list it in "missing_information" and leave details out of the copy.
- List any phrase in your copy that makes a claim the seller should double-check in "claims_requiring_review".
- Never use words from the seller's FORBIDDEN WORDS list.
- Never output template placeholders such as {hook} or [name]; write the final text.
- Do not assume who the buyer is (gender, age, occasion) unless the facts say so. Do not claim fit, comfort, durability or quality that the facts don't state.
- Keep calls to action suitable for the platform; no fake urgency ("only 3 left", "sale ends tonight").
- The video does not render text; on-screen text is added later, so keep hooks short (max 8 words).
- voiceover_script must be readable aloud in about 10 seconds (maximum 25 words).
- video_storyboard has exactly 4 beats at times "0-2s" (hook), "2-6s" (product showcase), "6-8s" (one verified key feature), "8-10s" (product name + CTA).
- video_generation_prompt describes subtle camera movement and gentle scene motion only. It must keep the product's appearance unchanged and must not add labels, logos, text or new objects.
Respond with a single JSON object that matches the requested schema. No markdown, no commentary."""


def _facts(p: ProductInput) -> str:
    rows = [("Product name", p.name), ("Brand", p.brand_name), ("Summary", p.summary),
            ("Price", f"{p.price} {p.currency or ''}".strip() if p.price else None),
            ("Materials / ingredients", p.materials), ("Dimensions / specs", p.dimensions),
            ("Main features", "; ".join(p.features) or None), ("Verified benefits", "; ".join(p.benefits) or None),
            ("Target audience", p.audience), ("Brand voice", p.brand_voice),
            ("Care / usage", p.care_instructions)]
    lines = [f"- {k}: {v}" for k, v in rows if v]
    absent = [k for k, v in rows if not v and k not in ("Brand voice", "Brand")]
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
                      current: CopyOutput | None = None, instructions: str | None = None) -> str:
    parts = [
        "## PRODUCT FACTS\n" + _facts(product),
        "## FORBIDDEN WORDS\n" + (", ".join(product.forbidden_words) or "none"),
        "## PLATFORMS\n" + "\n".join(f"- {p.value}: {PLATFORM_GUIDE[p]}\n  fields: {', '.join(PLATFORM_FIELDS[p])}"
                                     for p in settings.platforms),
        "## TONE\n" + TONE_GUIDE[settings.tone],
        "## VISUAL STYLE (for the video brief)\n" + STYLE_GUIDE[settings.visual_style],
        "## MARKETING OBJECTIVE\n" + OBJECTIVE_GUIDE[settings.objective],
    ]
    if section:
        parts.append(f"## TASK\nRewrite ONLY \"{section}\" in the tone above, using the same facts. "
                     "Return a JSON object containing just that key.")
        if current:
            parts.append("## CURRENT COPY (for context; keep consistent)\n" + current.model_dump_json(exclude={"platform_outputs"}))
    else:
        parts.append("## TASK\nProduce the full marketing kit as JSON. Include platform_outputs for each platform listed.")
    if instructions:
        parts.append("## SELLER NOTE\n" + instructions)
    return "\n\n".join(parts)
