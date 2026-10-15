from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    ollama_timeout: float = 240.0
    vision_model: str = ""  # defaults to OLLAMA_MODEL; must be a multimodal model (Gemma 3 is)
    demo_mode: bool = False

    cutout_model: str = "silueta"  # rembg model: silueta (44 MB, fast) or u2net (176 MB, slightly cleaner edges)
    video_provider: str = "fallback"
    video_provider_url: str = ""
    video_provider_api_key: str = ""

    elevenlabs_api_key: str = ""
    elevenlabs_default_voice_id: str = ""

    shopify_store_domain: str = ""  # e.g. my-store.myshopify.com
    shopify_admin_token: str = ""  # custom-app Admin API token (shpat_...). Backend only.
    shopify_api_version: str = "2026-07"

    access_code: str = ""  # if set, every API call needs it (cookie or X-Access-Code header). dev-phone.sh sets one.
    secret_key: str = ""  # Fernet key for stored connection tokens; auto-generated into data/.secret if empty

    sentry_dsn: str = ""

    upload_dir: Path = Path("data/uploads")
    output_dir: Path = Path("data/outputs")
    database_url: str = "sqlite:///data/sellcraft.db"
    max_upload_mb: int = 10

    cors_origins: str = "http://localhost:3000"

    def resolve(self, p: Path) -> Path:
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def upload_path(self) -> Path:
        return self.resolve(self.upload_dir)

    @property
    def output_path(self) -> Path:
        return self.resolve(self.output_dir)

    @property
    def db_path(self) -> Path:
        raw = self.database_url.removeprefix("sqlite:///")
        return self.resolve(Path(raw))


@lru_cache
def get_settings() -> Settings:
    return Settings()
