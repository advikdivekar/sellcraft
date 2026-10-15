"""Deterministic Demo Mode. Builds copy ONLY from the supplied facts and is always labelled as demo.
This is NOT a model response; it exists so the UI can be shown without Ollama."""
from ...schemas import CopyOutput, CreativeSettings, Platform, ProductInput, StoryBeat
from ..prompts import CORE_FIELDS


def demo_copy(product: ProductInput, settings: CreativeSettings) -> CopyOutput:
    n = product.name
    feats = product.features or ([product.materials] if product.materials else [])
    first = feats[0] if feats else None
    short = product.summary or f"{n}."
    missing = [label for label, v in [("Materials", product.materials), ("Dimensions", product.dimensions),
                                       ("Price", product.price), ("Care instructions", product.care_instructions)] if not v]
    tag = n.lower().replace(" ", "")
    po: dict[str, dict] = {}
    for p in settings.platforms:
        if p is Platform.instagram:
            po[p.value] = {"hook": f"Meet {n}.", "reel_caption": short, "hashtags": [f"#{tag}"], "video_on_screen_text": [n]}
        elif p is Platform.facebook:
            po[p.value] = {"primary_text": short, "headline": n, "description": first or n, "cta": "Learn more"}
        elif p is Platform.pinterest:
            po[p.value] = {"pin_title": n, "pin_description": short, "keyword_phrases": [n.lower()]}
        elif p is Platform.etsy:
            po[p.value] = {"title": n, "item_description": short, "tags": [n.lower()[:20]], "attributes": feats}
        else:
            po[p.value] = {"page_copy": short, "feature_bullets": feats, "seo_title": n[:60], "meta_description": short[:160]}
    return CopyOutput(
        product_title=n, short_description=short, full_description=short + (" " + "; ".join(feats) + "." if feats else ""),
        key_features=feats, benefits=product.benefits, target_audience=product.audience or "",
        call_to_action="Shop now", seo_title=n[:60], meta_description=short[:160], keywords=[n.lower()],
        tags=[n.lower()[:20]], social_caption=short, hashtags=[f"#{tag}"], ad_headline=n,
        voiceover_script=f"{n}. {first or ''}".strip(), video_hook=n[:40],
        video_storyboard=[StoryBeat(time=t, visual=v, on_screen_text=o) for t, v, o in [
            ("0-2s", "Opening shot of the product", n), ("2-6s", "Slow camera move around the product", ""),
            ("6-8s", "Highlight one verified feature", first or ""), ("8-10s", "Product name and call to action", "Shop now")]],
        video_generation_prompt="Slow, subtle camera push-in. Keep the product unchanged; add no text, labels or logos.",
        missing_information=missing, claims_requiring_review=[], platform_outputs=po,
    )


def demo_section(product: ProductInput, settings: CreativeSettings, section: str) -> dict:
    full = demo_copy(product, settings)
    if section.startswith("platform:"):
        key = section.split(":", 1)[1]
        return {key: full.platform_outputs[key]}
    assert section in CORE_FIELDS
    return {section: getattr(full, section)}
