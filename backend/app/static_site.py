"""Single Page Application static file serving with fallback to index.html (Owner: Baibhav).

Follows Blueprint Section 4 & 6.2:
- Serves built React artifacts from STATIC_DIR
- Falls back to index.html for client-side routing on all non-API paths
- Deep link e.g. /alerts, /dashboard reloads cleanly in browser
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def configure_static_site(app: FastAPI, static_dir: str) -> None:
    """Configures SPA static file serving and fallback routing on FastAPI app."""
    resolved_path = Path(static_dir)
    if not resolved_path.is_absolute():
        # Resolve relative to current working directory or backend root
        backend_static = Path(__file__).parent / "static"
        if backend_static.is_dir():
            resolved_path = backend_static
        else:
            resolved_path = Path.cwd() / static_dir

    if not resolved_path.is_dir():
        return

    index_html = resolved_path / "index.html"
    assets_dir = resolved_path / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.middleware("http")
    async def spa_fallback_middleware(request: Request, call_next):
        # Allow API routes, docs, and assets to be handled normally
        path = request.url.path
        if (
            path.startswith("/api")
            or path.startswith("/docs")
            or path.startswith("/redoc")
            or path.startswith("/openapi.json")
            or path.startswith("/assets")
        ):
            return await call_next(request)

        # Check if requested path is a real file in static root (e.g. favicon.ico, vite.svg)
        candidate_file = resolved_path / path.lstrip("/")
        if candidate_file.is_file():
            return FileResponse(str(candidate_file))

        # Otherwise, if index.html exists, serve it for client-side routing fallback
        if index_html.is_file():
            return FileResponse(str(index_html))

        return await call_next(request)
