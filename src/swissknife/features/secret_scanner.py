from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

PATTERNS: dict[str, re.Pattern[str]] = {
    "AWS Access Key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "AWS Secret Key": re.compile(r"(?i)aws(.{0,20})?secret(.{0,20})?['\"][0-9a-zA-Z/+]{40}['\"]"),
    "Chave privada": re.compile(r"-----BEGIN (RSA|EC|OPENSSH|DSA|PGP) PRIVATE KEY-----"),
    "GitHub Token": re.compile(r"gh[pousr]_[0-9A-Za-z]{36}"),
    "Slack Token": re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    "Google API Key": re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    "Segredo genérico": re.compile(r"(?i)(secret|password|passwd|token|apikey|api_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
}

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


@dataclass(slots=True)
class Finding:
    path: str
    line: int
    rule: str
    excerpt: str
    entropy: float


def _shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return round(-sum((count / length) * math.log2(count / length) for count in counts.values()), 3)


def _high_entropy_tokens(line: str, min_length: int = 20, threshold: float = 4.0) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9+/=_\-]{%d,}" % min_length, line)
    return [token for token in tokens if _shannon_entropy(token) >= threshold]


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings
    for line_number, line in enumerate(text.splitlines(), 1):
        for rule, pattern in PATTERNS.items():
            match = pattern.search(line)
            if match:
                findings.append(Finding(str(path), line_number, rule, match.group(0)[:80], _shannon_entropy(match.group(0))))
        for token in _high_entropy_tokens(line):
            findings.append(Finding(str(path), line_number, "Alta entropia", token[:80], _shannon_entropy(token)))
    return findings


def scan(root: str | Path) -> dict[str, object]:
    findings: list[Finding] = []
    for path in Path(root).rglob("*"):
        if not path.is_file() or any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.stat().st_size > 2_000_000:
            continue
        findings.extend(scan_file(path))
    return {"total": len(findings), "findings": [asdict(finding) for finding in findings]}
