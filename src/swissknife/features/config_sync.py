from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from swissknife.core.config import load_mapping
from swissknife.core.utils import atomic_write


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    output = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(output.get(key), dict):
            output[key] = deep_merge(output[key], value)
        else:
            output[key] = deepcopy(value)
    return output


def synchronize(base: str | Path, overlay: str | Path, output: str | Path) -> dict[str, Any]:
    merged = deep_merge(load_mapping(base), load_mapping(overlay))
    atomic_write(output, json.dumps(merged, indent=2, ensure_ascii=False) + "\n")
    return merged
