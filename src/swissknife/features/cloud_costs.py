from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True)
class ResourceCost:
    provider: str
    resource_id: str
    service: str
    monthly_cost: float
    utilization: float | None = None


def optimize(resources: Iterable[ResourceCost], idle_threshold: float = 5.0) -> dict[str, object]:
    items = list(resources)
    recommendations = []
    savings = 0.0
    for item in items:
        if item.utilization is not None and item.utilization < idle_threshold:
            estimate = item.monthly_cost * 0.8
            savings += estimate
            recommendations.append(
                {
                    "provider": item.provider,
                    "resource_id": item.resource_id,
                    "action": "desligar ou redimensionar",
                    "estimated_savings": round(estimate, 2),
                }
            )
    return {
        "total_monthly_cost": round(sum(item.monthly_cost for item in items), 2),
        "estimated_savings": round(savings, 2),
        "recommendations": recommendations,
    }


def aws_monthly_costs(start: str, end: str) -> list[ResourceCost]:
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("Instale boto3 para consultar custos AWS") from exc
    response = boto3.client("ce").get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    return [
        ResourceCost("aws", group["Keys"][0], group["Keys"][0], float(group["Metrics"]["UnblendedCost"]["Amount"]))
        for period in response["ResultsByTime"]
        for group in period["Groups"]
    ]
