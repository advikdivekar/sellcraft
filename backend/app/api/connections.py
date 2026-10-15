import json

from fastapi import APIRouter

from .. import db
from ..config import get_settings
from ..errors import AppError
from ..schemas import ConnectShopifyRequest
from ..services import vault
from ..services.publish.shopify import ShopifyPublisher, normalize_domain

router = APIRouter(prefix="/api/connections")


def _shopify_state() -> dict:
    row = db.get_connection("shopify")
    if row and vault.decrypt(row["secret_enc"]):
        return {"provider": "shopify", "connected": True, "label": row["label"], "source": "app"}
    s = get_settings()
    if ShopifyPublisher().configured:
        return {"provider": "shopify", "connected": True, "label": s.shopify_store_domain, "source": "env"}
    return {"provider": "shopify", "connected": False, "label": None, "source": None}


@router.get("")
def list_connections():
    """Which stores are connected. Never includes tokens."""
    return [_shopify_state()]


@router.post("/shopify")
def connect_shopify(req: ConnectShopifyRequest):
    domain = normalize_domain(req.domain)
    token = req.token.strip()
    if not token:
        raise AppError("token_required", "Paste the Admin API access token from your Shopify app.", status=422)
    info = ShopifyPublisher(domain, token).verify()  # raises a clear error if the store/token/scopes are wrong
    label = f'{info["name"]} ({info["domain"]})'
    db.save_connection("shopify", label, vault.encrypt(token), {"domain": info["domain"]})
    return _shopify_state()


@router.delete("/shopify")
def disconnect_shopify():
    db.delete_connection("shopify")
    return _shopify_state()
