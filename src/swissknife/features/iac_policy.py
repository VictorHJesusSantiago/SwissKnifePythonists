from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Violation:
    rule: str
    resource: str
    message: str
    severity: str = "high"


def validate(plan_path: str | Path) -> list[Violation]:
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    violations = []
    for change in plan.get("resource_changes", []):
        address = change.get("address", "unknown")
        after: dict[str, Any] = change.get("change", {}).get("after") or {}
        resource_type = change.get("type", "")
        tags = after.get("tags") or {}
        if not tags.get("Owner") or not tags.get("Environment"):
            violations.append(Violation("required-tags", address, "Tags Owner e Environment são obrigatórias"))
        if resource_type in {"aws_s3_bucket", "azurerm_storage_account"}:
            if after.get("public_access_enabled") is True or after.get("account_kind") == "public":
                violations.append(Violation("no-public-storage", address, "Storage público não permitido"))
        if after.get("encrypted") is False:
            violations.append(Violation("encryption-required", address, "Criptografia deve estar habilitada"))
    return violations
