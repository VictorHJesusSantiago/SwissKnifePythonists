from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from swissknife.core.utils import atomic_write
from swissknife.features.snapshots import Snapshot
from swissknife.features.vault import SecretVault


class JsonIdentitySystem:
    """Adaptador local para testar workflows de pessoas sem diretório corporativo."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _load(self) -> dict[str, dict[str, object]]:
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def _save(self, data: dict[str, dict[str, object]]) -> None:
        atomic_write(self.path, json.dumps(data, indent=2, ensure_ascii=False))

    def grant(self, user: str, group: str) -> None:
        data = self._load()
        entry = data.setdefault(user, {"enabled": True, "groups": []})
        groups = cast(list[str], entry.setdefault("groups", []))
        if group not in groups:
            groups.append(group)
        entry["enabled"] = True
        self._save(data)

    def revoke(self, user: str, group: str) -> None:
        data = self._load()
        entry = data.setdefault(user, {"enabled": True, "groups": []})
        groups = cast(list[str], entry.get("groups", []))
        entry["groups"] = [item for item in groups if item != group]
        self._save(data)

    def disable(self, user: str) -> None:
        data = self._load()
        data.setdefault(user, {"groups": []})["enabled"] = False
        self._save(data)


class VaultCredentialProvider:
    def __init__(self, vault: SecretVault):
        self.vault = vault

    def update(self, identity: str, secret: str) -> None:
        self.vault.set(f"credential:{identity}", secret)


class DirectorySnapshotProvider:
    """Snapshots locais por arquivos, útil para ensaio do ciclo de vida."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def list(self, resource_id: str) -> list[Snapshot]:
        snapshots = []
        for path in self.root.glob(f"{resource_id}--*.snapshot"):
            timestamp = datetime.fromtimestamp(path.stat().st_mtime, UTC)
            snapshots.append(Snapshot(path.stem, resource_id, timestamp, ".protected." in path.name))
        return snapshots

    def create(self, resource_id: str, name: str) -> Snapshot:
        target = self.root / f"{resource_id}--{name}.snapshot"
        target.touch()
        return Snapshot(target.stem, resource_id, datetime.now(UTC))

    def delete(self, snapshot_id: str) -> None:
        matches = list(self.root.glob(f"{snapshot_id}.snapshot"))
        if not matches:
            raise FileNotFoundError(snapshot_id)
        matches[0].unlink()
