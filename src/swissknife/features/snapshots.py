from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol


@dataclass(slots=True)
class Snapshot:
    identifier: str
    resource_id: str
    created_at: datetime
    protected: bool = False


class SnapshotProvider(Protocol):
    def list(self, resource_id: str) -> list[Snapshot]: ...
    def create(self, resource_id: str, name: str) -> Snapshot: ...
    def delete(self, snapshot_id: str) -> None: ...


def apply_lifecycle(
    provider: SnapshotProvider, resource_id: str, retention_days: int = 30, execute: bool = False
) -> dict[str, object]:
    now = datetime.now(UTC)
    name = f"skp-{resource_id}-{now:%Y%m%dT%H%M%SZ}"
    created = provider.create(resource_id, name) if execute else None
    expired = [
        item
        for item in provider.list(resource_id)
        if not item.protected and item.created_at < now - timedelta(days=retention_days)
    ]
    if execute:
        for item in expired:
            provider.delete(item.identifier)
    return {"created": created.identifier if created else name, "expired": [x.identifier for x in expired], "executed": execute}
