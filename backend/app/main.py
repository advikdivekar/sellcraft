import logging
from contextlib import asynccontextmanager

import hmac

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import db, tracing
from .api.connections import router as connections_router
from .api.routes import router
from .config import get_settings
from .errors import AppError
from .schemas import AccessRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    s = get_settings()
    s.upload_path.mkdir(parents=True, exist_ok=True)
    s.output_path.mkdir(parents=True, exist_ok=True)
    db.init_db()
    tracing.init()
    yield


app = FastAPI(title="SellCraft AI", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins.split(","),
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
app.include_router(connections_router)


@app.exception_handler(AppError)
async def app_error(_: Request, e: AppError):
    return JSONResponse(status_code=e.status, content={"error": {"code": e.code, "message": e.message, "retryable": e.retryable}})


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, e: RequestValidationError):
    # Only field locations + messages: never echo submitted values back.
    fields = [{"field": ".".join(str(p) for p in err["loc"] if p != "body"), "message": err["msg"]} for err in e.errors()]
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "Please check the highlighted fields.", "fields": fields}})


COOKIE = "sc_access"


def _granted(request: Request) -> bool:
    code = get_settings().access_code
    if not code:
        return True
    given = request.cookies.get(COOKIE) or request.headers.get("x-access-code") or ""
    return hmac.compare_digest(given.encode(), code.encode())


@app.middleware("http")
async def access_gate(request: Request, call_next):
    """Optional shared secret. Used when the app is reachable from outside (the phone tunnel): without it,
    anyone who learned the URL could spend your GPU or publish to your store."""
    path = request.url.path
    if path.startswith("/api/") and path not in ("/api/health", "/api/access") and request.method != "OPTIONS" and not _granted(request):
        return JSONResponse(status_code=401, content={"error": {"code": "access_required", "message": "Enter the access code to use this app.", "retryable": False}})
    return await call_next(request)


@app.get("/api/access")
async def access_status(request: Request):
    return {"required": bool(get_settings().access_code), "granted": _granted(request)}


@app.post("/api/access")
async def access_login(req: AccessRequest, request: Request):
    code = get_settings().access_code
    if code and not hmac.compare_digest(req.code.strip().encode(), code.encode()):
        return JSONResponse(status_code=401, content={"error": {"code": "bad_code", "message": "That code isn't right.", "retryable": False}})
    resp = JSONResponse({"required": bool(code), "granted": True})
    if code:
        secure = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
        resp.set_cookie(COOKIE, code, httponly=True, samesite="lax", secure=secure, max_age=60 * 60 * 24 * 30)
    return resp
