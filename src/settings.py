from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# Load .env into os.environ so non-MYTHO_ keys (OPENAI_API_KEY, HF_TOKEN, …)
# reach the SDKs; real environment variables take precedence (override=False).
for _env_file in (".env", "config/.env"):
    load_dotenv(_env_file)

# ---------------------------------------------------------------------------
# Sub-models (BaseModel — not BaseSettings, nested inside Settings)
# ---------------------------------------------------------------------------


class CorpusSettings(BaseModel):
    max_workers: int = 10
    timeout_connect: int = 10
    timeout_read: int = 30
    retry_total: int = 4
    retry_backoff_factor: float = 1.5
    retry_status_forcelist: list[int] = [429, 500, 502, 503, 504]
    html_include_comments: bool = False
    html_include_tables: bool = True
    pdf_extract_tables: bool = False
    pdf_preserve_layout: bool = True


class EmbeddingSettings(BaseModel):
    chunk_size: int = 1024
    chunk_overlap: int = 128
    batch_size: int = 32
    max_workers: int = 16


class LLMSettings(BaseModel):
    model: str = "gpt4o-mini"
    temperature: float = 0.1
    max_retries: int = 5


class GraphsSettings(BaseModel):
    use_json_mode: bool = True
    chunk_size: int = 4000
    chunk_overlap: int = 1000
    # Chunks processed in parallel; the rate limiter is the real throttle, this just
    # bounds in-flight work. Each chunk now makes its 4 LLM calls sequentially, so
    # concurrency lives entirely here (overshoot is harmless — the buckets throttle).
    # 18 keeps a typical gpt-4o-mini run near its TPM ceiling rather than latency-bound.
    max_concurrent: int = 18
    # Keep only the N most-mentioned entities in each graph (None = keep all).
    max_entities: int | None = 50


class MotifsSettings(BaseModel):
    # Concurrent HTTP fetches when scraping Berezkin detail pages.
    max_workers: int = 10
    # Fetch + parse Berezkin per-motif detail pages (definitions). The motif
    # backbone (codes, names, areas) is always built from the single index page;
    # details add the short definition at the cost of one request per motif.
    berezkin_details: bool = True
    # Cap motifs whose detail pages are fetched (None = all). Used by `build --sample`.
    max_motifs: int | None = None


class ProjectionsSettings(BaseModel):
    umap_n_neighbors: int = 15
    umap_min_dist: float = 0.1
    # Summaries processed in parallel (one LLM call each).
    max_concurrent: int = 5


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    gzip_minimum_size: int = 1024


# ---------------------------------------------------------------------------
# Root settings
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    config_dir: Path = Path("config")
    corpus_dir: Path = Path("outputs/corpus")
    # Root for local `file:` corpus sources; file paths are confined under it.
    sources_dir: Path = Path("config/sources")
    embeddings_dir: Path = Path("outputs/embeddings")
    projections_dir: Path = Path("outputs/projections")
    graphs_dir: Path = Path("outputs/graphs")
    motifs_dir: Path = Path("outputs/motifs")
    logs_dir: Path = Path("outputs/logs")
    web_root: Path = Path("src/server/web")

    log_level: str = "INFO"

    # sub-settings
    corpus: CorpusSettings = CorpusSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    llm: LLMSettings = LLMSettings()
    graphs: GraphsSettings = GraphsSettings()
    motifs: MotifsSettings = MotifsSettings()
    projections: ProjectionsSettings = ProjectionsSettings()
    server: ServerSettings = ServerSettings()

    model_config = {
        "env_file": [".env", "config/.env"],
        "env_prefix": "MYTHO_",
        "env_nested_delimiter": "__",
        "extra": "ignore",
    }


settings = Settings()
