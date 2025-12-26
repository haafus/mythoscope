"""
Knowledge Extraction from Mythological Corpus
==============================================

Pipeline:
- Load chunked corpus
- Named Entity Recognition (spaCy)
- Ontology-based concept mapping (wikontic)
- Pattern-based relation extraction
- Knowledge graph construction
- Export to JSON / RDF

Requirements:
pip install wikontic spacy sentence-transformers
python -m spacy download en_core_web_sm
"""

import json
import os
from collections import defaultdict

import spacy
from wikontic import Ontology, ConceptGraph

# ===================== CONFIG =====================
CHUNK_META_PATH = "embeddings/chunk_metadata.json"
OUT_DIR = "knowledge_graph"

ONTOLOGY_NAME = "wordnet"   # или путь к кастомной онтологии
LANG_MODEL = "en_core_web_sm"

MIN_ENTITY_LEN = 3
# =================================================

os.makedirs(OUT_DIR, exist_ok=True)

# ===================== LOAD =======================
print("🔹 Loading corpus chunks...")
with open(CHUNK_META_PATH, encoding="utf-8") as f:
    chunks = json.load(f)

texts = [c["text"] for c in chunks]

print(f"Loaded {len(texts)} chunks")

# ===================== NLP ========================
print("🔹 Loading spaCy...")
nlp = spacy.load(LANG_MODEL)

# ===================== WIKONTIC ===================
print("🔹 Loading ontology...")
ontology = Ontology.load(ONTOLOGY_NAME)
graph = ConceptGraph(ontology)

# ===================== UTILITIES ==================
def extract_entities(text):
    """
    Extract named entities and noun phrases
    """
    doc = nlp(text)
    ents = set()

    for ent in doc.ents:
        if len(ent.text) >= MIN_ENTITY_LEN:
            ents.add(ent.text)

    for chunk in doc.noun_chunks:
        if len(chunk.text) >= MIN_ENTITY_LEN:
            ents.add(chunk.text)

    return list(ents)


def map_to_concept(term):
    """
    Map textual term to ontological concept
    """
    results = ontology.search(term)
    if results:
        return results[0]
    return None


# ===================== RELATIONS ==================
MYTH_RELATIONS = {
    "create": "creates",
    "form": "creates",
    "make": "creates",
    "bring": "creates",
    "descend": "descends_to",
    "enter": "descends_to",
    "rule": "rules",
    "govern": "rules",
    "sacrifice": "sacrifices",
    "offer": "sacrifices",
    "establish": "establishes_law",
    "law": "establishes_law",
    "order": "establishes_order"
}


def extract_relations(text):
    """
    Extract subject–verb–object mythological relations
    """
    doc = nlp(text)
    triples = []

    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in MYTH_RELATIONS:
            subj = [w for w in token.lefts if w.dep_ == "nsubj"]
            obj = [w for w in token.rights if w.dep_ in ("dobj", "pobj")]

            if subj and obj:
                triples.append({
                    "subject": subj[0].text,
                    "relation": MYTH_RELATIONS[lemma],
                    "object": obj[0].text
                })

    return triples


# ===================== EXTRACTION =================
print("🔹 Extracting knowledge...")

stats = defaultdict(int)

for chunk in chunks:
    text = chunk["text"]
    source = chunk["text_id"]

    # --- entities ---
    entities = extract_entities(text)
    concepts = []

    for ent in entities:
        concept = map_to_concept(ent)
        if concept:
            concepts.append(concept)
            stats["concepts"] += 1

    # --- co-occurrence relations ---
    for i in range(len(concepts)):
        for j in range(i + 1, len(concepts)):
            graph.add_edge(
                concepts[i],
                "co_occurs_with",
                concepts[j],
                source=source
            )
            stats["co_occurrences"] += 1

    # --- mythological relations ---
    relations = extract_relations(text)

    for r in relations:
        subj = map_to_concept(r["subject"])
        obj = map_to_concept(r["object"])

        if subj and obj:
            graph.add_edge(
                subj,
                r["relation"],
                obj,
                source=source
            )
            stats["relations"] += 1

# ===================== EXPORT =====================
print("🔹 Exporting knowledge graph...")

json_path = os.path.join(OUT_DIR, "knowledge_graph.json")
graph.export_json(json_path)

# RDF, если поддерживается
try:
    rdf_path = os.path.join(OUT_DIR, "knowledge_graph.rdf")
    graph.export_rdf(rdf_path)
    print("RDF export completed")
except Exception:
    print("RDF export not supported")

# ===================== DONE =======================
print("✅ Knowledge extraction completed")
print("Stats:")
for k, v in stats.items():
    print(f"  {k}: {v}")

print(f"Saved to: {OUT_DIR}")
