from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class CloudResourceRecord:
    resource_id: str
    resource_type: str
    attached_to: str | None
    last_used_at: datetime | None
    monthly_cost: float = 0.0


def _as_aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def find_orphans(resources: list[CloudResourceRecord], idle_days: int = 30, now: datetime | None = None) -> dict[str, object]:
    now = _as_aware(now) if now is not None else datetime.now(UTC)
    orphans = []
    for resource in resources:
        reasons = []
        if resource.attached_to is None:
            reasons.append("sem recurso associado")
        if resource.last_used_at is not None:
            idle_for = (now - _as_aware(resource.last_used_at)).days
            if idle_for >= idle_days:
                reasons.append(f"sem uso há {idle_for} dias")
        elif resource.attached_to is None:
            reasons.append("sem registro de uso")
        if reasons:
            orphans.append(
                {
                    "resource_id": resource.resource_id,
                    "resource_type": resource.resource_type,
                    "monthly_cost": resource.monthly_cost,
                    "reasons": reasons,
                }
            )
    return {
        "total_resources": len(resources),
        "orphan_count": len(orphans),
        "potential_savings": round(sum(item["monthly_cost"] for item in orphans), 2),
        "orphans": orphans,
    }
