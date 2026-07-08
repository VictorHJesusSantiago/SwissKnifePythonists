from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class DeviceDriver(Protocol):
    def get_config(self) -> str: ...
    def load_candidate(self, config: str) -> None: ...
    def compare(self) -> str: ...
    def commit(self) -> None: ...
    def discard(self) -> None: ...


@dataclass(slots=True)
class ConfigResult:
    changed: bool
    diff: str
    committed: bool


def apply_template(driver: DeviceDriver, template: str | Path, execute: bool = False) -> ConfigResult:
    desired = Path(template).read_text(encoding="utf-8")
    current = driver.get_config()
    fallback_diff = "".join(
        difflib.unified_diff(
            current.splitlines(True), desired.splitlines(True), fromfile="running", tofile="candidate"
        )
    )
    if not fallback_diff:
        return ConfigResult(False, "", False)
    driver.load_candidate(desired)
    diff = driver.compare() or fallback_diff
    if execute:
        driver.commit()
    else:
        driver.discard()
    return ConfigResult(True, diff, execute)


def napalm_driver(host: str, username: str, password: str, platform: str = "ios") -> DeviceDriver:
    try:
        from napalm import get_network_driver
    except ImportError as exc:
        raise RuntimeError("Instale napalm para configurar dispositivos") from exc
    raw = get_network_driver(platform)(hostname=host, username=username, password=password)
    raw.open()
    return NapalmAdapter(raw)


class NapalmAdapter:
    def __init__(self, driver: Any):
        self.driver = driver

    def get_config(self) -> str:
        config = self.driver.get_config()
        return config.get("running", "") if isinstance(config, dict) else str(config)

    def load_candidate(self, config: str) -> None:
        self.driver.load_merge_candidate(config=config)

    def compare(self) -> str:
        return str(self.driver.compare_config())

    def commit(self) -> None:
        self.driver.commit_config()

    def discard(self) -> None:
        self.driver.discard_config()
