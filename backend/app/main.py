from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import time
import logging

from app.core.config import get_settings
from app.core.database import init_db, async_session
from app.core.rate_limiter import RateLimiter
from app.api.routes import worksheets, analysis, reports, auth, tracking, children, dashboard, parent
from app.models import Child
from sqlalchemy import select, func

# ─── Rate limiter (singleton, created once at import) ──────────────

rate_limiter = RateLimiter()

# ─── Logging setup ────────────────────────────────────────────────────

try:
    import structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logger = structlog.get_logger("mathsprout")
    USE_STRUCTLOG = True
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("mathsprout")
    USE_STRUCTLOG = False


# ─── Lifespan ─────────────────────────────────────────────────────────

async def seed_demo_children():
    """Insert demo children if the table is empty (development only)."""
    async with async_session() as db:
        try:
            result = await db.execute(select(func.count(Child.id)))
            count = result.scalar()
            if count and count > 0:
                return  # Already seeded

            demo_children = [
                Child(
                    name="小明",
                    age_group="middle",
                    class_name="中一班",
                    parent_access_code="XIAOMING01",
                    notes="活泼好动，喜欢数学游戏",
                ),
                Child(
                    name="小红",
                    age_group="large",
                    class_name="大一班",
                    parent_access_code="XIAOHONG02",
                    notes="专注力好，图形认知强",
                ),
                Child(
                    name="小华",
                    age_group="small",
                    class_name="小一班",
                    parent_access_code="XIAOHUA003",
                    notes="刚入园，需要适应",
                ),
            ]
            for child in demo_children:
                db.add(child)
            await db.commit()
            logger.info("🌱 Demo children seeded successfully.")
        except Exception as e:
            await db.rollback()
            logger.warning(f"Seed demo children skipped: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.REPORT_DIR, exist_ok=True)
    os.makedirs("./cache/images", exist_ok=True)
    os.makedirs("./cache/assessments", exist_ok=True)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")
    logger.info(f"   Upload dir: {settings.UPLOAD_DIR}")
    await init_db()  # Auto-create tables on startup

    # Seed demo data in development
    if settings.ENVIRONMENT == "development":
        await seed_demo_children()

    yield
    # Shutdown
    logger.info("👋 Shutting down...")


# ─── Global exception handlers ────────────────────────────────────────

async def _http_exception_handler(request: Request, exc: HTTPException):
    """Structured HTTP error response."""
    logger.warning(
        f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
        },
    )


async def _validation_exception_handler(request: Request, exc: Exception):
    """Handle Pydantic validation errors (422)."""
    detail = str(exc)
    # Extract field-level errors from pydantic ValidationError
    errors = []
    if hasattr(exc, "errors"):
        for err in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
            })
    logger.warning(f"Validation error on {request.method} {request.url.path}: {errors}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "status_code": 422,
            "detail": "请求数据验证失败",
            "validation_errors": errors,
            "path": request.url.path,
        },
    )


async def _general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected errors."""
    logger.error(
        f"Unhandled error on {request.method} {request.url.path}: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "detail": "服务器内部错误，请稍后重试",
            "error_type": type(exc).__name__,
            "path": request.url.path,
        },
    )


# ─── Request logging middleware ───────────────────────────────────────

async def _request_logging_middleware(request: Request, call_next):
    """Log all requests with timing information."""
    start_time = time.perf_counter()

    # Log the incoming request
    logger.info(f"→ {request.method} {request.url.path}")

    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"✗ {request.method} {request.url.path} — "
            f"{type(exc).__name__} ({elapsed_ms:.0f}ms)"
        )
        raise

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    status_code = response.status_code

    # Log response
    if status_code >= 500:
        logger.error(f"← {status_code} {request.method} {request.url.path} ({elapsed_ms:.0f}ms)")
    elif status_code >= 400:
        logger.warning(f"← {status_code} {request.method} {request.url.path} ({elapsed_ms:.0f}ms)")
    else:
        logger.info(f"← {status_code} {request.method} {request.url.path} ({elapsed_ms:.0f}ms)")

    return response


# ─── App factory ──────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # ── Middleware (order matters: last added = outermost) ──

    # CORS — outermost
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiter — runs after CORS, before logging
    app.middleware("http")(rate_limiter.middleware)

    # Request logging — innermost (runs first on request, last on response)
    app.middleware("http")(_request_logging_middleware)

    # ── Exception handlers ──

    app.add_exception_handler(HTTPException, _http_exception_handler)
    # Import here to avoid circular imports
    try:
        from fastapi.exceptions import RequestValidationError
        app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    except ImportError:
        pass
    app.add_exception_handler(Exception, _general_exception_handler)

    # ── Static files ──

    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    # ── Routes ──

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(worksheets.router, prefix="/api/v1/worksheets", tags=["Worksheets"])
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
    app.include_router(tracking.router, prefix="/api/v1/tracking", tags=["Tracking"])
    app.include_router(children.router, prefix="/api/v1/children", tags=["Children"])

    app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
    app.include_router(parent.router, prefix="/api/v1/parent", tags=["Parent"])

    # ── Health & Stats ──

    @app.get("/api/health")
    async def health_check():
        from app.core.database import check_db_connection
        db_ok = await check_db_connection()
        status = "ok" if db_ok else "degraded"
        return {
            "status": status,
            "version": settings.APP_VERSION,
            "database": "connected" if db_ok else "disconnected",
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/api/stats")
    async def db_stats():
        from app.core.database import get_db_stats
        return await get_db_stats()

    return app


app = create_app()
