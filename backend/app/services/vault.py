"""Encrypts connection secrets (like a Shopify token) before they touch SQLite.
Key: SECRET_KEY env if set, otherwise generated once into data/.secret (mode 0600). Secrets are never returned
by any API; only a label is. Protects a copied database file, not a compromised server."""
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from ..config import get_settings


def _key() -> bytes:
    s = get_settings()
    if s.secret_key:
        return s.secret_key.encode()
    path: Path = s.db_path.parent / ".secret"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(Fernet.generate_key())
    return path.read_bytes().strip()


def encrypt(text: str) -> str:
    return Fernet(_key()).encrypt(text.encode()).decode()


def decrypt(token: str) -> str | None:
    try:
        return Fernet(_key()).decrypt(token.encode()).decode()
    except InvalidToken:
        return None  # key changed or data tampered with: treat as not connected
