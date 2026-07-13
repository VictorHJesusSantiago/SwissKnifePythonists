from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from swissknife.core.utils import atomic_write


def _flatten(data: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            flat.update(_flatten(value, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            flat.update(_flatten(value, f"{prefix}[{index}]"))
    else:
        flat[prefix] = data
    return flat


def snapshot(config: dict[str, Any], path: str | Path) -> dict[str, object]:
    atomic_write(path, json.dumps(config, indent=2, ensure_ascii=False, default=str))
    return {"path": str(path), "keys": len(_flatten(config))}


def compare(baseline_path: str | Path, current: dict[str, Any]) -> dict[str, object]:
    baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    baseline_flat = _flatten(baseline)
    current_flat = _flatten(current)
    added = {key: current_flat[key] for key in current_flat.keys() - baseline_flat.keys()}
    removed = {key: baseline_flat[key] for key in baseline_flat.keys() - current_flat.keys()}
    changed = {
        key: {"before": baseline_flat[key], "after": current_flat[key]}
        for key in baseline_flat.keys() & current_flat.keys()
        if baseline_flat[key] != current_flat[key]
    }
    return {
        "drifted": bool(added or removed or changed),
        "added": added,
        "removed": removed,
        "changed": changed,
    }
