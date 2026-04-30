    #!/usr/bin/env python3
"""Build the Aloxa health corpus by crawling NHS condition pages.

Fetches curated pages from https://www.nhs.uk/conditions/ and writes each
one as a markdown file under data/health_corpus/.

To add more entries:
    - Append URLs to CONDITIONS for single pages.
    - Append (index_url, subdir) tuples to INDEX_PAGES to crawl an index
      page and all its sub-pages (e.g. vitamins-and-minerals).
Then rerun the script. Already-downloaded pages are skipped unless --force
is passed.

Usage:
    python3 scripts/build_health_corpus.py
    python3 scripts/build_health_corpus.py --force
"""

import argparse
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import BASE_DIR

CORPUS_DIR = Path(BASE_DIR) / "data" / "health_corpus"

USER_AGENT = (
    "AloxaCorpusBuilder/1.0 "
    "(Raspberry Pi medication reminder; educational/research use)"
)
REQUEST_DELAY_SECONDS = 1.0

# --- Edit these lists to extend the corpus ---------------------------------

CONDITIONS: list[str] = [
    "https://www.nhs.uk/conditions/headaches/",
    "https://www.nhs.uk/conditions/migraine/",
    "https://www.nhs.uk/conditions/stomach-ulcer/",
    "https://www.nhs.uk/conditions/gastritis/",
    "https://www.nhs.uk/conditions/food-allergy/",
    "https://www.nhs.uk/conditions/periods/",
    "https://www.nhs.uk/conditions/indigestion/",
    "https://www.nhs.uk/conditions/frozen-shoulder/",
    "https://www.nhs.uk/conditions/high-blood-pressure-hypertension/",
    "https://www.nhs.uk/conditions/cold-sores/",
]

# (index_url, subdir) — the index page itself is saved, then every in-scope
# sub-page linked from it is fetched too.
INDEX_PAGES: list[tuple[str, str]] = [
    (
        "https://www.nhs.uk/conditions/vitamins-and-minerals/",
        "vitamins-and-minerals",
    ),
]

# ---------------------------------------------------------------------------


def slugify(url: str) -> str:
    path = urlparse(url).path.strip("/")
    last = path.split("/")[-1] or "index"
    return re.sub(r"[^a-z0-9-]+", "-", last.lower()).strip("-") or "index"


def fetch(url: str) -> str:
    resp = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def extract_content(html: str) -> tuple[str, str]:
    """Return (title, markdown_body) from an NHS page."""
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else ""

    main = soup.find("main") or soup.find("article") or soup.body
    if main is None:
        return title, ""

    # Strip navigation, asides, forms, breadcrumbs, cookie banners.
    drop_selectors = [
        "nav", "aside", "footer", "form",
        ".nhsuk-breadcrumb", ".nhsuk-pagination",
        ".nhsuk-footer", ".nhsuk-header",
        ".nhsuk-skip-link", ".nhsuk-contents-list",
        "[role=navigation]", "[role=complementary]",
        "script", "style", "noscript",
    ]
    for sel in drop_selectors:
        for el in main.select(sel):
            el.decompose()

    parts: list[str] = []
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if el.name == "h1":
            parts.append(f"# {text}")
        elif el.name == "h2":
            parts.append(f"## {text}")
        elif el.name == "h3":
            parts.append(f"### {text}")
        elif el.name == "h4":
            parts.append(f"#### {text}")
        elif el.name == "li":
            parts.append(f"- {text}")
        else:
            parts.append(text)

    body = "\n\n".join(parts)
    return title, body


def save(url: str, subdir: str, title: str, body: str) -> Path:
    out_dir = CORPUS_DIR / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slugify(url)}.md"
    frontmatter = (
        "---\n"
        f"source: {url}\n"
        f"title: {title}\n"
        f"fetched: {date.today().isoformat()}\n"
        "---\n\n"
    )
    path.write_text(frontmatter + body + "\n", encoding="utf-8")
    return path


def discover_subpages(index_url: str, html: str) -> list[str]:
    """Find in-scope links from an NHS index page."""
    soup = BeautifulSoup(html, "html.parser")
    base_path = urlparse(index_url).path
    if not base_path.endswith("/"):
        base_path += "/"

    main = soup.find("main") or soup.body
    if main is None:
        return []

    seen: set[str] = set()
    subpages: list[str] = []
    for a in main.find_all("a", href=True):
        full = urljoin(index_url, a["href"]).split("#")[0]
        p = urlparse(full)
        if p.netloc != "www.nhs.uk":
            continue
        if not p.path.startswith(base_path):
            continue
        if p.path.rstrip("/") == base_path.rstrip("/"):
            continue
        if full in seen:
            continue
        seen.add(full)
        subpages.append(full)
    return subpages


def process(url: str, subdir: str, force: bool) -> bool:
    out_path = CORPUS_DIR / subdir / f"{slugify(url)}.md"
    if out_path.exists() and not force:
        print(f"  skip (cached): {out_path.relative_to(CORPUS_DIR)}")
        return False
    print(f"  fetching: {url}")
    try:
        html = fetch(url)
    except requests.RequestException as e:
        print(f"    ERROR: {e}")
        return False
    title, body = extract_content(html)
    if not body.strip():
        print("    WARN: empty body — skipping save")
        return False
    path = save(url, subdir, title, body)
    print(f"    saved → {path.relative_to(CORPUS_DIR)} ({len(body)} chars)")
    time.sleep(REQUEST_DELAY_SECONDS)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--force", action="store_true",
        help="Re-fetch pages even if a cached markdown file exists.",
    )
    args = ap.parse_args()

    print(f"Corpus dir: {CORPUS_DIR}")

    print("\n[Conditions]")
    for url in CONDITIONS:
        process(url, "conditions", args.force)

    for index_url, subdir in INDEX_PAGES:
        print(f"\n[Index] {index_url} → {subdir}/")
        try:
            html = fetch(index_url)
        except requests.RequestException as e:
            print(f"  ERROR fetching index: {e}")
            continue
        title, body = extract_content(html)
        if body.strip():
            path = save(index_url, subdir, title, body)
            print(f"  saved index → {path.relative_to(CORPUS_DIR)}")
        time.sleep(REQUEST_DELAY_SECONDS)

        subpages = discover_subpages(index_url, html)
        print(f"  discovered {len(subpages)} sub-page(s)")
        for sub in subpages:
            process(sub, subdir, args.force)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
