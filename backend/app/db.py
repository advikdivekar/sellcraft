import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import get_settings
from .schemas import CreativeSettings, GeneratedAsset, GenerationJob, JobStatus, StageEntry, overall_progress

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  product TEXT NOT NULL,
  settings TEXT NOT NULL,
  copy_output TEXT,
  copy_source TEXT,
  error TEXT,
  stages TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS connections (
  provider TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  secret_enc TEXT NOT NULL,
  meta TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assets (
  id TEXT PRIMARY KEY,
  job_id TEXT,
  kind TEXT NOT NULL,
  mime TEXT NOT NULL,
  method TEXT,
  duration_seconds REAL,
  path TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


def now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid.uuid4().hex


@contextmanager
def connect():
    path = get_settings().db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as c:
        c.executescript(SCHEMA)


def _asset(row: sqlite3.Row) -> GeneratedAsset:
    return GeneratedAsset(
        id=row["id"], kind=row["kind"], mime=row["mime"], method=row["method"],
        duration_seconds=row["duration_seconds"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _job(row: sqlite3.Row, assets: list[GeneratedAsset]) -> GenerationJob:
    stages = [StageEntry.model_validate(x) for x in json.loads(row["stages"])]
    progress, phase = overall_progress(stages, CreativeSettings.model_validate(json.loads(row["settings"])), JobStatus(row["status"]))
    return GenerationJob.model_validate({
        "progress": progress, "phase": phase,
        "id": row["id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "product": json.loads(row["product"]),
        "settings": json.loads(row["settings"]),
        "copy_output": json.loads(row["copy_output"]) if row["copy_output"] else None,
        "copy_source": row["copy_source"],
        "error": json.loads(row["error"]) if row["error"] else None,
        "stages": json.loads(row["stages"]),
        "assets": [a.model_dump() for a in assets],
    })


def create_job(product, settings) -> str:
    job_id = new_id()
    ts = now().isoformat()
    with connect() as c:
        c.execute(
            "INSERT INTO jobs (id,status,created_at,updated_at,product,settings) VALUES (?,?,?,?,?,?)",
            (job_id, JobStatus.queued.value, ts, ts, product.model_dump_json(), settings.model_dump_json()),
        )
    return job_id


def get_job(job_id: str) -> GenerationJob | None:
    with connect() as c:
        row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return None
        assets = [_asset(r) for r in c.execute(
            "SELECT * FROM assets WHERE job_id=? AND kind NOT IN ('clip', 'product_src') ORDER BY created_at", (job_id,))]
    return _job(row, assets)


def update_job(job_id: str, **fields) -> None:
    """fields: status, copy_output (model|None), copy_source, error (model|None), stages (list of models)."""
    cols, vals = ["updated_at"], [now().isoformat()]
    for k, v in fields.items():
        if k == "status":
            v = v.value if hasattr(v, "value") else v
        elif k in ("copy_output", "error", "settings"):
            v = v.model_dump_json() if v is not None else None
        elif k == "stages":
            v = json.dumps([s.model_dump(mode="json") for s in v])
        cols.append(k)
        vals.append(v)
    with connect() as c:
        c.execute(f"UPDATE jobs SET {', '.join(f'{c_}=?' for c_ in cols)} WHERE id=?", (*vals, job_id))


def add_asset(*, kind, mime, path, method=None, duration_seconds=None, job_id=None, asset_id=None) -> str:
    asset_id = asset_id or new_id()
    with connect() as c:
        c.execute(
            "INSERT INTO assets (id,job_id,kind,mime,method,duration_seconds,path,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (asset_id, job_id, kind, mime, method, duration_seconds, str(path), now().isoformat()),
        )
    return asset_id


def get_asset_row(asset_id: str) -> sqlite3.Row | None:
    with connect() as c:
        return c.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()


def attach_asset(asset_id: str, job_id: str) -> bool:
    """Attach an unattached upload to a job. Returns False if missing or already owned."""
    with connect() as c:
        cur = c.execute("UPDATE assets SET job_id=? WHERE id=? AND job_id IS NULL", (job_id, asset_id))
        return cur.rowcount == 1


def list_asset_rows(job_id: str, kinds: tuple[str, ...]) -> list[sqlite3.Row]:
    marks = ",".join("?" * len(kinds))
    with connect() as c:
        return list(c.execute(f"SELECT * FROM assets WHERE job_id=? AND kind IN ({marks})", (job_id, *kinds)))


def delete_asset(asset_id: str) -> None:
    with connect() as c:
        c.execute("DELETE FROM assets WHERE id=?", (asset_id,))


def save_connection(provider: str, label: str, secret_enc: str, meta: dict) -> None:
    with connect() as c:
        c.execute("INSERT OR REPLACE INTO connections (provider,label,secret_enc,meta,created_at) VALUES (?,?,?,?,?)",
                  (provider, label, secret_enc, json.dumps(meta), now().isoformat()))


def get_connection(provider: str) -> sqlite3.Row | None:
    with connect() as c:
        return c.execute("SELECT * FROM connections WHERE provider=?", (provider,)).fetchone()


def delete_connection(provider: str) -> bool:
    with connect() as c:
        return c.execute("DELETE FROM connections WHERE provider=?", (provider,)).rowcount > 0
