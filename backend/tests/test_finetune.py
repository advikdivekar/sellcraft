"""Tests for the fine-tuning toolkit (generator, scorer, providers, teacher loop). No live model or network."""
import json

import httpx
import pytest

from app.errors import AppError
from app.schemas import CreativeSettings, Platform, ProductInput
from app.services import prompts
from app.services.copy import CopyService
from app.services.llm.base import LLMProvider, LLMResult
from finetune import factsets, report, scoring, teacher
from finetune.runners import OpenAICompatProvider, extract_json


# ---------------- fact sets ----------------
def test_factsets_are_deterministic_and_split_cleanly():
    a_tr, a_te = factsets.build(seed=3, n_train=60, n_test=15)
    b_tr, b_te = factsets.build(seed=3, n_train=60, n_test=15)
    assert a_tr == b_tr and a_te == b_te
    c_tr, _ = factsets.build(seed=4, n_train=60, n_test=15)
    assert a_tr != c_tr
    key = lambda fs: json.dumps(fs["product"], sort_keys=True) + "|" + ",".join(fs["settings"]["platforms"])
    assert not {key(f) for f in a_tr} & {key(f) for f in a_te}  # no product appears in both splits
    unseen = {f["category"] for f in a_te} & factsets.TEST_ONLY
    assert unseen == factsets.TEST_ONLY and not {f["category"] for f in a_tr} & factsets.TEST_ONLY  # categories the model never trains on
    assert {f["tier"] for f in a_tr} == {"sparse", "medium", "dense", "adversarial"}
    assert [f["id"] for f in a_te] == [f"test-{i:04d}" for i in range(1, 16)]


def test_factset_banks_are_coherent_and_inputs_valid():
    for c in factsets.CATEGORIES.values():
        assert len(c["names"]) == len(c["materials"]) == len(c["dims"])
    train, test = factsets.build(seed=1, n_train=80, n_test=20)
    for fs in train + test:
        ProductInput.model_validate(fs["product"])
        CreativeSettings.model_validate(fs["settings"])
        p = fs["product"]
        assert fs["expected_missing"] == factsets._facts_label_missing({**p, "care_instructions": p.get("care_instructions")})
        if fs["tier"] == "sparse":
            assert len(fs["expected_missing"]) >= 6  # sparse sets really are sparse


def test_expected_missing_matches_what_the_app_prompt_says_is_missing():
    train, _ = factsets.build(seed=2, n_train=40, n_test=10)
    for fs in train:
        prompt = prompts.build_user_prompt(ProductInput.model_validate(fs["product"]), CreativeSettings.model_validate(fs["settings"]),
                                           fields=prompts.CORE_CHUNKS[0])
        line = [l for l in prompt.splitlines() if l.startswith("- Not provided:")][0].removeprefix("- Not provided: ")
        said = [] if line == "none" else [x.strip() for x in line.split(", ")]
        assert said == fs["expected_missing"]


# ---------------- scoring ----------------
FS = {"id": "t-1", "product": {"name": "Soy Candle", "image_asset_ids": ["x"], "price": "24", "currency": "USD", "materials": "soy wax, cotton wick",
                               "features": ["45 hour burn time"], "benefits": [], "forbidden_words": ["cheap"]},
      "settings": {"platforms": ["instagram"], "tone": "friendly", "visual_style": "minimal", "objective": "sales", "duration_seconds": 10,
                   "aspect_ratio": "9:16", "voiceover": False},
      "expected_missing": ["Summary", "Dimensions / specs", "Verified benefits", "Target audience", "Care / usage"]}


def good_kit(fs=FS):
    plats = fs["settings"]["platforms"]
    return {"product_title": "Soy Candle", "short_description": "A soy wax candle with a cotton wick.", "full_description": "Made with soy wax and a cotton wick. Burns for 45 hours.",
            "key_features": ["45 hour burn time"], "benefits": [], "target_audience": "", "call_to_action": "Shop now", "seo_title": "Soy Candle",
            "meta_description": "Soy wax candle, $24.", "keywords": ["soy candle"], "tags": ["candle"], "social_caption": "Meet the soy candle.", "hashtags": ["#candle"],
            "ad_headline": "Soy wax, cotton wick", "voiceover_script": "A soy wax candle.", "video_hook": "Meet the soy candle", "video_storyboard": [{"time": "0-2s", "visual": "push in", "on_screen_text": "Soy Candle"}] * 4,
            "video_generation_prompt": "Slow push-in on the candle.", "missing_information": list(fs["expected_missing"]), "claims_requiring_review": [],
            "platform_outputs": {p: {f: ("text" if t == "str" else ["x"]) for f, t in prompts.PLATFORM_FIELDS[Platform(p)].items()} for p in plats}}


def codes(sc, kind="hard"):
    return {h["code"] for h in sc[kind]}


def test_a_clean_kit_scores_clean():
    sc = scoring.score(FS, good_kit())
    assert sc["ok"] and sc["hard"] == [] and sc["missing_recall"] == 1.0


@pytest.mark.parametrize("field,value,code", [
    ("short_description", "A cheap candle.", "forbidden_word"),
    ("short_description", "The perfect candle for women.", "unsupported_claim"),
    ("full_description", "Burns for 60 hours.", "invented_number"),
    ("social_caption", "Meet [Store Name] today.", "placeholder"),
    ("product_title", "", "empty_required"),
])
def test_each_hard_violation_is_detected_with_its_field(field, value, code):
    kit = good_kit(); kit[field] = value
    sc = scoring.score(FS, kit)
    assert not sc["ok"] and code in codes(sc)
    hit = next(h for h in sc["hard"] if h["code"] == code)
    assert field in hit["fields"] or code == "placeholder"


def test_numbers_from_the_facts_are_allowed_in_any_format():
    kit = good_kit(); kit["full_description"] = "Only $24.00 for 45 hours."
    assert scoring.score(FS, kit)["ok"]


def test_forbidden_word_inside_the_claims_list_is_not_a_violation():
    kit = good_kit(); kit["claims_requiring_review"] = ["Forbidden word used: cheap"]
    assert scoring.score(FS, kit)["ok"]


def test_missing_info_is_scored_softly_both_ways():
    kit = good_kit(); kit["missing_information"] = ["Care / usage"]
    sc = scoring.score(FS, kit)
    assert sc["ok"] and "missed_missing_info" in codes(sc, "soft") and sc["missing_recall"] == pytest.approx(0.2)
    kit = good_kit(); kit["missing_information"] = list(FS["expected_missing"]) + ["Price"]  # Price WAS given
    assert "false_missing_info" in codes(scoring.score(FS, kit), "soft")


def test_unusable_output_is_a_hard_failure_and_aggregation_counts_kits():
    assert scoring.score(FS, None, "llm_bad_json")["hard"][0]["code"] == "invalid_output"
    bad = good_kit(); bad["short_description"] = "A cheap perfect candle"
    rows = [{"score": scoring.score(FS, good_kit()), "seconds": 10, "tokens": 100}, {"score": scoring.score(FS, bad), "seconds": 30, "tokens": 300}]
    agg = scoring.aggregate(rows)
    assert agg["n"] == 2 and agg["clean_kit_rate"] == 0.5 and agg["mean_seconds"] == 20.0 and agg["hard_rate"]["forbidden_word"] == 0.5
    assert agg["hard_violations_per_kit"] == 1.0  # (0 + 2) / 2


# ---------------- providers ----------------
def test_extract_json_handles_fences_reasoning_and_chatter():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('<think>hmm {"x":1}</think>{"a": 2}') == {"a": 2}
    assert extract_json('Sure! Here you go: {"a": 3} Hope that helps') == {"a": 3}
    for bad in ("no json here", "[1, 2]", "{broken"):
        with pytest.raises(AppError):
            extract_json(bad)


def _oai(handler, **kw):
    return OpenAICompatProvider("https://host.example/v1", "teacher-x", "k-secret", client=httpx.Client(transport=httpx.MockTransport(handler)), **kw)


def test_openai_provider_sends_auth_and_schema_and_parses_usage():
    seen = {}
    def handler(req):
        seen["auth"] = req.headers["authorization"]; seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": '```json\n{"ok": true}\n```'}}], "usage": {"prompt_tokens": 11, "completion_tokens": 5}})
    r = _oai(handler).generate_json("sys", "user", {"type": "object"})
    assert r.data == {"ok": True} and r.usage == {"prompt_tokens": 11, "completion_tokens": 5}
    assert seen["auth"] == "Bearer k-secret" and seen["body"]["response_format"]["type"] == "json_schema" and seen["body"]["messages"][0]["content"] == "sys"


def test_openai_provider_falls_back_when_host_rejects_response_format():
    modes = []
    def handler(req):
        rf = json.loads(req.content).get("response_format", {}).get("type", "none"); modes.append(rf)
        return httpx.Response(400, json={}) if rf != "none" else httpx.Response(200, json={"choices": [{"message": {"content": '{"a": 1}'}}]})
    assert _oai(handler).generate_json("s", "u", {}).data == {"a": 1}
    assert modes == ["json_schema", "json_object", "none"]


@pytest.mark.parametrize("status,code", [(401, "llm_auth"), (429, "llm_rate_limited"), (500, "llm_error")])
def test_openai_provider_maps_errors(status, code):
    with pytest.raises(AppError) as e:
        _oai(lambda req: httpx.Response(status, json={})).generate_json("s", "u", {})
    assert e.value.code == code


# ---------------- teacher loop ----------------
class FakeTeacher(LLMProvider):
    """Answers from a full kit; `fix_on_revision` controls whether a revision request repairs the problem."""
    name, model = "fake", "fake-teacher"

    def __init__(self, kit, fix_on_revision=True, fs=FS):
        self.kit, self.fix, self.fs, self.calls = kit, fix_on_revision, fs, []

    def health(self):
        return {}

    def generate_json(self, system, user, schema, *, temperature=0.4, images=None):
        self.calls.append((system, user))
        keys = list(schema["properties"])
        if "## REVISION" in user and self.fix:
            src = good_kit(self.fs)
        else:
            src = self.kit
        if keys[0] in src.get("platform_outputs", {}):
            data = {k: src["platform_outputs"][k] for k in keys}
        else:
            data = {k: src[k] for k in keys if k in src}
        return LLMResult(data=data, model="fake-teacher", usage={"prompt_tokens": 10, "completion_tokens": 5})


def test_teacher_keeps_clean_kits_and_builds_part_level_chat_examples():
    t = FakeTeacher(good_kit())
    r = teacher.build_one(t, FS)
    assert r["accepted"] and r["rounds"] == 0 and r["tokens"] == 15 * 5  # 4 core parts + 1 platform
    assert len(r["examples"]) == 5
    app_jobs = {n: u for n, _, u in CopyService(t)._chunks(ProductInput.model_validate(FS["product"]), CreativeSettings.model_validate(FS["settings"]))}
    for ex in r["examples"]:
        roles = [m["role"] for m in ex["messages"]]
        assert roles == ["system", "user", "assistant"]
        assert ex["messages"][0]["content"] == prompts.SYSTEM_PROMPT  # the student never sees the teacher note
        assert ex["messages"][1]["content"] == app_jobs[ex["meta"]["part"]]
        assert "COPYWRITING STANDARD" not in ex["messages"][1]["content"]
        out = json.loads(ex["messages"][2]["content"])
        expect = prompts.CORE_CHUNKS[int(ex["meta"]["part"][5:])] if ex["meta"]["part"].startswith("core:") else ["instagram"]
        assert sorted(out) == sorted(expect)
    assert all("COPYWRITING STANDARD" in c[0] for c in t.calls)  # but the teacher does


def test_teacher_target_uses_ground_truth_missing_information():
    kit = good_kit(); kit["missing_information"] = ["something vague"]
    r = teacher.build_one(FakeTeacher(kit), FS)
    ex = next(e for e in r["examples"] if e["meta"]["part"] == "core:2")
    assert json.loads(ex["messages"][2]["content"])["missing_information"] == FS["expected_missing"]


def test_violations_trigger_a_targeted_revision_with_the_checkers_findings():
    bad = good_kit(); bad["short_description"] = "A cheap candle"
    t = FakeTeacher(bad)
    r = teacher.build_one(t, FS)
    assert r["accepted"] and r["rounds"] == 1
    revisions = [u for _, u in t.calls if "## REVISION" in u]
    assert len(revisions) == 1  # only the part holding the problem is rewritten, not the whole kit
    assert "'cheap' is a forbidden word" in revisions[0] and "short_description" in revisions[0]
    ex = next(e for e in r["examples"] if e["meta"]["part"] == "core:0")
    assert "cheap" not in ex["messages"][2]["content"]


def test_kits_that_cannot_be_fixed_are_rejected_not_trained_on():
    bad = good_kit(); bad["short_description"] = "A cheap candle"
    r = teacher.build_one(FakeTeacher(bad, fix_on_revision=False), FS, max_revisions=2)
    assert not r["accepted"] and r["examples"] == [] and r["rounds"] == 2 and "forbidden_word" in r["reason"]


def test_teacher_tool_refuses_the_test_split():
    with pytest.raises(SystemExit):
        teacher.main(["--provider", "ollama", "--model", "x", "--split", "test"])


def test_report_renders_a_comparison_table(tmp_path):
    agg = {"n": 3, "clean_kit_rate": 0.67, "hard_violations_per_kit": 0.5, "hard_rate": {c: 0.0 for c in scoring.HARD_CODES}, "soft_rate": {},
           "missing_info_recall": 0.9, "mean_seconds": 12.5, "mean_tokens": 900}
    f = tmp_path / "a.json"; f.write_text(json.dumps({"model": "gemma3:12b", "aggregate": agg}))
    out = report.table([f])
    assert "gemma3:12b (n=3)" in out and "67%" in out and "12.5" in out
