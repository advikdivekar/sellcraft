"""Privacy canary for Sentry: push a unique marker through every place seller text lives (facts, model output, a failing
call) and fail if the marker appears in ANY envelope the SDK would send. Also checks that useful metadata does get through."""
import json

import pytest
import sentry_sdk
from sentry_sdk.transport import Transport

from app import tracing
from app.schemas import CreativeSettings, ProductInput
from app.services.copy import CopyService

from .conftest import good_llm_data
from .test_api import FakeLLM

MARKER = "ZXQ-CANARY-7731"


class Capture(Transport):
    def __init__(self, options=None):
        super().__init__(options)
        self.sent: list[str] = []

    def capture_envelope(self, envelope):
        self.sent.append(json.dumps([i.payload.json for i in envelope.items if i.payload.json is not None], default=str))


@pytest.fixture
def sentry(monkeypatch):
    from app import config
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.invalid/1")
    config.get_settings.cache_clear()
    t = Capture()
    tracing.init(transport=t)
    yield t
    sentry_sdk.get_client().close()
    tracing._enabled = False


def _run_kit(**product_kw):
    d = good_llm_data()
    d["short_description"] = f"A perfect cure for wrinkles. {MARKER}"  # trips risky + regulated checks; carries the marker
    product = ProductInput(name=f"Cream {MARKER}", image_asset_id="img", summary=f"secret {MARKER}", **product_kw)
    with sentry_sdk.start_transaction(op="job", name="generation"):
        with tracing.span("gen_ai.invoke_agent", "invoke_agent sellcraft-copy", job_id="j1"):
            return CopyService(FakeLLM([d])).generate(product, CreativeSettings())


def test_marker_never_reaches_sentry(sentry):
    _run_kit(features=[f"feature {MARKER}"], forbidden_words=["perfect"])
    sentry_sdk.flush()
    body = "\n".join(sentry.sent)
    assert body, "nothing was captured, so this test would pass for the wrong reason"
    assert MARKER not in body


def test_flags_and_counts_are_reported(sentry):
    _run_kit(forbidden_words=["perfect"])
    sentry_sdk.flush()
    body = "\n".join(sentry.sent)
    assert "flag.kind" in body and "prompt_version" in body
    assert "flags.total" in body


def test_scrub_removes_request_extras_and_unlisted_span_data():
    ev = {"request": {"data": MARKER}, "extra": {"x": MARKER}, "user": {"id": MARKER},
          "breadcrumbs": {"values": [{"message": MARKER}]},
          "spans": [{"data": {"prompt": MARKER, "gen_ai.request.model": "m", "latency_ms": 5}}],
          "tags": {"flag.kind": "risky", "secret_tag": MARKER},
          "exception": {"values": [{"type": "ValidationError", "value": MARKER}]}}
    out = tracing._scrub(ev)
    assert MARKER not in json.dumps(out)
    assert out["spans"][0]["data"] == {"gen_ai.request.model": "m", "latency_ms": 5}


def test_report_endpoint_accepts_only_fixed_reasons(client, uploaded):
    j = client.post("/api/generations", json={"product": {"name": "x", "image_asset_ids": [uploaded]}}).json()
    assert client.post(f"/api/generations/{j['id']}/report", json={"section": "social_caption", "reason": "invented_claim"}).status_code == 204
    assert client.post(f"/api/generations/{j['id']}/report", json={"section": "social_caption", "reason": MARKER}).status_code == 422
    assert client.post(f"/api/generations/{j['id']}/report", json={"section": MARKER, "reason": "other"}).status_code == 422
    assert client.post("/api/generations/nope/report", json={"section": "social_caption", "reason": "other"}).status_code == 404
