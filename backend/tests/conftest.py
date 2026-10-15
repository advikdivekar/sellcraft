import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import config


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "up"))
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 't.db'}")
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("SENTRY_DSN", "")
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


@pytest.fixture(autouse=True)
def fast_framing(monkeypatch, request):
    """Most tests don't need the segmentation model (slow to load); use the framed-photo path unless a test opts in."""
    if "real_cutout" not in request.keywords:
        from app.services.video import studio
        monkeypatch.setattr(studio, "cutout", lambda img: None)


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


def png_bytes(size=(64, 48), fmt="PNG") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 120, 60)).save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def uploaded(client):
    r = client.post("/api/uploads", files={"file": ("p.png", png_bytes(), "image/png")})
    assert r.status_code == 201, r.text
    return r.json()["asset_id"]


def good_llm_data(platforms=("instagram",)):
    from app.services.prompts import PLATFORM_FIELDS
    from app.schemas import Platform
    d = {
        "product_title": "Silver Moon Necklace", "short_description": "A delicate necklace.",
        "full_description": "A delicate silver necklace with a moon pendant.", "key_features": ["Moon pendant"],
        "benefits": [], "target_audience": "", "call_to_action": "Shop now", "seo_title": "Silver Moon Necklace",
        "meta_description": "Silver necklace.", "keywords": ["necklace"], "tags": ["necklace"],
        "social_caption": "New in: the moon necklace.", "hashtags": ["#necklace"], "ad_headline": "Moonlight, worn.",
        "voiceover_script": "The silver moon necklace.", "video_hook": "Meet the moon.",
        "video_storyboard": [{"time": "0-2s", "visual": "pendant", "on_screen_text": "Meet the moon"}],
        "video_generation_prompt": "Slow push-in.", "missing_information": ["Price"], "claims_requiring_review": [],
        "platform_outputs": {p: {f: ("x" if t == "str" else ["x"]) for f, t in PLATFORM_FIELDS[Platform(p)].items()}
                             for p in platforms},
    }
    return d
