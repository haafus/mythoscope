import uvicorn
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.api import corpus, graphs, motifs, similarity
from settings import settings


def create_app() -> FastAPI:
    app = FastAPI(title="MythoScope UI Server")

    srv = settings.server
    app.add_middleware(GZipMiddleware, minimum_size=srv.gzip_minimum_size)

    app.include_router(corpus.router)
    app.include_router(graphs.router)
    app.include_router(motifs.router)
    app.include_router(similarity.router)

    assets_dir = settings.web_root / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(settings.web_root / "index.html")

    return app


def run_server(host: str | None = None, port: int | None = None) -> None:
    srv = settings.server
    uvicorn.run("main:app", host=host or srv.host, port=port or srv.port, reload=False)
