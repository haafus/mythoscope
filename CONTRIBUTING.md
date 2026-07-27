# Contributing to Mythoscope

Thanks for your interest! Mythoscope is an open, collaborative research project — contributions
of code, corpus texts, annotations, methods, and documentation are all welcome.

## Ways to contribute

- **Code / bugs** — open an issue or a pull request.
- **Corpus & data** — see the corpus and motif provenance docs; propose sources via an issue.
- **Annotations & expertise** — domain corrections (traditions, motifs, regions) are valuable.
- **Docs** — fixes and clarifications to `docs/`.

For the fuller collaboration model (corpus, metadata, methods, co-authorship), see the project's
contribution & credit policy (in the public docs / `docs/proposals/public-docs-plan.md` §15).

## Development setup

```sh
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all]"     # or a lighter extra — see docs/how-to.md (viewer / search / all)
```

The end-to-end pipeline, CLI, and module map are documented in **[docs/how-to.md](docs/how-to.md)**.

## Before you open a PR

```sh
ruff check src tests scripts      # lint
python -m pytest -q               # Python tests
npm test                          # frontend unit tests
```

- Keep changes focused; match the surrounding code style.
- Add/adjust tests for behavior changes.
- Comments only where they explain something non-obvious.
- Do not commit generated artifacts under `outputs/` or secrets (`.env`).

## Reporting bugs / requesting features

Use the issue templates. Include repro steps, expected vs actual, and environment details.

## Code of conduct

Participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your code contributions are licensed under the repository's
[MIT license](LICENSE), and documentation/data contributions under the corresponding CC licenses
noted in `LICENSE`.
