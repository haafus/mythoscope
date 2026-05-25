from dataclasses import dataclass
from pathlib import Path


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
    project_root = ui_root.parent
    web_root = ui_root / "web"

    return ProjectPaths(
        project_root=project_root,
        ui_root=ui_root,
        web_root=web_root,
        assets_dir=web_root / "assets",
        analysis_dir=project_root / "analysis",
        template_dir=project_root / "template",
        corpus_dir=project_root / "corpus",
        corpus_chunked_dir=project_root / "corpus_chunked",
    )


paths = get_paths()

