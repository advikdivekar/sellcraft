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

    def generate_json(self, system, user, schema, *, temperature=0.4):
        self.calls.append((system, user, schema))
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
    assert [(s.name, s.status) for s in job.stages] == [("copy", "done"), ("video", "skipped")]


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
