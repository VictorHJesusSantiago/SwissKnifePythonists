from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def load_mapping(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        return json.loads(text)
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("Instale PyYAML para ler configurações YAML") from exc
    return yaml.safe_load(text) or {}


@dataclass(frozen=True, slots=True)
class Settings:
    home: Path
    database: Path
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        home = Path(os.getenv("SKP_HOME", ".skp")).expanduser()
        database = Path(os.getenv("SKP_DATABASE", str(home / "swissknife.db"))).expanduser()
        home.mkdir(parents=True, exist_ok=True)
        return cls(home=home, database=database, log_level=os.getenv("SKP_LOG_LEVEL", "INFO"))
