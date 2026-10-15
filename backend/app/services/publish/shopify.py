"""Publish a finished kit to a Shopify store as a DRAFT product (Admin GraphQL API).
Draft only: the seller reviews and publishes inside Shopify. The token lives on the backend and is never
returned to the browser. Written against Shopify's documented stagedUploadsCreate + productCreate flow; it is
unit-tested with a mocked transport, not yet run against a live store."""
import logging
import re
from pathlib import Path

import httpx

from ...config import get_settings
from ...errors import AppError
from ...schemas import CopyOutput
from ..export import listing_html

log = logging.getLogger("sellcraft.shopify")
DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.myshopify\.com$")

STAGED = """mutation($input: [StagedUploadInput!]!) {
  stagedUploadsCreate(input: $input) {
    stagedTargets { url resourceUrl parameters { name value } }
    userErrors { field message }
  }
}"""
CREATE = """mutation($product: ProductCreateInput!, $media: [CreateMediaInput!]) {
  productCreate(product: $product, media: $media) {
    product { id handle }
    userErrors { field message }
  }
}"""


class ShopifyPublisher:
    def __init__(self, domain: str | None = None, token: str | None = None, version: str | None = None,
                 client: httpx.Client | None = None):
        s = get_settings()
        self.domain = (domain if domain is not None else s.shopify_store_domain).strip().lower()
        self.token = token if token is not None else s.shopify_admin_token
        self.version = version or s.shopify_api_version
        self.client = client or httpx.Client(timeout=60)

    @property
    def configured(self) -> bool:
        return bool(self.domain and self.token and DOMAIN_RE.match(self.domain))

    def _gql(self, query: str, variables: dict) -> dict:
        try:
            r = self.client.post(f"https://{self.domain}/admin/api/{self.version}/graphql.json",
                                 json={"query": query, "variables": variables},
                                 headers={"X-Shopify-Access-Token": self.token})
        except httpx.HTTPError:
            raise AppError("shopify_unreachable", "Couldn't reach your Shopify store. Check the store domain and your connection.",
                           retryable=True, status=502)
        if r.status_code in (401, 403):
            raise AppError("shopify_auth", "Shopify rejected the access token. Check SHOPIFY_ADMIN_TOKEN and its product/file write scopes.", status=502)
        if r.status_code == 429:
            raise AppError("shopify_rate_limited", "Shopify is rate limiting requests. Try again in a moment.", retryable=True, status=429)
        if r.status_code >= 400:
            raise AppError("shopify_error", f"Shopify returned an error (HTTP {r.status_code}).", retryable=True, status=502)
        body = r.json()
        if body.get("errors"):
            raise AppError("shopify_error", "Shopify rejected the request: " + "; ".join(str(e.get("message", e)) for e in body["errors"])[:300], status=502)
        return body["data"]

    @staticmethod
    def _user_errors(payload: dict) -> None:
        errs = payload.get("userErrors") or []
        if errs:
            raise AppError("shopify_rejected", "Shopify said: " + "; ".join(e.get("message", "") for e in errs)[:300], status=422)

    def _upload(self, files: list[tuple[Path, str, str]]) -> list[tuple[str, str]]:
        """files: (path, mime, 'IMAGE'|'VIDEO') -> [(resourceUrl, mediaContentType)]"""
        if not files:
            return []
        inp = [{"filename": p.name, "mimeType": mime, "httpMethod": "POST", "resource": kind, "fileSize": str(p.stat().st_size)}
               for p, mime, kind in files]
        payload = self._gql(STAGED, {"input": inp})["stagedUploadsCreate"]
        self._user_errors(payload)
        out = []
        for (path, mime, kind), t in zip(files, payload["stagedTargets"]):
            data = {p["name"]: p["value"] for p in t["parameters"]}
            try:
                with path.open("rb") as fh:
                    r = self.client.post(t["url"], data=data, files={"file": (path.name, fh, mime)})
                r.raise_for_status()
            except httpx.HTTPError:
                raise AppError("shopify_upload_failed", "Uploading media to Shopify failed. Please retry.", retryable=True, status=502)
            out.append((t["resourceUrl"], kind))
        return out

    def publish_draft(self, *, title: str, brand: str | None, copy: CopyOutput, images: list[Path], video: Path | None) -> dict:
        if not self.configured:
            raise AppError("shopify_not_configured", "Shopify isn't connected. Set SHOPIFY_STORE_DOMAIN and SHOPIFY_ADMIN_TOKEN.", status=409)
        files = [(p, "image/jpeg", "IMAGE") for p in images if p.is_file()] + ([(video, "video/mp4", "VIDEO")] if video and video.is_file() else [])
        uploaded = self._upload(files)
        product = {"title": (copy.product_title or title)[:255], "descriptionHtml": listing_html(copy), "status": "DRAFT",
                   "tags": [t for t in copy.tags if t][:20], "seo": {"title": copy.seo_title[:70], "description": copy.meta_description[:320]}}
        if brand:
            product["vendor"] = brand[:255]
        media = [{"originalSource": url, "mediaContentType": kind, "alt": (copy.product_title or title)[:250]} for url, kind in uploaded]
        payload = self._gql(CREATE, {"product": product, "media": media})["productCreate"]
        self._user_errors(payload)
        gid = payload["product"]["id"]  # gid://shopify/Product/123
        return {"product_id": gid, "media_attached": len(media),
                "admin_url": f"https://{self.domain}/admin/products/{gid.rsplit('/', 1)[-1]}"}
