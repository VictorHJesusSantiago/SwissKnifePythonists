from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SLO:
    service: str
    target_percent: float
    window_days: int = 30


def calculate(slo: SLO, good: int, total: int, elapsed_days: float | None = None) -> dict[str, float]:
    if total <= 0:
        raise ValueError("total deve ser maior que zero")
    achieved = good / total * 100
    allowed_bad = total * (1 - slo.target_percent / 100)
    consumed = (total - good) / allowed_bad * 100 if allowed_bad else 0.0
    elapsed = elapsed_days if elapsed_days is not None else slo.window_days
    expected_elapsed = elapsed / slo.window_days * 100
    return {
        "achieved_percent": round(achieved, 5),
        "error_budget_consumed_percent": round(consumed, 2),
        "burn_rate": round(consumed / expected_elapsed, 3) if expected_elapsed else 0.0,
        "remaining_bad_events": max(0, int(allowed_bad - (total - good))),
    }
