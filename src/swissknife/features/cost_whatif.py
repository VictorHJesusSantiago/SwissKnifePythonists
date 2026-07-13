from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PricedResource:
    service: str
    unit_price: float
    quantity: float
    unit: str = "hora"


def estimate(resources: list[PricedResource], hours: float = 730) -> dict[str, object]:
    breakdown = []
    total = 0.0
    for resource in resources:
        cost = resource.unit_price * resource.quantity * (hours if resource.unit == "hora" else 1)
        total += cost
        breakdown.append(
            {
                "service": resource.service,
                "quantity": resource.quantity,
                "unit": resource.unit,
                "unit_price": resource.unit_price,
                "estimated_cost": round(cost, 2),
            }
        )
    return {"total_estimated_cost": round(total, 2), "breakdown": breakdown}


def compare_scenarios(scenarios: dict[str, list[PricedResource]], hours: float = 730) -> dict[str, object]:
    results = {name: estimate(resources, hours) for name, resources in scenarios.items()}
    cheapest = min(results.items(), key=lambda item: item[1]["total_estimated_cost"])
    return {"scenarios": results, "cheapest": cheapest[0], "cheapest_cost": cheapest[1]["total_estimated_cost"]}


def scale_projection(base_resources: list[PricedResource], growth_factors: list[float], hours: float = 730) -> list[dict[str, object]]:
    projections = []
    for factor in growth_factors:
        scaled = [PricedResource(item.service, item.unit_price, item.quantity * factor, item.unit) for item in base_resources]
        result = estimate(scaled, hours)
        projections.append({"growth_factor": factor, **result})
    return projections
