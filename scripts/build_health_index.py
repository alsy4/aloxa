#!/usr/bin/env python3
"""Build the Aloxa health RAG vector index.

Reads every markdown file under data/health_corpus/, splits each document
into section-aware chunks, embeds them with a sentence-transformer model,
and writes the result to a sqlite-vec database at data/health_index.db.

Usage:
    python3 scripts/build_health_index.py
    python3 scripts/build_health_index.py --model all-mpnet-base-v2
"""

import argparse
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
import sqlite_vec
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    HEALTH_CHUNK_MAX_CHARS,
    HEALTH_CORPUS_DIR,
    HEALTH_EMBED_DIM,
    HEALTH_EMBED_MODEL,
    HEALTH_INDEX_PATH,
)

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (metadata, body) from a markdown string with YAML frontmatter."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def chunk_document(
    title: str,
    body: str,
    max_chars: int,
) -> list[tuple[str, str]]:
    """Split body into (section, text) chunks, section-aware.

    Each chunk is emitted when adding the next paragraph would push it past
    max_chars. A new section header also forces a flush so chunks don't
    straddle H2 boundaries.
    """
    section = ""
    buf: list[str] = []
    buf_len = 0
    chunks: list[tuple[str, str]] = []

    def flush():
        nonlocal buf, buf_len
        if buf:
            chunks.append((section, "\n\n".join(buf).strip()))
            buf = []
            buf_len = 0

    for para in re.split(r"\n\s*\n", body):
        para = para.strip()
        if not para:
            continue

        # Section header — flush current buffer and update section label.
        if para.startswith("## "):
            flush()
            section = para.lstrip("# ").strip()
            continue
        # H1 we already have as title; H3/H4 stay inside the section.
        if para.startswith("# "):
            continue

        # Would this paragraph overflow the buffer?
        if buf_len + len(para) > max_chars and buf:
            flush()

        buf.append(para)
        buf_len += len(para) + 2

        # Single paragraph larger than max — emit it alone.
        if buf_len >= max_chars:
            flush()

    flush()
    return chunks


def embedding_text(title: str, section: str, text: str) -> str:
    """Self-contained text used for embedding and retrieval display."""
    header = title if not section else f"{title} — {section}"
    return f"[{header}]\n\n{text}"


def iter_corpus(corpus_dir: Path):
    for path in sorted(corpus_dir.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        title = meta.get("title") or path.stem
        source = meta.get("source", "")
        yield path, title, source, body


def build(index_path: Path, corpus_dir: Path, model_name: str,
          max_chars: int, expected_dim: int) -> None:
    if not corpus_dir.exists():
        raise SystemExit(f"Corpus dir not found: {corpus_dir}")

    print(f"Loading model: {model_name}")
    t0 = time.time()
    model = SentenceTransformer(model_name)
    dim = model.get_sentence_embedding_dimension()
    if dim != expected_dim:
        raise SystemExit(
            f"Embedding dim mismatch: model={dim}, config={expected_dim}. "
            f"Update HEALTH_EMBED_DIM in config.py."
        )
    print(f"  loaded in {time.time() - t0:.1f}s (dim={dim})")

    # Gather and chunk everything first so we can batch-encode.
    records: list[tuple[str, str, str, str]] = []  # (title, source, section, text)
    for path, title, source, body in iter_corpus(corpus_dir):
        doc_chunks = chunk_document(title, body, max_chars)
        rel = path.relative_to(corpus_dir)
        print(f"  {rel}: {len(doc_chunks)} chunk(s)")
        for section, text in doc_chunks:
            records.append((title, source, section, text))

    if not records:
        raise SystemExit("No chunks produced — is the corpus empty?")

    print(f"\nEncoding {len(records)} chunks...")
    t0 = time.time()
    texts = [embedding_text(t, s, x) for t, _, s, x in records]
    embeddings = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    print(f"  encoded in {time.time() - t0:.1f}s")

    if index_path.exists():
        index_path.unlink()
    index_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(index_path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    conn.executescript(f"""
        CREATE TABLE meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            section TEXT NOT NULL,
            text TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE vec_chunks USING vec0(
            embedding float[{dim}]
        );
    """)

    conn.executemany(
        "INSERT INTO meta(key, value) VALUES (?, ?)",
        [
            ("embed_model", model_name),
            ("embed_dim", str(dim)),
            ("chunk_max_chars", str(max_chars)),
            ("chunk_count", str(len(records))),
        ],
    )

    for (title, source, section, text), emb in zip(records, embeddings):
        cur = conn.execute(
            "INSERT INTO chunks(title, source, section, text) VALUES (?, ?, ?, ?)",
            (title, source, section, text),
        )
        conn.execute(
            "INSERT INTO vec_chunks(rowid, embedding) VALUES (?, ?)",
            (cur.lastrowid, np.asarray(emb, dtype=np.float32).tobytes()),
        )

    conn.commit()
    conn.close()

    size_kb = index_path.stat().st_size / 1024
    print(f"\nWrote {index_path} ({size_kb:.1f} KB, {len(records)} chunks)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--model", default=HEALTH_EMBED_MODEL,
        help="Sentence-transformers model name (default from config).",
    )
    ap.add_argument(
        "--corpus", default=HEALTH_CORPUS_DIR, type=Path,
        help="Corpus directory to index.",
    )
    ap.add_argument(
        "--out", default=HEALTH_INDEX_PATH, type=Path,
        help="Output sqlite index path.",
    )
    ap.add_argument(
        "--max-chars", type=int, default=HEALTH_CHUNK_MAX_CHARS,
        help="Max chars per chunk.",
    )
    args = ap.parse_args()

    build(
        index_path=Path(args.out),
        corpus_dir=Path(args.corpus),
        model_name=args.model,
        max_chars=args.max_chars,
        expected_dim=HEALTH_EMBED_DIM,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
