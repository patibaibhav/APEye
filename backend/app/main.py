"""FastAPI application factory and server entry point (Owner: Baibhav).

Wires settings, logging, middleware order, central router, and error handlers.
"""

from typing import Callable, Optional

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.logging_config import configure_logging, get_ops_logger
from app.middleware.request_logging import RequestLoggingMiddleware
from app.schemas.detection import RequestEvent


def create_app(
    settings: Optional[Settings] = None,
    ingest_callable: Optional[Callable[[RequestEvent], None]] = None,
) -> FastAPI:
    """Application factory creating a configured FastAPI instance."""
    cfg = settings or get_settings()

    # 1. Configure operational JSON logger
    configure_logging(cfg.log_level)
    ops_logger = get_ops_logger()
    ops_logger.info("application_startup", extra={"extra_fields": {"env": cfg.app_env}})

    # 2. Instantiate FastAPI app
    application = FastAPI(
        title="APEye - API Security Monitoring Platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Store settings on state and provide to dependencies
    application.state.settings = cfg
    application.dependency_overrides[get_settings] = lambda: cfg

    # 3. Register global error handlers (never expose stack traces)
    register_error_handlers(application)

    # 4. Mount API router under /api
    application.include_router(api_router, prefix="/api")

    # 4b. Configure SPA static files and fallback routing
    from app.static_site import configure_static_site
    configure_static_site(application, cfg.static_dir)

    # 5. Determine event ingestion callable for middleware
    if ingest_callable is not None:
        ingest_func = ingest_callable
    else:
        def _runtime_ingest(event: RequestEvent) -> None:
            try:
                from app.db.session import SessionLocal
                from app.detection.engine import build_default_engine
                from app.services.ingestion_service import IngestionService

                engine = build_default_engine(cfg.detection)
                service = IngestionService(
                    session_factory=SessionLocal,
                    engine=engine,
                    settings=cfg,
                )
                service.ingest(event)
            except Exception as exc:
                ops_logger.error(
                    "runtime_ingest_initialization_error",
                    extra={"extra_fields": {"error": f"{type(exc).__name__}: {exc}"}},
                )

        ingest_func = _runtime_ingest

    # 6. Add RequestLoggingMiddleware (wrap outer ASGI layer)
    application.add_middleware(
        RequestLoggingMiddleware,
        ingest=ingest_func,
        trusted_proxy_count=cfg.trusted_proxy_count,
        ignored_paths=frozenset({"/api/health"}),
    )

    return application


# Global application entry point for Uvicorn
app = create_app()
