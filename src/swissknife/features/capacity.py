from __future__ import annotations

from math import ceil


def linear_forecast(
    samples: list[float], capacity: float, interval_hours: float = 1.0
) -> dict[str, float | None]:
    if len(samples) < 2:
        raise ValueError("Informe ao menos duas amostras")
    n = len(samples)
    x_mean = (n - 1) / 2
    y_mean = sum(samples) / n
    denominator = sum((x - x_mean) ** 2 for x in range(n))
    slope = sum((x - x_mean) * (y - y_mean) for x, y in enumerate(samples)) / denominator
    current = samples[-1]
    intervals = (capacity - current) / slope if slope > 0 else None
    return {
        "current": current,
        "capacity": capacity,
        "growth_per_interval": round(slope, 6),
        "hours_to_capacity": ceil(intervals * interval_hours) if intervals and intervals > 0 else None,
        "utilization_percent": round(current / capacity * 100, 2),
    }
