from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from ui_server.api import clustering, corpus, geography, models, similarity
from ui_server.config import paths


def create_app() -> FastAPI:
    app = FastAPI(
        title="MythoSemantic UI Server",
        default_response_class=ORJSONResponse,
    )

    app.add_middleware(GZipMiddleware, minimum_size=1024)

    app.include_router(models.router)
    app.include_router(corpus.router)
    app.include_router(geography.router)
    app.include_router(similarity.router)
    app.include_router(clustering.router)

    if paths.assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(paths.assets_dir)), name="assets")
    if paths.analysis_dir.exists():
        app.mount("/analysis", StaticFiles(directory=str(paths.analysis_dir)), name="analysis")
    if paths.template_dir.exists():
        app.mount("/template", StaticFiles(directory=str(paths.template_dir)), name="template")
    if paths.corpus_dir.exists():
        app.mount("/corpus", StaticFiles(directory=str(paths.corpus_dir)), name="corpus")
    if paths.corpus_chunked_dir.exists():
        app.mount("/corpus_chunked", StaticFiles(directory=str(paths.corpus_chunked_dir)), name="corpus_chunked")

    @app.middleware("http")
    async def add_cache_headers(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path

        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        elif path.startswith("/assets/"):
            response.headers["Cache-Control"] = "no-store"
        elif path.startswith(("/analysis/", "/template/", "/corpus/", "/corpus_chunked/")):
            response.headers["Cache-Control"] = "public, max-age=86400"
        else:
            response.headers["Cache-Control"] = "no-cache"

        return response

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/")
    def index():
        return _index_response()

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        return _index_response()

    return app


def _index_response():
    return FileResponse(paths.web_root / "index.html")




def run_server():
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)


def main():
    run_server()
