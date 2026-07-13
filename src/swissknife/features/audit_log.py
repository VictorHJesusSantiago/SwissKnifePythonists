from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _sign(secret: str, payload: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def record(log_path: str | Path, secret: str, actor: str, command: str, arguments: dict[str, Any] | None = None) -> dict[str, object]:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = "0" * 64
    if path.exists():
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            previous_hash = json.loads(lines[-1])["entry_hash"]
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "actor": actor,
        "command": command,
        "arguments": arguments or {},
        "previous_hash": previous_hash,
    }
    payload = json.dumps(entry, sort_keys=True, default=str)
    entry["entry_hash"] = _sign(secret, payload)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    return entry


def verify(log_path: str | Path, secret: str) -> dict[str, object]:
    path = Path(log_path)
    if not path.exists():
        return {"valid": True, "entries": 0, "broken_at": None}
    previous_hash = "0" * 64
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    for index, line in enumerate(lines, 1):
        entry = json.loads(line)
        stored_hash = entry.pop("entry_hash")
        if entry["previous_hash"] != previous_hash:
            return {"valid": False, "entries": index, "broken_at": index}
        payload = json.dumps(entry, sort_keys=True, default=str)
        expected_hash = _sign(secret, payload)
        if not hmac.compare_digest(expected_hash, stored_hash):
            return {"valid": False, "entries": index, "broken_at": index}
        previous_hash = stored_hash
    return {"valid": True, "entries": len(lines), "broken_at": None}
