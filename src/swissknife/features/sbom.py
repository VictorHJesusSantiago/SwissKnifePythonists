from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

from swissknife.core.utils import atomic_write


def collect_packages() -> list[dict[str, Any]]:
    packages = []
    for distribution in metadata.distributions():
        name = distribution.metadata.get("Name") or distribution.metadata.get("Summary") or "desconhecido"
        packages.append(
            {
                "name": name,
                "version": distribution.version,
                "license": distribution.metadata.get("License") or "não informado",
                "requires": [str(req) for req in (distribution.requires or [])],
            }
        )
    return sorted(packages, key=lambda item: item["name"].lower())


def build_sbom(component_name: str = "projeto", packages: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    packages = packages if packages is not None else collect_packages()
    return {
        "bomFormat": "SwissKnifeSBOM",
        "specVersion": "1.0",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "createdAt": datetime.now(UTC).isoformat(),
        "component": component_name,
        "componentCount": len(packages),
        "components": [
            {"type": "library", "name": item["name"], "version": item["version"], "license": item["license"]}
            for item in packages
        ],
    }


def write_sbom(path: str | Path, component_name: str = "projeto") -> dict[str, Any]:
    sbom = build_sbom(component_name)
    atomic_write(path, json.dumps(sbom, indent=2, ensure_ascii=False))
    return {"path": str(path), "componentCount": sbom["componentCount"]}
