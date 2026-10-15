import io
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from .. import db
from ..config import get_settings
from ..errors import AppError

ALLOWED = {"JPEG": ("image/jpeg", "jpg"), "PNG": ("image/png", "png"), "WEBP": ("image/webp", "webp")}
MAX_PIXELS = 40_000_000


def save_upload(file: UploadFile) -> dict:
    """Validate by content (not filename/header), re-encode, store under a generated name."""
    s = get_settings()
    max_bytes = s.max_upload_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if not data:
        raise AppError("empty_file", "The uploaded file is empty.")
    if len(data) > max_bytes:
        raise AppError("file_too_large", f"Image is larger than {s.max_upload_mb} MB.", status=413)
    try:
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format
            if probe.width * probe.height > MAX_PIXELS:
                raise AppError("image_too_large", "Image dimensions are too large.")
        if fmt not in ALLOWED:
            raise AppError("unsupported_type", "Use a JPEG, PNG or WebP image.", status=415)
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise AppError("invalid_image", "That file isn't a valid JPEG, PNG or WebP image.", status=415)

    mime, ext = ALLOWED[fmt]
    if fmt == "JPEG" and img.mode != "RGB":
        img = img.convert("RGB")
    asset_id = db.new_id()
    dest: Path = s.upload_path / f"{asset_id}.{ext}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, format=fmt, **({"quality": 92} if fmt == "JPEG" else {}))
    db.add_asset(kind="image", mime=mime, path=dest, method="upload", asset_id=asset_id)
    return {"asset_id": asset_id, "width": img.width, "height": img.height, "mime": mime}


def asset_file(row) -> Path:
    """Resolve an asset row to a file, refusing anything outside the managed directories."""
    s = get_settings()
    p = Path(row["path"]).resolve()
    for root in (s.upload_path.resolve(), s.output_path.resolve()):
        if p.is_relative_to(root) and p.is_file():
            return p
    raise AppError("asset_missing", "Asset file not found.", status=404)
