#!/usr/bin/env python3
"""Static builder for the public documentation.

Renders every ``docs/public/**/*.md`` (frontmatter + Markdown body) into a standalone HTML
page wrapped in one shared shell (header/nav/footer/CSS), mirroring the source tree so the
relative ``.md`` links resolve as ``.html``. The landing page (``url: /``) gets a hero layout;
every other page gets the document layout — Research ▾ dropdown TOC, breadcrumbs, a right-rail
on-page TOC, and the full footer. Per page: ``<title>``, ``<meta name=description>``, OG tags,
and a ``<link rel=canonical>``.

No Jinja2 — the shell is plain string substitution. The one dependency is Python-Markdown
(tables + fenced code + heading anchors), because the pages use GFM tables and code fences.

    python scripts/build_docs.py                # build into docs/public/site/
    python scripts/build_docs.py --watch        # rebuild on change (authoring preview)

The output is fully self-contained (its own ``assets/site.css``) and portable.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import time
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "public"
OUT = SRC / "site"
CSS_SRC = SRC / "html" / "mockups.css"
SITE_ORIGIN = "https://mythoscope.io"

TIER_LABEL = {"A": "The argument", "B": "Reference & surveys", "C": "Participate"}
# Explicit page order within each tier (by url); anything unlisted falls to the end, alphabetically.
ORDER = [
    "/", "/what-we-found", "/cases/swan-maiden", "/cases/sun-and-moon", "/cases/fished-up-earth",
    "/how-it-works", "/about",
    "/crosswalk", "/indexes/tmi", "/indexes/atu", "/indexes/berezkin",
    "/research/computational-folkloristics", "/research/landscape",
    "/research/corpus-sourcing", "/research/encyclopedias", "/regions",
    "/contribute", "/resources", "/publications", "/updates", "/credit",
]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split leading ``--- ... ---`` YAML-ish frontmatter (simple ``key: value`` lines)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    head = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    meta: dict = {}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body


class Page:
    def __init__(self, path: Path):
        self.src = path
        raw = path.read_text(encoding="utf-8")
        self.meta, self.body_md = parse_frontmatter(raw)
        self.url = self.meta.get("url", "/" + path.relative_to(SRC).with_suffix("").as_posix())
        self.tier = self.meta.get("tier", "")
        self.title = self.meta.get("title", path.stem)
        self.description = self.meta.get("description", "")
        # output path mirrors the source tree (index.md -> index.html, foo/bar.md -> foo/bar.html)
        self.out = OUT / path.relative_to(SRC).with_suffix(".html")
        self.depth = len(path.relative_to(SRC).parts) - 1   # for relative root prefix
        self.html = ""
        self.toc: list = []


def render_markdown(page: Page) -> None:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "attr_list", "sane_lists"])
    html = md.convert(page.body_md)
    # relative .md links -> .html (internal only; the mirrored tree keeps them valid)
    html = re.sub(r'href="(?!https?:)([^"]+?)\.md((?:#[^"]*)?)"', r'href="\1.html\2"', html)
    page.html = html
    page.toc = getattr(md, "toc_tokens", [])


def toc_html(tokens: list) -> str:
    """Right-rail on-page TOC from the h2/h3 heading tree."""
    out = []
    for t in tokens:                     # top level = h2
        out.append(f'<a href="#{t["id"]}">{t["name"]}</a>')
        for c in t.get("children", []):  # h3
            out.append(f'<a class="sub" href="#{c["id"]}">{c["name"]}</a>')
    return "\n".join(out)


def research_menu(pages: list[Page], root: str, current_url: str) -> str:
    """The Research ▾ dropdown / the shared doc TOC, grouped by tier."""
    blocks = []
    for tier in ("A", "B", "C"):
        items = [p for p in pages if p.tier == tier]
        if not items:
            continue
        blocks.append(f'<h4>{tier} · {TIER_LABEL[tier]}</h4>')
        for p in items:
            active = " active" if p.url == current_url else ""
            href = root + p.out.relative_to(OUT).as_posix()
            blocks.append(f'<a class="menu-link{active}" href="{href}">{p.title}</a>')
    return "\n".join(blocks)


def header(pages: list[Page], page: Page, root: str) -> str:
    menu = research_menu(pages, root, page.url)
    app = root + "../html/app.html"     # link into the (mockup) live app
    return f"""<header class="site-header">
  <div class="brand"><span class="glyph">M</span> <a href="{root}index.html" style="color:inherit">Mythoscope</a></div>
  <nav class="nav">
    <a href="{app}">Explore</a>
    <div class="has-menu"><span class="navitem">Research</span><div class="menu">{menu}</div></div>
    <a href="{root}about.html">About</a>
    <span class="sep"></span><a class="star" href="https://github.com/haafus/mythoscope">★ GitHub</a>
  </nav>
</header>"""


def footer(root: str) -> str:
    return f"""<footer class="footer-full">
  <div class="cols">
    <div><h5>Read</h5><a href="{root}index.html">Overview</a><a href="{root}what-we-found.html">What we found</a><a href="{root}crosswalk.html">The motif crosswalk</a><a href="{root}research/computational-folkloristics.html">Surveys</a><a href="{root}contribute.html">Contribute</a><a href="{root}publications.html">Publications</a></div>
    <div><h5>Connect</h5><a href="https://github.com/haafus/mythoscope">★ GitHub</a><a href="#">Bluesky</a><a href="#">Mastodon</a><a href="mailto:hello@mythoscope.io">hello@mythoscope.io</a></div>
    <div><h5>Get updates</h5><div class="sub"><input placeholder="you@example.com"><button>Subscribe</button></div>
      <div style="font-size:11.5px;color:var(--muted);margin-top:8px">Occasional notes — motif &amp; mockup of the month.</div></div>
  </div>
  <div class="base"><span>© 2026 Mythoscope · content CC-BY-SA · data CC-BY · code MIT</span>
    <span class="r"><a href="{root}publications.html">Cite</a><a href="#">awesome-list</a></span></div>
</footer>"""


def head(page: Page, root: str) -> str:
    canonical = SITE_ORIGIN + page.url
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page.title} · Mythoscope</title>
<meta name="description" content="{page.description}">
<meta property="og:title" content="{page.title}">
<meta property="og:description" content="{page.description}">
<meta property="og:type" content="article">
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="{root}assets/site.css">
</head>"""


def breadcrumbs(page: Page, root: str) -> str:
    label = TIER_LABEL.get(page.tier, "Docs")
    return (f'<div class="crumbs"><a href="{root}index.html">Research</a>'
            f'<span class="sep">›</span><span>{label}</span>'
            f'<span class="sep">›</span>{page.title}</div>')


def render_doc(pages: list[Page], page: Page) -> str:
    root = "../" * page.depth
    toc = toc_html(page.toc)
    toc_col = f'<nav class="toc"><h4>On this page</h4>{toc}</nav>' if toc else ""
    grid = "doc-grid with-toc" if toc else "doc-grid"
    return f"""{head(page, root)}
<body>
{header(pages, page, root)}
{breadcrumbs(page, root)}
<div class="doc-wrap"><div class="{grid}">
  <article class="article"><div class="prose">
{page.html}
  </div></article>
  {toc_col}
</div></div>
{footer(root)}
</body></html>"""


def render_landing(pages: list[Page], page: Page) -> str:
    root = "../" * page.depth
    # drop the body's leading <h1> — the hero already shows the title
    body = re.sub(r"^\s*<h1[^>]*>.*?</h1>", "", page.html, count=1, flags=re.S)
    return f"""{head(page, root)}
<body>
{header(pages, page, root)}
<section class="hero">
  <h1>{page.title}</h1>
  <p class="hero-sub">{page.description}</p>
  <div class="hero-cta">
    <a class="cta" href="{root}../html/app.html">Explore the live data →</a>
    <a class="cta ghost" href="{root}what-we-found.html">Read what we found</a>
  </div>
</section>
<div class="doc-wrap"><div class="doc-grid"><article class="article"><div class="prose landing-body">
{body}
</div></article></div></div>
{footer(root)}
</body></html>"""


LANDING_CSS = """
/* landing hero (build_docs.py) */
.hero{max-width:var(--content-max);margin:0 auto;padding:56px 22px 26px;text-align:center}
.hero h1{font-family:var(--serif);font-size:44px;line-height:1.12;max-width:900px;margin:0 auto .4em}
.hero-sub{font-size:19px;color:var(--muted);max-width:720px;margin:0 auto 22px;line-height:1.55}
.hero-cta{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.cta.ghost{background:transparent;color:var(--blue);border:1px solid var(--blue-line)}
.cta.ghost:hover{background:var(--blue-soft)}
.landing-body{max-width:760px;margin:0 auto}
.menu-link.active{background:#e2edf0;border-radius:6px}
"""


def build() -> int:
    pages = [Page(p) for p in SRC.rglob("*.md") if p.name != "README.md" and OUT not in p.parents]
    order = {u: i for i, u in enumerate(ORDER)}
    pages.sort(key=lambda p: (order.get(p.url, 999), p.url))

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    (OUT / "assets" / "site.css").write_text(CSS_SRC.read_text(encoding="utf-8") + LANDING_CSS, encoding="utf-8")

    for page in pages:
        render_markdown(page)
        page.out.parent.mkdir(parents=True, exist_ok=True)
        html = render_landing(pages, page) if page.url == "/" else render_doc(pages, page)
        page.out.write_text(html, encoding="utf-8")

    print(f"built {len(pages)} pages -> {OUT.relative_to(ROOT)}")
    return len(pages)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--watch", action="store_true", help="rebuild on change (foreground authoring preview; Ctrl+C to stop)")
    args = ap.parse_args()

    build()
    if not args.watch:
        return 0

    print("watching docs/public for changes … (Ctrl+C to stop)")
    seen = {p: p.stat().st_mtime for p in SRC.rglob("*.md")}
    seen[CSS_SRC] = CSS_SRC.stat().st_mtime
    try:
        while True:
            time.sleep(0.6)
            now = {p: p.stat().st_mtime for p in list(SRC.rglob("*.md")) + [CSS_SRC] if p.exists()}
            if now != seen:
                seen = now
                try:
                    build()
                except Exception as e:  # keep the watcher alive on a transient error
                    print(f"build error: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
