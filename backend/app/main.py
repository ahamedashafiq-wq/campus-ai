from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.services.errors import AppError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("campusmatch")
settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("CampusMatch AI starting env=%s", settings.app_env)
    yield


app = FastAPI(
    title="CampusMatch AI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(AppError)
async def app_error_handler(_, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.message, "code": exc.code})


@app.exception_handler(Exception)
async def unhandled(_, exc: Exception):
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"error": "Internal server error", "code": "internal"})


app.include_router(api_router, prefix=settings.api_prefix)
# health also at root for compose
from app.api.v1.routes.health import health as health_root  # noqa: E402

app.add_api_route("/health", health_root, methods=["GET"])
