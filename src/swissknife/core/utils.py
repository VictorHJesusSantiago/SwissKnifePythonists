from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable


def checksum(path: str | Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: str | Path, content: str | bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        with tempfile.NamedTemporaryFile(mode="wb", dir=target.parent, delete=False) as tmp:
            tmp.write(content)
            temporary = Path(tmp.name)
    else:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent, delete=False
        ) as tmp:
            tmp.write(content)
            temporary = Path(tmp.name)
    os.replace(temporary, target)


def run(command: list[str], *, execute: bool, timeout: int = 300) -> dict[str, Any]:
    if not execute:
        return {"executed": False, "command": command, "returncode": None}
    process = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    return {
        "executed": True,
        "command": command,
        "returncode": process.returncode,
        "stdout": process.stdout[-10000:],
        "stderr": process.stderr[-10000:],
    }


def json_lines(items: Iterable[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(item, ensure_ascii=False, default=str) for item in items)
