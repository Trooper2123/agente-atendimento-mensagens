"""Recuperação lexical das políticas, com trechos e referências de página."""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

STOPWORDS = {"a", "o", "os", "as", "de", "da", "do", "dos", "das", "e", "em", "na", "no", "um", "uma", "para", "por", "qual", "como", "que", "com", "eu", "me", "sobre", "quero", "tem", "pode"}


def tokens(text: str) -> list[str]:
    normal = unicodedata.normalize("NFKD", text.lower())
    normal = "".join(c for c in normal if not unicodedata.combining(c))
    return [t for t in re.findall(r"[a-z0-9]+", normal) if len(t) > 2 and t not in STOPWORDS]


class PolicyIndex:
    def __init__(self, pdf_path: str | Path):
        try:
            import pymupdf
        except ImportError as exc:
            raise RuntimeError("Instale pymupdf para ler o manual") from exc
        self.chunks: list[tuple[int, str]] = []
        with pymupdf.open(pdf_path) as pdf:
            for number, page in enumerate(pdf, 1):
                text = page.get_text(sort=True)
                blocks = re.split(r"\n\s*\n", text)
                for block in blocks:
                    block = " ".join(block.split())
                    if len(block) > 55 and "Página " not in block[:10]:
                        self.chunks.append((number, block))
        if not self.chunks:
            raise ValueError("Manual sem conteúdo textual recuperável")
        self.docs = [Counter(tokens(text)) for _, text in self.chunks]
        df = Counter(word for doc in self.docs for word in doc)
        self.idf = {term: math.log((1 + len(self.docs)) / (1 + count)) + 1
                    for term, count in df.items()}

    def search(self, query: str, limit: int = 3) -> list[dict]:
        query_terms = set(tokens(query))
        scored = []
        for (page, text), doc in zip(self.chunks, self.docs):
            score = sum((1 + math.log(doc[t])) * self.idf[t]
                        for t in query_terms if t in doc)
            if score:
                scored.append((score, page, text))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"page": page, "text": text, "score": round(score, 2)}
                for score, page, text in scored[:limit]]
