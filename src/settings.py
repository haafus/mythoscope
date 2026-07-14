from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# Load .env into os.environ so non-MYTHO_ keys (OPENAI_API_KEY, HF_TOKEN, …)
# reach the SDKs; real environment variables take precedence (override=False).
for _env_file in (".env", "config/.env"):
    load_dotenv(_env_file)

# Sub-models are plain BaseModel; only the root reads the environment.


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
    # LLM for chunk preprocessing (summary variants); alias from config/models.json.
    llm: str = "gpt4o-mini"
    temperature: float = 0.1


class GraphsSettings(BaseModel):
    llm: str = "gpt4o-mini"  # alias from config/models.json
    temperature: float = 0.1
    use_json_mode: bool = True
    chunk_size: int = 50000
    chunk_overlap: int = 1000
    # Only bounds in-flight chunks; the rate limiter is the real throttle. 18 keeps
    # a typical gpt-4o-mini run near its TPM ceiling.
    max_concurrent: int = 18
    max_entities: int | None = 50  # most-mentioned kept per graph; None = keep all


class MotifsSettings(BaseModel):
    max_workers: int = 10  # concurrent Berezkin detail-page fetches
    # Detail pages add per-motif definitions; the backbone (codes, names, areas)
    # comes from the index page regardless.
    berezkin_details: bool = True
    max_motifs: int | None = None  # cap detailed motifs (None = all); used by `build --sample`


class ProjectionsSettings(BaseModel):
    umap_n_neighbors: int = 15
    umap_min_dist: float = 0.1
    max_concurrent: int = 5  # LLM calls in flight during chunk preprocessing


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    gzip_minimum_size: int = 1024


class Settings(BaseSettings):
    config_dir: Path = Path("config")
    corpus_dir: Path = Path("outputs/corpus")
    # Root for local `file:` corpus sources; file paths are confined under it.
    sources_dir: Path = Path("sources")
    embeddings_dir: Path = Path("outputs/embeddings")
    preprocessed_dir: Path = Path("outputs/preprocessed")
    projections_dir: Path = Path("outputs/projections")
    graphs_dir: Path = Path("outputs/graphs")
    motifs_dir: Path = Path("outputs/motifs")
    logs_dir: Path = Path("outputs/logs")
    web_root: Path = Path("src/server/web")

    log_level: str = "INFO"
    logs_max_files: int = 20  # per-run log files kept in logs_dir (<=0 = keep all)

    corpus: CorpusSettings = CorpusSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
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
