from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


def _vector(text: str) -> Counter[str]:
    return Counter(re.findall(r"[a-zá-ú0-9]+", text.lower()))


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    dot = sum(value * b[word] for word, value in a.items())
    norm = math.sqrt(sum(x * x for x in a.values()) * sum(x * x for x in b.values()))
    return dot / norm if norm else 0.0


@dataclass(slots=True)
class Document:
    path: str
    title: str
    content: str


class WikiIndex:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.documents = [
            Document(str(path), path.stem, path.read_text(encoding="utf-8", errors="ignore"))
            for path in self.root.rglob("*.md")
        ]

    def search(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        query_vector = _vector(query)
        ranked = sorted(
            ((_cosine(query_vector, _vector(doc.title + " " + doc.content)), doc) for doc in self.documents),
            reverse=True,
            key=lambda item: item[0],
        )
        return [{"score": round(score, 4), "path": doc.path, "title": doc.title} for score, doc in ranked[:limit] if score > 0]
