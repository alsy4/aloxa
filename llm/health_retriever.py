"""Retrieves relevant NHS passages for health-related queries.

Uses fastembed (ONNX runtime) to encode the query with the same model the
index was built with, then runs a cosine nearest-neighbour search against
the sqlite-vec index at HEALTH_INDEX_PATH. Results below HEALTH_RETRIEVAL_MIN_SCORE
are discarded so off-topic queries return nothing rather than irrelevant text.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sqlite_vec
from fastembed import TextEmbedding

from config import (
    HEALTH_EMBED_MODEL,
    HEALTH_INDEX_PATH,
    HEALTH_RETRIEVAL_K,
    HEALTH_RETRIEVAL_MIN_SCORE,
)


@dataclass(frozen=True)
class RetrievedChunk:
    title: str
    source: str
    section: str
    text: str
    score: float


class HealthRetriever:
    """Semantic retriever over the pre-built NHS health index."""

    def __init__(
        self,
        index_path: str | Path = HEALTH_INDEX_PATH,
        model_name: str = HEALTH_EMBED_MODEL,
    ) -> None:
        path = Path(index_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Health index not found at {path}. "
                "Run `python3 scripts/build_health_index.py` first."
            )

        self._model = TextEmbedding(model_name=model_name)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.enable_load_extension(True)
        sqlite_vec.load(self._conn)
        self._conn.enable_load_extension(False)

    def _encode(self, query: str) -> bytes:
        vec = next(iter(self._model.embed([query])))
        vec = np.asarray(vec, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tobytes()

    def retrieve(
        self,
        query: str,
        k: int = HEALTH_RETRIEVAL_K,
        min_score: float = HEALTH_RETRIEVAL_MIN_SCORE,
    ) -> list[RetrievedChunk]:
        """Return top-k chunks with cosine similarity >= min_score."""
        if not query.strip():
            return []

        emb = self._encode(query)
        rows = self._conn.execute(
            """
            SELECT chunks.title, chunks.source, chunks.section, chunks.text, distance
            FROM vec_chunks
            JOIN chunks ON chunks.id = vec_chunks.rowid
            WHERE embedding MATCH ? AND k = ?
            ORDER BY distance
            """,
            (emb, k),
        ).fetchall()

        results: list[RetrievedChunk] = []
        for title, source, section, text, distance in rows:
            # sqlite-vec returns squared L2 distance on normalized vectors,
            # which relates to cosine similarity as: cos = 1 - distance / 2.
            score = 1.0 - float(distance) / 2.0
            if score < min_score:
                continue
            results.append(RetrievedChunk(
                title=title,
                source=source,
                section=section,
                text=text,
                score=score,
            ))
        return results

    def close(self) -> None:
        self._conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 -m llm.health_retriever <query>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    retriever = HealthRetriever()
    hits = retriever.retrieve(query)
    if not hits:
        print("(no results above threshold)")
    for h in hits:
        header = f"{h.title} — {h.section}" if h.section else h.title
        print(f"\n[{h.score:.3f}] {header}")
        print(f"  source: {h.source}")
        print(f"  {h.text[:200]}{'...' if len(h.text) > 200 else ''}")
