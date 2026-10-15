"""Thin Sentry wrapper: no-ops when SENTRY_DSN is unset. Never attaches product text."""
from contextlib import contextmanager

import sentry_sdk

from .config import get_settings

_enabled = False


def init() -> None:
    global _enabled
    dsn = get_settings().sentry_dsn
    if dsn:
        sentry_sdk.init(dsn=dsn, traces_sample_rate=1.0, send_default_pii=False)
        _enabled = True


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
