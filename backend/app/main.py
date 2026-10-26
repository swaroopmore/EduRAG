import threading
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.api import api_router
from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger("app")


def _background_startup() -> None:
    """Warm heavy models and reconcile documents without blocking the first request."""
    try:
        if settings.PRELOAD_MODELS:
            from app.ai.embeddings.embedding_service import get_embeddings
            from app.ai.reranker.reranker import get_reranker

            get_embeddings()
            get_reranker()
        if settings.RUN_STARTUP_RECOVERY:
            from app.services.ingestion_service import recover_documents

            recover_documents()
    except Exception:  # noqa: BLE001
        logger.exception("background startup tasks failed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.is_production:
        if len(settings.SECRET_KEY) < 32:
            logger.warning("SECRET_KEY is shorter than 32 characters - use a long random value in production")
        if settings.cors_origins_list == ["*"]:
            logger.warning("CORS_ORIGINS is '*' - set it to your frontend origin(s) in production")
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set - AI features will be unavailable")
    logger.info(
        "EduRAG %s starting (env=%s, vector_db=%s, uploads=%s)",
        settings.PROJECT_VERSION, settings.ENVIRONMENT, settings.VECTOR_DB_PATH, settings.UPLOAD_DIR,
    )
    threading.Thread(target=_background_startup, name="startup", daemon=True).start()
    yield
    from app.services.ingestion_service import ingestion_queue

    ingestion_queue.shutdown()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI Teacher using Retrieval-Augmented Generation",
    lifespan=lifespan,
)

@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = uuid.uuid4().hex[:12]
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:  # noqa: BLE001 - keep CORS headers on 500s (CORS wraps this middleware)
        logger.exception("unhandled error on %s %s rid=%s", request.method, request.url.path, request_id)
        response = _error(500, "Something went wrong on our side. Please try again.", "internal_error", request)
    elapsed = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path not in ("/health",):
        logger.info("%s %s -> %s %.0fms rid=%s", request.method, request.url.path, response.status_code, elapsed, request_id)
    return response


def _error(status: int, detail: str, code: str, request: Request | None = None, **extra) -> JSONResponse:
    body = {"detail": detail, "code": code, **extra}
    if request is not None and getattr(request.state, "request_id", None):
        body["request_id"] = request.state.request_id
    return JSONResponse(status_code=status, content=body)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    response = _error(exc.status_code, exc.message, exc.code, request)
    if headers:
        response.headers.update(headers)
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(p) for p in first.get("loc", []) if p not in ("body", "query", "path"))
    message = str(first.get("msg", "Invalid input")).removeprefix("Value error, ")
    detail = f"{field.replace('_', ' ').capitalize()}: {message}" if field else message
    return _error(422, detail, "validation_error", request)


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception(
        "unhandled error on %s %s rid=%s", request.method, request.url.path, getattr(request.state, "request_id", "-")
    )
    return _error(
        500,
        "Something went wrong on our side. Please try again.",
        "internal_error",
        request,
    )


# Auth uses bearer tokens (no cookies), so credentialed CORS is not needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


app.include_router(api_router)
