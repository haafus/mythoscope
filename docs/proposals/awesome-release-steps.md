# Awesome release steps — creating & shipping `awesome-computational-mythology`

The end-to-end steps to stand up, lint, cite, and promote the standalone
`awesome-computational-mythology` repository. The list content lives in
[`../awesome-computational-mythology.md`](../awesome-computational-mythology.md); the repo
scaffold (README, `contributing.md`, `code-of-conduct.md`, `LICENSE`, `CITATION.cff`,
`.github/` templates + CI) was staged under `staging/` in this repo and has since been moved
out into its own standalone repository. This doc is the release runbook.

## Scaffold contents (for reference)

```
README.md                                  ← the list (becomes the repo's front page)
contributing.md
code-of-conduct.md
LICENSE                                    ← CC0 1.0 (content license)
CITATION.cff                               ← fill in OWNER + your name (+ ORCID)
.gitignore
.github/
├── workflows/awesome-lint.yml             ← CI: awesome-lint + lychee link check
├── pull_request_template.md
└── ISSUE_TEMPLATE/suggest-a-resource.md
```

## Step 1 — Create the empty repo (personal account)

On github.com: **New repository** →
- Owner: **your personal account** (not an org — a personal-account awesome list reads as
  neutral community curation and is the convention; you can transfer it to an org later without
  losing stars or links).
- Name: exactly **`awesome-computational-mythology`**.
- Public. **Do not** initialize with a README/license/gitignore (the scaffold provides them).
- Create.

## Step 2 — Push the scaffold

From your machine, in the folder holding the scaffold files:

```sh
git init -b main            # git ≥ 2.28
git add .
git commit -m "init: awesome-computational-mythology"
git remote add origin git@github.com:<your-username>/awesome-computational-mythology.git
git push -u origin main
```

**Older git (< 2.28, e.g. 2.15):** `git init -b main` and `git switch -c` do not exist. Use:

```sh
git init
git checkout -b main        # renames the unborn branch master → main (works pre-2.28)
git add .
git commit -m "init: awesome-computational-mythology"
git remote add origin git@github.com:<your-username>/awesome-computational-mythology.git
git push -u origin main
```

(`git branch -M main` fails right after `git init` — there is no `master` ref until the first
commit; `git checkout -b main` re-points the unborn HEAD instead.)

## Step 3 — Fill in placeholders

- **`CITATION.cff`** — replace `OWNER`, `FIRST`/`LAST`, and optionally add your ORCID.
- **`README.md`** — the maintainer/backlink line under **Projects** is already tasteful; leave
  it neutral.

## Step 4 — Configure the repo (Settings → …)

- **Description:** "A curated list of resources for the computational, comparative, and
  quantitative study of myth, folklore, and traditional narrative."
- **Topics:** `awesome`, `awesome-list`, `computational-folkloristics`, `digital-humanities`,
  `folklore`, `mythology`, `nlp`, `comparative-mythology`.
- **Social preview:** upload a simple 1280×640 image (Settings → General → Social preview).
- Enable **Issues** and **Discussions**.

## Step 5 — Make it lint-clean (before promoting)

The list is a strong draft but **not yet `awesome-lint`-perfect** — awesome-lint wants every
entry to be a Markdown link (`- [Name](url) - Description.`) and forbids dead links. Before you
submit to the index:

```sh
npx awesome-lint            # fix what it flags
```

1. **Verify every link** (CI's lychee job will also flag dead ones).
2. **Add links** to entries that lack them, or move purely conceptual entries (some
   Methods/Scholars items) into linked resources — or trim them; awesome-lint expects linked
   list items.
3. Re-run `npx awesome-lint` until green.

## Step 6 — Citability (optional but recommended)

- Keep `CITATION.cff` (GitHub shows a "Cite this repository" button).
- Connect the repo to **Zenodo** (zenodo.org → GitHub → flip the repo on), then cut a GitHub
  **Release** — Zenodo mints a DOI. Add the DOI badge to the README.

## Step 7 — Submit to the awesome index

Once the repo is **≥ 30 days old**, has real history, and `npx awesome-lint` is green, open a
PR to **[`sindresorhus/awesome`](https://github.com/sindresorhus/awesome)** following their
contribution guidelines.

## Step 8 — Promote (see [`go-to-market.md`](go-to-market.md) §8a)

Seed stars via Bluesky / Humanist list / r/DigitalHumanities; add reciprocal links with
related awesome lists; add it to relevant Wikipedia "External links"; announce on
r/coolgithubprojects / libhunt.
