# Mythoscope

> Toward a computational framework for comparative mythology.

[![CI](https://github.com/haafus/mythoscope/actions/workflows/ci.yml/badge.svg)](https://github.com/haafus/mythoscope/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docs: CC BY-SA 4.0](https://img.shields.io/badge/Docs-CC%20BY--SA%204.0-lightgrey.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-2.1-purple.svg)](CODE_OF_CONDUCT.md)
[![GitHub stars](https://img.shields.io/github/stars/haafus/mythoscope?style=flat&logo=github)](https://github.com/haafus/mythoscope/stargazers)
<!-- Add on first archived release: a Zenodo DOI badge (citability) and a latest-release badge. See docs/proposals/public-docs-plan.md §15/§17. -->
<!-- Badge owner is haafus/mythoscope; if the repo moves to an org, update the owner in these URLs too (§17 placeholder-fill). -->

**Mythoscope** is a computational framework for comparative mythology. It builds a corpus of
myth and folklore texts, embeds them, and turns the result into an explorable **semantic
space** — with character / place / time **graphs** extracted per text by LLMs, a
**geographic** view, and full-text **search by meaning**. Alongside this unsupervised layer it
assembles a **motif database** that integrates the three traditional folklore indexes —
Thompson (TMI), Aarne–Thompson–Uther (ATU) and Berezkin's areal catalogue — into one
cross-linked, browsable whole, with an automatic **cross-walk** between them and
lexical/semantic **parallel-finding** on top. Everything is served through one web UI.

**[Live demo](https://mythoscope.io)** · **[Documentation](docs/how-to.md)** · **[Roadmap](docs/ROADMAP.md)**

<!-- TODO: add screenshots / a short demo GIF of Atlas, Similarity, and Motifs here. -->

## Features

- **Semantic space** — whole-corpus embeddings projected (UMAP) into an interactive, coloured
  scatter you can explore by tradition and region.
- **Search by meaning** — full-text semantic search and nearest-neighbour "similar fragments"
  across traditions.
- **Knowledge graphs** — per-text character/relation, place, and time graphs (Ages / Realms /
  Beings), extracted by LLMs.
- **Atlas** — a geographic view of the traditions in the corpus.
- **Motif crosswalk** — a browsable catalogue integrating TMI, ATU, and Berezkin with a
  cross-index crosswalk and lexical/semantic parallels.
- **One UI + API** — a single web app plus a REST/OpenAPI service; export bundles let you
  browse prebuilt data with no heavy dependencies.

## Quickstart

```sh
git clone https://github.com/OWNER/mythoscope
cd mythoscope
python -m venv .venv && source .venv/bin/activate
pip install -e ".[viewer]"   # lightweight: browse prebuilt data. Use ".[all]" for the full pipeline.
mytho --help
mytho server                 # serve the web UI + API at http://localhost:8000
```

Install profiles (viewer / search / all), environment setup, and the end-to-end pipeline are
documented in **[docs/how-to.md](docs/how-to.md)**.

## How it works

The pipeline is linear, idempotent, and resumable:

```
corpus → embeddings → { projections, graphs } → server
motifs (independent of the corpus) → server
```

- **corpus** — download & clean source texts (Project Gutenberg + local files), write cleaned
  `.txt` + a catalog.
- **embeddings** — chunk, optionally LLM-preprocess, encode (e.g. `bge-m3`), store in ChromaDB.
- **projections** — reduce vectors with UMAP into the semantic-space views.
- **graphs** — LLM-extract characters/relations, places, and a narrative timeline per text.
- **motifs** — scrape and cross-link the TMI, ATU, and Berezkin indexes into one catalogue.
- **server** — a FastAPI app reads `outputs/` and serves the SPA + REST/OpenAPI API.

## Documentation

- **[How to](docs/how-to.md)** — setup, CLI, and the end-to-end pipeline. Start here.
- **[Research context](docs/research/)** — surveys of the field (computational folkloristics, motif induction).
- **[Motif indexes](docs/motifs/)** — how TMI, ATU and Berezkin are sourced, parsed and cross-linked.
- **[Papers](docs/papers/)** — the working paper drafts and bibliography.
- **[Proposals](docs/proposals/)** — design notes, the public-docs plan, and go-to-market.
- **[Mockups](mockups/)** — standalone feature prototypes over the motif data.
- **Awesome Computational Mythology** — a curated field resource list, maintained as its own standalone repository.

## Project status & roadmap

Early research software (v0.1). Experiments, candidate data sources, potential collaborations,
and submission targets are tracked in **[docs/ROADMAP.md](docs/ROADMAP.md)**.

## Contributing

Contributions of code, corpus, annotations, and docs are welcome — see
**[CONTRIBUTING.md](CONTRIBUTING.md)** and the **[Code of Conduct](CODE_OF_CONDUCT.md)**.
Start with **[docs/how-to.md](docs/how-to.md)** for setup and the pipeline. Security issues:
see **[SECURITY.md](SECURITY.md)**.

## Citation

If you use Mythoscope in academic work, please cite it — see **[CITATION.cff](CITATION.cff)**
(a DOI will be added on the first archived release). GitHub renders a "Cite this repository"
button from that file.

## License

Source code is under the **[MIT license](LICENSE)**. Documentation and prose are under
**CC BY-SA 4.0**, and derived datasets (e.g. the motif crosswalk) under **CC BY 4.0**; see
[`LICENSE`](LICENSE) for details. Third-party source texts and indexes retain their own terms.
