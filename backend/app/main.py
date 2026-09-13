"""Main FastAPI Application Entrypoint for Code Archaeologist."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    routes_analysis,
    routes_files,
    routes_guidance,
    routes_historian,
    routes_knowledge,
    routes_offboarding,
    routes_repositories,
    routes_risk,
)
from app.core.config import get_settings
from app.models.db_models import init_db

logger = logging.getLogger("code_archaeologist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing database tables...")
    try:
        init_db()
    except Exception as exc:
        logger.warning("Database initialization skipped or failed: %s", exc)
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Global Exception Handlers enforcing Locked Error Format:
# { "error": { "code": "...", "message": "..." } }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    code = error_code_map.get(exc.status_code, "ERROR")

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": str(exc.detail)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    first_msg = errors[0].get("msg") if errors else "Invalid request data."
    loc = errors[0].get("loc", []) if errors else []
    field_str = " -> ".join(str(l) for l in loc if l not in ("body", "query", "path"))
    message = f"{field_str}: {first_msg}" if field_str else first_msg

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": "INVALID_REQUEST", "message": message}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
            }
        },
    )


# Register API Routers
app.include_router(routes_repositories.router)
app.include_router(routes_analysis.router)
app.include_router(routes_files.router)
app.include_router(routes_historian.router)
app.include_router(routes_guidance.router)
app.include_router(routes_risk.router)
app.include_router(routes_knowledge.router)
app.include_router(routes_offboarding.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "app": settings.app_name}
