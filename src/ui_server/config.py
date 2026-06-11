from dataclasses import dataclass
from pathlib import Path

from settings import settings


@dataclass(frozen=True)
class ProjectPaths:
    project_root: Path
    ui_root: Path
    web_root: Path
    assets_dir: Path
    analysis_dir: Path
    template_dir: Path
    corpus_dir: Path
    corpus_chunked_dir: Path


def get_paths() -> ProjectPaths:
    ui_root = Path(__file__).resolve().parent
    web_root = ui_root / "web"

    return ProjectPaths(
        project_root=settings.project_root,
        ui_root=ui_root,
        web_root=web_root,
        assets_dir=web_root / "assets",
        analysis_dir=settings.analysis_dir,
        template_dir=settings.project_root / "config" / "template",
        corpus_dir=settings.corpus_dir,
        corpus_chunked_dir=settings.corpus_chunked_dir,
    )


paths = get_paths()
