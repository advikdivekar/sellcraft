import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import db, tracing
from .api.routes import router
from .config import get_settings
from .errors import AppError

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


@app.exception_handler(AppError)
async def app_error(_: Request, e: AppError):
    return JSONResponse(status_code=e.status, content={"error": {"code": e.code, "message": e.message, "retryable": e.retryable}})


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, e: RequestValidationError):
    # Only field locations + messages: never echo submitted values back.
    fields = [{"field": ".".join(str(p) for p in err["loc"] if p != "body"), "message": err["msg"]} for err in e.errors()]
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "Please check the highlighted fields.", "fields": fields}})
