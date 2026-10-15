import pytest

from app import db
from app.errors import AppError
from app.schemas import CreativeSettings, ProductInput
from app.services import jobs
from app.services.copy import CopyService
from app.services.llm.base import LLMProvider, LLMResult

from .conftest import good_llm_data, png_bytes


class FakeLLM(LLMProvider):
    name = "fake"
    model = "fake-model"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def health(self):
        return {"reachable": True}

    def generate_json(self, system, user, schema, *, temperature=0.4, images=None):
        self.calls.append((system, user, schema))
        self.images = images
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return LLMResult(data=r, model=self.model)


def product(**kw):
    return ProductInput(name="Silver Moon Necklace", image_asset_id="img", **kw)


# ---------- validation ----------
def test_product_name_required():
    with pytest.raises(Exception):
        ProductInput(name="   ", image_asset_id="x")


def test_blank_optionals_become_none_and_lists_clean():
    p = product(materials="  ", features=["a", " ", "b "])
    assert p.materials is None and p.features == ["a", "b"]


def test_create_requires_uploaded_image(client):
    r = client.post("/api/generations", json={"product": {"name": "x", "image_asset_id": "nope"}, "settings": {}})
    assert r.status_code == 422 and r.json()["error"]["code"] == "bad_image"


def test_validation_error_does_not_echo_values(client):
    r = client.post("/api/generations", json={"product": {"name": "", "image_asset_id": "SECRETVAL"}})
    assert r.status_code == 422 and "SECRETVAL" not in r.text


# ---------- uploads ----------
def test_invalid_upload_rejected(client):
    r = client.post("/api/uploads", files={"file": ("a.png", b"not an image", "image/png")})
    assert r.status_code == 415 and r.json()["error"]["code"] == "invalid_image"


def test_gif_rejected_even_if_valid_image(client):
    r = client.post("/api/uploads", files={"file": ("a.jpg", png_bytes(fmt="GIF"), "image/jpeg")})
    assert r.status_code == 415 and r.json()["error"]["code"] == "unsupported_type"


def test_oversize_upload_rejected(client, monkeypatch):
    from app import config
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    config.get_settings.cache_clear()
    r = client.post("/api/uploads", files={"file": ("a.png", png_bytes(), "image/png")})
    assert r.status_code == 413


def test_upload_uses_generated_filename(client, tmp_path):
    r = client.post("/api/uploads", files={"file": ("../../evil.png", png_bytes(), "image/png")})
    assert r.status_code == 201
    names = [p.name for p in (tmp_path / "up").iterdir()]
    assert names == [r.json()["asset_id"] + ".png"]


# ---------- copy service ----------
def test_generate_validates_and_returns_copy():
    svc = CopyService(FakeLLM([good_llm_data()]))
    res = svc.generate(product(), CreativeSettings())
    assert res.copy.product_title == "Silver Moon Necklace"
    assert res.source == "ollama:fake-model" and res.copy.missing_information == ["Price"]


def test_string_instead_of_list_is_coerced():
    d = good_llm_data()
    d["key_features"] = "Moon pendant; Silver chain"
    res = CopyService(FakeLLM([d])).generate(product(), CreativeSettings())
    assert res.copy.key_features == ["Moon pendant", "Silver chain"]


def test_incomplete_output_triggers_one_repair():
    bad = good_llm_data(); bad["product_title"] = ""
    llm = FakeLLM([bad, good_llm_data()])
    res = CopyService(llm).generate(product(), CreativeSettings())
    assert res.copy.product_title and len(llm.calls) == 2
    assert "previous reply had a problem" in llm.calls[1][1]


def test_persistent_bad_output_raises():
    bad = good_llm_data(); bad["product_title"] = ""
    with pytest.raises(AppError) as e:
        CopyService(FakeLLM([bad, bad])).generate(product(), CreativeSettings())
    assert e.value.code == "llm_incomplete_output"


def test_malformed_json_retried_once():
    llm = FakeLLM([AppError("llm_bad_json", "bad", retryable=True), good_llm_data()])
    assert CopyService(llm).generate(product(), CreativeSettings()).copy.product_title


def test_provider_offline_surfaces_actionable_error():
    llm = FakeLLM([AppError("llm_offline", "Can't reach Ollama", retryable=True, status=503)])
    with pytest.raises(AppError) as e:
        CopyService(llm).generate(product(), CreativeSettings())
    assert e.value.code == "llm_offline"


def test_forbidden_words_flagged():
    d = good_llm_data(); d["social_caption"] = "Our cheap necklace"
    res = CopyService(FakeLLM([d])).generate(product(forbidden_words=["cheap"]), CreativeSettings())
    assert "Forbidden word used: cheap" in res.copy.claims_requiring_review


def test_regenerate_section_keeps_other_fields():
    svc = CopyService(FakeLLM([good_llm_data(), {"social_caption": "A softer caption."}]))
    first = svc.generate(product(), CreativeSettings())
    res = svc.regenerate(first.copy, product(), CreativeSettings(), section="social_caption", tone="emotional", instructions=None)
    assert res.copy.social_caption == "A softer caption." and res.copy.product_title == first.copy.product_title
    assert "emotional" in svc.llm.calls[1][1].lower() or "Warm" in svc.llm.calls[1][1]


def test_regenerate_unknown_section():
    first = CopyService(FakeLLM([good_llm_data()])).generate(product(), CreativeSettings())
    with pytest.raises(AppError):
        CopyService(FakeLLM([])).regenerate(first.copy, product(), CreativeSettings(), section="bogus", tone=None, instructions=None)


def test_prompt_separates_sections_and_lists_missing_facts():
    from app.services.prompts import build_user_prompt
    p = build_user_prompt(product(price="25", currency="USD"), CreativeSettings())
    for h in ("## PRODUCT FACTS", "## PLATFORMS", "## TONE", "## VISUAL STYLE", "## MARKETING OBJECTIVE"):
        assert h in p
    assert "Not provided:" in p and "Materials" in p.split("Not provided:")[1]


# ---------- jobs ----------
def _make_job(client, uploaded, **settings):
    return db.create_job(ProductInput(name="Necklace", image_asset_id=uploaded), CreativeSettings(**settings))


def test_job_completes_and_records_stages(client, uploaded):
    job_id = _make_job(client, uploaded)
    jobs.run_generation(job_id, CopyService(FakeLLM([good_llm_data()])))
    job = db.get_job(job_id)
    assert job.status.value == "completed" and job.copy_output is not None
    assert [(s.name, s.status) for s in job.stages] == [("copy", "done"), ("video", "done"), ("assembly", "done")]
    vid = [a for a in job.assets if a.kind == "video"]
    assert len(vid) == 1 and vid[0].method == "animated_photo" and abs(vid[0].duration_seconds - 10) < 0.5
    assert all(a.kind != "clip" for a in job.assets)  # internal clip never exposed


def test_job_failure_is_safe_and_retryable(client, uploaded):
    job_id = _make_job(client, uploaded)
    llm = FakeLLM([AppError("llm_offline", "Can't reach Ollama", retryable=True, status=503)])
    jobs.run_generation(job_id, CopyService(llm))
    job = db.get_job(job_id)
    assert job.status.value == "failed" and job.error.code == "llm_offline" and job.error.retryable
    assert job.stages[0].status == "failed"


def test_unexpected_error_hides_internals(client, uploaded):
    job_id = _make_job(client, uploaded)

    class Boom(FakeLLM):
        def generate_json(self, *a, **k):
            raise RuntimeError("secret internal detail")
    jobs.run_generation(job_id, CopyService(Boom([])))
    job = db.get_job(job_id)
    assert job.error.code == "internal_error" and "secret" not in job.error.message


def test_voiceover_disabled_has_no_voice_stage(client, uploaded):
    job_id = _make_job(client, uploaded, voiceover=False)
    jobs.run_generation(job_id, CopyService(FakeLLM([good_llm_data()])))
    assert all(s.name != "voiceover" for s in db.get_job(job_id).stages)


# ---------- API end-to-end (demo mode, no live model) ----------
def test_end_to_end_demo_mode(client, uploaded, monkeypatch):
    from app import config
    monkeypatch.setenv("DEMO_MODE", "true")
    config.get_settings.cache_clear()
    r = client.post("/api/generations", json={"product": {"name": "Moon Necklace", "image_asset_id": uploaded, "features": ["925 silver"]},
                                              "settings": {"platforms": ["etsy", "instagram"], "tone": "luxury"}})
    assert r.status_code == 202
    job = client.get(f"/api/generations/{r.json()['id']}").json()
    assert job["status"] == "completed" and job["copy_source"] == "demo"
    assert set(job["copy_output"]["platform_outputs"]) == {"etsy", "instagram"}
    assert "Price" in job["copy_output"]["missing_information"]

    edited = job["copy_output"] | {"social_caption": "My edit"}
    assert client.patch(f"/api/generations/{job['id']}/copy", json=edited).json()["copy_output"]["social_caption"] == "My edit"

    rg = client.post(f"/api/generations/{job['id']}/regenerate-copy", json={"section": "social_caption", "tone": "playful"})
    assert rg.status_code == 200 and rg.json()["settings"]["tone"] == "playful"


def test_asset_authorization(client, uploaded, monkeypatch):
    from app import config
    monkeypatch.setenv("DEMO_MODE", "true")
    config.get_settings.cache_clear()
    j1 = client.post("/api/generations", json={"product": {"name": "A", "image_asset_id": uploaded}}).json()
    up2 = client.post("/api/uploads", files={"file": ("p.png", png_bytes(), "image/png")}).json()["asset_id"]
    j2 = client.post("/api/generations", json={"product": {"name": "B", "image_asset_id": up2}}).json()
    assert client.get(f"/api/generations/{j1['id']}/assets/{uploaded}").status_code == 200
    assert client.get(f"/api/generations/{j2['id']}/assets/{uploaded}").status_code == 404
    assert client.get(f"/api/generations/{j1['id']}/assets/..%2F..%2Fetc%2Fpasswd").status_code == 404
    # an already-used image cannot be re-attached to another job
    again = client.post("/api/generations", json={"product": {"name": "C", "image_asset_id": uploaded}})
    assert again.status_code == 422


def test_providers_status_hides_secrets(client, monkeypatch):
    from app import config
    monkeypatch.setenv("ELEVENLABS_API_KEY", "sk_supersecret")
    config.get_settings.cache_clear()
    r = client.get("/api/providers/status")
    assert r.status_code == 200 and "sk_supersecret" not in r.text and r.json()["voiceover"]["configured"] is True


def test_retry_only_for_failed_jobs(client, uploaded, monkeypatch):
    from app import config
    monkeypatch.setenv("DEMO_MODE", "true")
    config.get_settings.cache_clear()
    j = client.post("/api/generations", json={"product": {"name": "A", "image_asset_id": uploaded}}).json()
    assert client.post(f"/api/generations/{j['id']}/retry").status_code == 409
    db.update_job(j["id"], status="failed")
    r = client.post(f"/api/generations/{j['id']}/retry")
    assert r.status_code == 202
    assert client.get(f"/api/generations/{j['id']}").json()["status"] == "completed"


def test_placeholder_output_is_repaired():
    bad = good_llm_data(); bad["social_caption"] = "{hook} Meet the moon."
    llm = FakeLLM([bad, good_llm_data()])
    res = CopyService(llm).generate(product(), CreativeSettings())
    assert "{" not in res.copy.social_caption and len(llm.calls) == 2


def test_filler_words_removed_from_facts_but_real_words_kept():
    from app.services.prompts import clean_fact
    assert clean_fact("haa choco chips in it") == "choco chips in it"
    assert clean_fact("Umm, handmade hat") == "handmade hat"
    assert clean_fact("Haha-proof, hammock, Hahn ceramic") == "Haha-proof, hammock, Hahn ceramic"
    assert clean_fact("haa") is None


# ---------- video ----------
def _demo(monkeypatch):
    from app import config
    monkeypatch.setenv("DEMO_MODE", "true")
    config.get_settings.cache_clear()


def test_video_served_and_scoped_to_job(client, uploaded, monkeypatch):
    _demo(monkeypatch)
    j = client.post("/api/generations", json={"product": {"name": "A", "image_asset_id": uploaded, "features": ["x"]}}).json()
    job = client.get(f"/api/generations/{j['id']}").json()
    vid = next(a for a in job["assets"] if a["kind"] == "video")
    r = client.get(f"/api/generations/{j['id']}/assets/{vid['id']}")
    assert r.status_code == 200 and r.headers["content-type"] == "video/mp4" and r.content[4:8] == b"ftyp"
    other = client.post("/api/uploads", files={"file": ("p.png", png_bytes(), "image/png")}).json()["asset_id"]
    j2 = client.post("/api/generations", json={"product": {"name": "B", "image_asset_id": other}}).json()
    assert client.get(f"/api/generations/{j2['id']}/assets/{vid['id']}").status_code == 404


def test_video_failure_keeps_copy_and_retry_skips_copy(client, uploaded, monkeypatch):
    from app.services.video import service as video
    llm = FakeLLM([good_llm_data()])
    job_id = _make_job(client, uploaded)
    real = video.render_clip
    monkeypatch.setattr(video, "render_clip", lambda job: (_ for _ in ()).throw(AppError("video_render_failed", "boom", retryable=True)))
    jobs.run_generation(job_id, CopyService(llm))
    job = db.get_job(job_id)
    assert job.status.value == "failed" and job.error.code == "video_render_failed" and job.copy_output is not None
    assert [(s.name, s.status) for s in job.stages] == [("copy", "done"), ("video", "failed")]
    monkeypatch.setattr(video, "render_clip", real)
    jobs.run_generation(job_id, CopyService(llm))  # FakeLLM has no responses left: copy must NOT be regenerated
    assert db.get_job(job_id).status.value == "completed" and len(llm.calls) == 1


def test_unknown_video_provider_fails_cleanly(client, uploaded, monkeypatch):
    from app import config
    monkeypatch.setenv("VIDEO_PROVIDER", "ltx")
    config.get_settings.cache_clear()
    job_id = _make_job(client, uploaded)
    jobs.run_generation(job_id, CopyService(FakeLLM([good_llm_data()])))
    job = db.get_job(job_id)
    assert job.status.value == "failed" and job.error.code == "video_provider_unavailable" and job.copy_output


def test_special_characters_render_safely(client, uploaded, monkeypatch):
    _demo(monkeypatch)
    nasty = "50% off' \"quoted\" {x} [y] ; $(rm -rf /) \\ \u2728 :colon"
    j = client.post("/api/generations", json={"product": {"name": nasty, "image_asset_id": uploaded, "features": [nasty]}}).json()
    job = client.get(f"/api/generations/{j['id']}").json()
    assert job["status"] == "completed" and any(a["kind"] == "video" for a in job["assets"])


def test_reassemble_replaces_video_without_new_clip(client, uploaded, monkeypatch):
    _demo(monkeypatch)
    j = client.post("/api/generations", json={"product": {"name": "A", "image_asset_id": uploaded, "features": ["x"]}}).json()
    job = client.get(f"/api/generations/{j['id']}").json()
    old = next(a for a in job["assets"] if a["kind"] == "video")["id"]
    clip_before = [r["id"] for r in db.list_asset_rows(j["id"], ("clip",))]
    edited = job["copy_output"] | {"video_hook": "A brand new hook"}
    client.patch(f"/api/generations/{j['id']}/copy", json=edited)
    assert client.post(f"/api/generations/{j['id']}/reassemble").status_code == 202
    after = client.get(f"/api/generations/{j['id']}").json()
    new = [a for a in after["assets"] if a["kind"] == "video"]
    assert len(new) == 1 and new[0]["id"] != old and after["status"] == "completed"
    assert [r["id"] for r in db.list_asset_rows(j["id"], ("clip",))] == clip_before
    assert client.get(f"/api/generations/{j['id']}/assets/{old}").status_code == 404


def test_validate_rejects_wrong_duration(tmp_path):
    import subprocess
    from app.services.video import ffmpeg
    short = tmp_path / "s.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=1080x1920:d=3", "-pix_fmt", "yuv420p",
                    "-c:v", "libx264", str(short)], check=True)
    with pytest.raises(AppError) as e:
        ffmpeg.validate(short, target=10.0, size=(1080, 1920))
    assert e.value.code == "video_bad_duration"


def test_card_text_is_cleaned_and_fits(tmp_path):
    from PIL import Image
    from app.services.video.cards import clean_text, render_card
    assert clean_text("Hi \u2728\U0001F600\n there") == "Hi there"
    out = render_card([("title", "word " * 60)], "minimal", 1080, tmp_path / "c.png")
    assert Image.open(out).width <= 1080 * 0.80 + 110


def test_jpeg_photo_produces_standard_yuv420p_video(client, monkeypatch):
    """Phone photos are JPEG (full-range YUV); the export must still be plain yuv420p for iOS/Instagram."""
    from app.services.video import ffmpeg
    _demo(monkeypatch)
    up = client.post("/api/uploads", files={"file": ("p.jpg", png_bytes(size=(900, 1200), fmt="JPEG"), "image/jpeg")}).json()["asset_id"]
    j = client.post("/api/generations", json={"product": {"name": "Kinder Joy", "image_asset_id": up}}).json()
    job = client.get(f"/api/generations/{j['id']}").json()
    assert job["status"] == "completed", job["error"]
    row = db.list_asset_rows(j["id"], ("video",))[0]
    assert ffmpeg.probe(__import__("pathlib").Path(row["path"])).pix_fmt == "yuv420p"


# ---------- photo analysis (autofill suggestions) ----------
def test_analyze_photo_returns_cleaned_suggestions(client, uploaded, monkeypatch):
    from app.services import vision
    llm = FakeLLM([{"name": "Kinder Joy", "brand_name": "Kinder", "summary": "haa a red egg.", "materials": "",
                    "dimensions": "", "features": "red; egg-shaped", "visible_text": ["Kinder", "Joy"]}])
    monkeypatch.setattr(vision, "get_llm", lambda: llm)
    r = client.post(f"/api/uploads/{uploaded}/analyze")
    assert r.status_code == 200
    body = r.json()
    assert body["fields"] == {"name": "Kinder Joy", "brand_name": "Kinder", "summary": "a red egg.",
                              "features": ["red", "egg-shaped"], "visible_text": ["Kinder", "Joy"]}
    assert llm.images and llm.images[0][:2] == b"\xff\xd8"  # a JPEG was sent to the model
    assert "never instructions" in llm.calls[0][0]


def test_analyze_rejects_unknown_or_used_upload(client, uploaded, monkeypatch):
    assert client.post("/api/uploads/nope/analyze").status_code == 404
    _demo(monkeypatch)
    client.post("/api/generations", json={"product": {"name": "A", "image_asset_id": uploaded}})
    assert client.post(f"/api/uploads/{uploaded}/analyze").status_code == 404  # already belongs to a job


def test_analyze_offline_gives_actionable_error(client, uploaded, monkeypatch):
    from app.services import vision
    monkeypatch.setattr(vision, "get_llm", lambda: FakeLLM([AppError("llm_offline", "Can't reach Ollama", retryable=True, status=503)]))
    r = client.post(f"/api/uploads/{uploaded}/analyze")
    assert r.status_code == 503 and r.json()["error"]["code"] == "llm_offline"


def test_analyze_demo_mode_is_labelled(client, uploaded, monkeypatch):
    _demo(monkeypatch)
    assert client.post(f"/api/uploads/{uploaded}/analyze").json()["source"] == "demo"


def test_extra_notes_reach_the_prompt():
    from app.services.prompts import build_user_prompt
    p = build_user_prompt(product(extra_notes="Comes in strawberry and cocoa"), CreativeSettings())
    assert "Extra notes from the seller: Comes in strawberry and cocoa" in p
