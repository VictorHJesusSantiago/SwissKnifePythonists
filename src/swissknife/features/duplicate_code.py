from __future__ import annotations

import hashlib
from pathlib import Path


def _normalize(line: str) -> str:
    return " ".join(line.split())


def _block_hash(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def find_duplicates(root: str | Path, min_lines: int = 6) -> dict[str, object]:
    blocks: dict[str, list[dict[str, object]]] = {}
    for path in Path(root).rglob("*.py"):
        if any(part.startswith(".") for part in path.parts):
            continue
        lines = [_normalize(line) for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()]
        significant = [(index, line) for index, line in enumerate(lines) if line]
        for start in range(len(significant) - min_lines + 1):
            window = significant[start : start + min_lines]
            block_lines = [line for _, line in window]
            digest = _block_hash(block_lines)
            blocks.setdefault(digest, []).append({"path": str(path), "start_line": window[0][0] + 1})

    duplicates = [
        {"occurrences": occurrences, "line_count": min_lines}
        for occurrences in blocks.values()
        if len(occurrences) > 1 and len({item["path"] for item in occurrences}) > 1
    ]
    return {"duplicate_blocks": len(duplicates), "duplicates": duplicates}
