from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zá-ú0-9]+", text.lower()))


@dataclass(slots=True)
class Answer:
    text: str
    confidence: float
    category: str


class FAQ:
    def __init__(self, entries: list[dict[str, str]]):
        self.entries = entries

    @classmethod
    def load(cls, path: str | Path) -> "FAQ":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def answer(self, question: str) -> Answer:
        query = tokens(question)
        ranked = []
        for item in self.entries:
            candidate = tokens(item["question"] + " " + item.get("keywords", ""))
            score = len(query & candidate) / max(1, len(query | candidate))
            ranked.append((score, item))
        score, item = max(ranked, default=(0, {"answer": "Encaminhado para atendimento humano", "category": "triagem"}), key=lambda x: x[0])
        if score < 0.08:
            return Answer("Não encontrei uma resposta segura. Encaminhei para a equipe responsável.", score, "triagem")
        return Answer(item["answer"], round(score, 3), item.get("category", "geral"))
