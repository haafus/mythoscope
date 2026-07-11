# ST config overrides — `uhhlt/story-emb`

`uhhlt/story-emb` ships **no sentence-transformers config** (just a bare Mistral-7B
`transformers` model + a LoRA adapter dir), so `SentenceTransformer(...)` would fall back to
**mean pooling** and produce wrong embeddings. This model is `e5-mistral-7b-instruct`-based and
needs **last-token pooling + normalize**.

These files are the sentence-transformers scaffolding, taken from the base model
[`intfloat/e5-mistral-7b-instruct`](https://huggingface.co/intfloat/e5-mistral-7b-instruct)
(architecture-identical, hidden size 4096):

- `modules.json` — Transformer → Pooling → Normalize
- `1_Pooling/config.json` — `pooling_mode_lasttoken: true`
- `2_Normalize/config.json` — L2 normalize

**Prompts are deliberately not included here** — they live in `config/models.json`
(`query_prompt` / `document_prompt`) as the single source of truth.

At load time (`src/embeddings/model_manager.py`), when a model has no native `modules.json`,
these files are injected into its downloaded snapshot before `SentenceTransformer` opens it.
