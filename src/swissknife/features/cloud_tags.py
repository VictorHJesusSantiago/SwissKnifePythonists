from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True)
class CloudResource:
    provider: str
    identifier: str
    kind: str
    tags: dict[str, str]


def audit(
    resources: Iterable[CloudResource], required: list[str], allowed: dict[str, set[str]] | None = None
) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for resource in resources:
        missing = [tag for tag in required if not resource.tags.get(tag)]
        invalid = {
            tag: value
            for tag, values in (allowed or {}).items()
            if (value := resource.tags.get(tag)) is not None and value not in values
        }
        if missing or invalid:
            violations.append(
                {
                    "provider": resource.provider,
                    "resource_id": resource.identifier,
                    "missing": missing,
                    "invalid": invalid,
                }
            )
    return violations
