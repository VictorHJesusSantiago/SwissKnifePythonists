from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swissknife.core.config import load_mapping
from swissknife.core.utils import run


@dataclass(slots=True)
class DeployStage:
    name: str
    command: list[str]
    timeout: int = 600


@dataclass(slots=True)
class DeployPlan:
    application: str
    environment: str
    stages: list[DeployStage] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path, environment: str) -> "DeployPlan":
        config = load_mapping(path)
        raw = config["environments"][environment]
        stages = [
            DeployStage(item["name"], [str(part) for part in item["command"]], item.get("timeout", 600))
            for item in raw["stages"]
        ]
        return cls(config["application"], environment, stages)

    def execute(self, confirm: bool = False) -> list[dict[str, Any]]:
        outcomes = []
        for stage in self.stages:
            result = run(stage.command, execute=confirm, timeout=stage.timeout)
            result["stage"] = stage.name
            outcomes.append(result)
            if result["executed"] and result["returncode"] != 0:
                break
        return outcomes
