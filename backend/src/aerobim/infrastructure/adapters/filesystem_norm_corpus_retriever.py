"""Filesystem keyword norm corpus retriever (RAG-lite; no vector DB required)."""

from __future__ import annotations

import re
from pathlib import Path

from aerobim.domain.norm_assist import NormPassage

_TOKEN = re.compile(r"[A-Za-zА-Яа-я0-9_.\-]{3,}")


class FilesystemNormCorpusRetriever:
    """Scan configured directories for .md/.txt/.json passages matching query tokens.

    Not a neural RAG — deterministic BM25-ish token overlap for provenance citations.
    """

    def __init__(self, corpus_roots: list[Path] | None = None) -> None:
        self._roots = list(corpus_roots or [])

    def retrieve(self, query: str, *, top_k: int = 8) -> list[NormPassage]:
        tokens = {t.casefold() for t in _TOKEN.findall(query)}
        if not tokens:
            return []

        scored: list[NormPassage] = []
        for root in self._roots:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in {".md", ".txt", ".json"}:
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if not text.strip():
                    continue
                file_tokens = {t.casefold() for t in _TOKEN.findall(text)}
                overlap = tokens & file_tokens
                if not overlap:
                    continue
                score = len(overlap) / max(len(tokens), 1)
                excerpt = text.strip().replace("\r\n", "\n")[:800]
                scored.append(
                    NormPassage(
                        passage_id=f"{path.stem}:{score:.3f}",
                        title=path.stem,
                        text=excerpt,
                        source_path=str(path),
                        score=score,
                        clause_hint=next(iter(sorted(overlap)), None),
                    )
                )

        scored.sort(key=lambda p: p.score, reverse=True)
        return scored[: max(1, top_k)]
