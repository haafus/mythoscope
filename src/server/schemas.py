from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from corpus.utils import UNASSIGNED


class ModelSummary(BaseModel):
    name: str
    key: str


class ModelListResponse(BaseModel):
    models: list[ModelSummary]
    # False in viewer builds; the frontend hides the search box.
    text_search: bool = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    model: str
    top_k: int = Field(default=20, ge=1, le=100)


class WarmupRequest(BaseModel):
    model: str


class SearchResult(BaseModel):
    # B1: a hit carries chunk data + the document reference only; tradition/region/url/
    # colour are resolved on the front from the globally-cached document + tree (§3).
    document_id: str = ""
    chunk_index: int = 0
    similarity_score: float
    text: str = ""
    # Original chunk for preprocessing variants (the embedded `text` is the
    # transformed version); empty for raw variants, where `text` is the source.
    source_text: str = ""


class CorpusDocument(BaseModel):
    document_id: str = ""
    title: str
    tradition: str = UNASSIGNED
    url: str = ""
    word_count: int = 0
    sentence_count: int = 0
    char_count: int = 0
    description: str = ""
    dating: str = ""
    source: str = ""


class DocumentsResponse(BaseModel):
    documents: list[CorpusDocument]
    total: int


class TraditionsResponse(BaseModel):
    traditions: dict[str, Any]
    total: int


# --- Motifs ---

class MotifChapter(BaseModel):
    model_config = ConfigDict(extra="allow")  # per-tier counts (substantive/definitions/atu)
    id: str
    label: str
    count: int


class MotifIndexSummary(BaseModel):
    model_config = ConfigDict(extra="allow")  # tier totals for the motif filter
    index: str
    label: str
    long_label: str = ""
    attribution: str = ""
    homepage: str = ""
    count: int
    chapters: list[MotifChapter] = []


class MotifIndexesResponse(BaseModel):
    indexes: list[MotifIndexSummary]


class MotifListItem(BaseModel):
    model_config = ConfigDict(extra="allow")  # tmi enrichments: substantive/notes_size/*_subtree/…
    index: str
    id: str
    name: str = ""
    chapter: str = ""
    badge: str = ""
    level: int = 0
    descendant_count: int = 0
    leaf: bool = False
    duplicate: bool = False


class MotifListResponse(BaseModel):
    index: str
    total: int
    items: list[MotifListItem]


class MotifDetail(BaseModel):
    # Common fields are fixed; index-specific ones (definition/areas/notes/summary/…)
    # vary by index, so allow extras rather than drop them.
    model_config = ConfigDict(extra="allow")
    index: str
    id: str
    name: str = ""
    chapter: str = ""
    chapter_label: str = ""
    links: dict[str, Any] = {}


# --- Similarity / projections ---

class ProjectionMethod(BaseModel):
    key: str
    label: str
    chart_type: str


class WarmupResponse(BaseModel):
    status: str
    model: str


class ProjectionData(BaseModel):
    # Payload shape depends on chart_type (points / matrix / distribution),
    # so only the discriminator is fixed; the rest passes through.
    model_config = ConfigDict(extra="allow")
    method: str


# --- Graphs ---

class GraphResponse(BaseModel):
    # Node/edge `data` carries graph-specific attributes; keep them via extras.
    model_config = ConfigDict(extra="allow")
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
