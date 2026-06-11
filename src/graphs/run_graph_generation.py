import copy
import json
import logging
from datetime import datetime
from pathlib import Path

from .config import load_config
from .graph_generator import generate_and_save_graph
from .llm_processing import LLMProcessor
from .prompts_loader import load_prompts

logger = logging.getLogger(__name__)


def _setup_graph_logging(logs_dir: Path) -> None:
    from settings import setup_logging

    logs_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(
        log_filename=f"generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        log_dir=str(logs_dir),
    )


def chunk_text(text: str, max_chars: int, overlap: int) -> list:
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + max_chars, text_len)
        if end < text_len:
            split_pos = max(text.rfind("\n", start, end), text.rfind(".", start, end), text.rfind(" ", start, end))
            if split_pos == -1 or split_pos <= start:
                split_pos = end
            else:
                split_pos += 1
        else:
            split_pos = end

        chunks.append(text[start:split_pos])
        next_start = split_pos - overlap
        start = split_pos if next_start <= start else next_start

    return chunks


def deduplicate_entities(entities: list) -> list:
    unique_entities = {}
    for ent in entities:
        name = ent.get("Name") or ent.get("name") or ent.get("NAME")
        if not name:
            continue

        norm_name = str(name).strip().lower()

        if norm_name not in unique_entities:
            unique_entities[norm_name] = copy.deepcopy(ent)
        else:
            existing = unique_entities[norm_name]
            for key, value in ent.items():
                if key.lower() in ["name"]:
                    continue

                if value in [None, "", [], "nan", "NaN"] or str(value).lower() == "nan":
                    continue

                existing_val = existing.get(key)

                if existing_val in [None, "", [], "nan", "NaN"] or str(existing_val).lower() == "nan":
                    existing[key] = copy.deepcopy(value)
                elif isinstance(existing_val, list) and isinstance(value, list):
                    merged = existing_val.copy()
                    for item in value:
                        if item not in merged:
                            merged.append(item)
                    existing[key] = merged
                elif isinstance(existing_val, str) and isinstance(value, str):
                    if value not in existing_val:
                        existing[key] = f"{existing_val}; {value}"
                elif isinstance(existing_val, list) and isinstance(value, str):
                    if value not in existing_val:
                        existing[key].append(value)
                elif isinstance(existing_val, str) and isinstance(value, list):
                    new_list = [existing_val]
                    for item in value:
                        if item not in new_list:
                            new_list.append(item)
                    existing[key] = new_list

    return list(unique_entities.values())


def deduplicate_relations(relations: list) -> list:
    unique_relations = set()
    deduplicated = []
    for rel in relations:
        subj = str(rel.get("Subject", rel.get("subject", ""))).strip().lower()
        obj = str(rel.get("Object", rel.get("object", ""))).strip().lower()
        r_type = str(rel.get("Relation", rel.get("relation", ""))).strip().lower()

        if not subj or not obj:
            continue

        identifier = (subj, obj, r_type)
        if identifier not in unique_relations:
            unique_relations.add(identifier)
            deduplicated.append(rel)

    return deduplicated


def run_generate_graphs(force: bool = False):
    cfg = load_config()

    _setup_graph_logging(cfg.logs_dir)

    llm_cfg = cfg.active_llm_config

    logger.info(f"Starting graph generation process (force={force})...")

    try:
        prompts = load_prompts(cfg.prompts_path)
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}")
        return

    llm = LLMProcessor(
        api_key=llm_cfg["api_key"],
        model_name=llm_cfg["model_name"],
        base_url=llm_cfg["base_url"],
        use_json_mode=llm_cfg["use_json_mode"],
        temperature=cfg.temperature,
        max_retries=cfg.max_retries,
        retry_backoff_factor=cfg.retry_backoff_factor,
    )

    if not cfg.metadata_path.exists():
        logger.error(f"Metadata file not found: {cfg.metadata_path}")
        return

    try:
        with open(cfg.metadata_path, encoding="utf-8") as f:
            corpus = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read metadata: {e}")
        return

    for book in corpus:
        book_id = book.get("id", "unknown_book")
        txt_path = Path(book.get("path", ""))

        book_out_dir = cfg.output_base_dir / book_id
        book_out_dir.mkdir(parents=True, exist_ok=True)

        expected_html_path = book_out_dir / "characters.html"

        if expected_html_path.exists():
            if not force:
                logger.info(f"--- Skipping: {book_id} (already exists) ---")
                continue
            else:
                logger.info(f"--- Overwriting: {book_id} (file exists, but force=True is enabled) ---")

        if not txt_path.exists():
            logger.warning(f"Text file not found: {txt_path}")
            continue

        try:
            with open(txt_path, encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Error reading file {txt_path}: {e}")
            continue

        logger.info(f"--- Processing: {book_id} ---")

        chunks = chunk_text(text, max_chars=cfg.chunk_size, overlap=cfg.chunk_overlap)
        logger.info(f"Text split into {len(chunks)} chunks.")

        all_characters, all_relations = [], []
        all_locations, all_times = [], []

        chars_prompt = prompts.get("characters", "Extract characters...")
        rels_prompt = prompts.get("relations", "Extract relations...")
        locs_prompt = prompts.get("locations", "Extract locations...")
        time_prompt = prompts.get("time", "Extract time...")

        for i, chunk in enumerate(chunks):
            logger.info(f"  [Chunk {i + 1}/{len(chunks)}] Extracting characters and relations...")

            chars = llm.extract_characters(chunk, chars_prompt)
            current_chunk_chars = chars if isinstance(chars, list) else []
            all_characters.extend(current_chunk_chars)

            rels = llm.extract_relations(chunk, current_chunk_chars, rels_prompt)
            if isinstance(rels, list):
                all_relations.extend(rels)

            locs = llm.extract_locations(chunk, locs_prompt)
            if isinstance(locs, list):
                all_locations.extend(locs)

            times = llm.extract_time(chunk, time_prompt)
            if isinstance(times, list):
                all_times.extend(times)

        all_characters = deduplicate_entities(all_characters)
        all_relations = deduplicate_relations(all_relations)
        all_locations = deduplicate_entities(all_locations)
        all_times = deduplicate_entities(all_times)
        logger.info(
            f"Extracted unique items: Characters ({len(all_characters)}), Relations ({len(all_relations)}), Locations ({len(all_locations)}), Times ({len(all_times)})"
        )

        try:
            with open(book_out_dir / "personas.json", "w", encoding="utf-8") as f:
                json.dump(all_characters, f, ensure_ascii=False, indent=2)

            with open(book_out_dir / "relations.json", "w", encoding="utf-8") as f:
                json.dump(all_relations, f, ensure_ascii=False, indent=2)

            with open(book_out_dir / "locations.json", "w", encoding="utf-8") as f:
                json.dump(all_locations, f, ensure_ascii=False, indent=2)

            with open(book_out_dir / "times.json", "w", encoding="utf-8") as f:
                json.dump(all_times, f, ensure_ascii=False, indent=2)

            generate_and_save_graph(all_characters, all_relations, book_out_dir)

        except Exception as e:
            logger.error(f"Error saving files or generating graph for {book_id}: {e}")
