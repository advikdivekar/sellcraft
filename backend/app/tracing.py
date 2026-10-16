"""Thin Sentry wrapper: no-ops when SENTRY_DSN is unset. Never attaches product text.

Privacy is enforced twice: callers only pass metadata (counts, ids, model names), and `_scrub` drops everything not on an
allow-list before an event leaves the machine, so a future careless `set_data("prompt", ...)` still can't leak seller facts."""
import subprocess
from contextlib import contextmanager
from pathlib import Path

import sentry_sdk

from .config import get_settings

_enabled = False
PROMPT_VERSION = "2026-10-16"  # bump when prompts.SYSTEM_PROMPT or the chunk prompts change; every event is tagged with it

# span.data keys that may leave the machine. Everything else is removed.
_ALLOWED_DATA = {"gen_ai.request.model", "gen_ai.system", "gen_ai.operation.name", "gen_ai.agent.name",
                 "gen_ai.usage.input_tokens", "gen_ai.usage.output_tokens", "gen_ai.usage.total_tokens",
                 "gen_ai.response.tokens_per_second", "latency_ms", "model", "job_id", "platforms", "photos", "style",
                 "prompt_tokens", "completion_tokens", "chunks", "retries", "flags.total", "flags.forbidden", "flags.risky",
                 "flags.regulated", "prompt_version", "source", "thread.id", "thread.name"}
_ALLOWED_TAGS_PREFIX = ("flag.", "model", "prompt_version", "job_id", "section", "reason", "runtime", "release")


def _release() -> str:
    try:
        root = Path(__file__).resolve().parents[2]
        return "sellcraft@" + subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True,
                                             timeout=2).stdout.strip()
    except Exception:  # noqa: BLE001 - a missing git must never stop the app
        return "sellcraft@dev"


def _scrub(event, _hint=None):
    """Drop anything that could carry product text: request bodies, local variables, free-form extras, non-allow-listed span data."""
    event.pop("request", None)
    event.pop("extra", None)
    event.pop("user", None)
    event["breadcrumbs"] = {"values": []}
    for sp in event.get("spans") or []:
        sp["data"] = {k: v for k, v in (sp.get("data") or {}).items() if k in _ALLOWED_DATA}
    ctx = (event.get("contexts") or {}).get("trace") or {}
    if "data" in ctx:
        ctx["data"] = {k: v for k, v in ctx["data"].items() if k in _ALLOWED_DATA}
    event["tags"] = {k: v for k, v in (event.get("tags") or {}).items() if k.startswith(_ALLOWED_TAGS_PREFIX)}
    for ex in ((event.get("exception") or {}).get("values") or []):
        if ex.get("type") != "AppError":  # AppError messages are fixed strings; others (e.g. pydantic) can echo submitted values
            ex["value"] = ""
        for fr in (ex.get("stacktrace") or {}).get("frames", []):
            fr.pop("vars", None)
    return event


def init(transport=None) -> None:
    global _enabled
    dsn = get_settings().sentry_dsn
    if dsn:
        sentry_sdk.init(dsn=dsn, traces_sample_rate=1.0, send_default_pii=False, include_local_variables=False,
                        release=_release(), environment="local", before_send=_scrub, before_send_transaction=_scrub,
                        max_request_body_size="never", transport=transport)
        sentry_sdk.set_tag("prompt_version", PROMPT_VERSION)
        _enabled = True


def enabled() -> bool:
    return _enabled


@contextmanager
def span(op: str, name: str, **data):
    """Trace one pipeline stage. `data` must be metadata only (counts, ids, model name)."""
    if not _enabled:
        yield None
        return
    with sentry_sdk.start_span(op=op, name=name) as sp:
        for k, v in data.items():
            sp.set_data(k, v)
        yield sp


def annotate(**data) -> None:
    """Add metadata to the span that is currently open (e.g. the flag counts of a finished kit)."""
    if not _enabled:
        return
    sp = sentry_sdk.get_current_span()
    if sp is not None:
        for k, v in data.items():
            sp.set_data(k, v)


def flag(kind: str, term: str, **tags) -> None:
    """Report one flagged claim as a Sentry event. Carries the rule and the matched term only, never the copy or the product facts."""
    if not _enabled:
        return
    with sentry_sdk.new_scope() as scope:
        scope.set_tag("flag.kind", kind)
        scope.set_tag("flag.term", term)
        scope.set_tag("prompt_version", PROMPT_VERSION)
        for k, v in tags.items():
            scope.set_tag(k, v)
        scope.fingerprint = ["copy-flag", kind, term]
        sentry_sdk.capture_message(f"Copy flagged ({kind}): {term}", level="warning")


def report(job_id: str, section: str, reason: str) -> None:
    """The seller pressed 'Report' on a section. Section and a fixed reason code only, so it can be matched to the job's trace."""
    if not _enabled:
        return
    with sentry_sdk.new_scope() as scope:
        scope.set_tag("job_id", job_id)
        scope.set_tag("section", section)
        scope.set_tag("reason", reason)
        scope.fingerprint = ["seller-report", section, reason]
        sentry_sdk.capture_message(f"Seller reported {section}: {reason}", level="warning")
