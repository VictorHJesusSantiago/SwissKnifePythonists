from __future__ import annotations

import math
import re
from dataclasses import dataclass


SUSPICIOUS = {
    "urgente": 1.2,
    "senha": 1.0,
    "clique": 0.8,
    "bloqueada": 1.2,
    "pagamento": 0.8,
    "verify": 1.0,
    "immediately": 1.0,
}


@dataclass(slots=True)
class Classification:
    label: str
    probability: float
    indicators: list[str]


def classify(subject: str, body: str) -> Classification:
    text = f"{subject} {body}".lower()
    indicators = [word for word in SUSPICIOUS if word in text]
    score = sum(SUSPICIOUS[word] for word in indicators)
    urls = re.findall(r"https?://[^\s<]+", text)
    if urls:
        score += min(2, len(urls) * 0.5)
        indicators.append(f"{len(urls)} URL(s)")
    if re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", text):
        score += 1.5
        indicators.append("URL com endereço IP")
    probability = 1 / (1 + math.exp(-(score - 2.4)))
    return Classification("phishing" if probability >= 0.5 else "legitimo", round(probability, 4), indicators)
