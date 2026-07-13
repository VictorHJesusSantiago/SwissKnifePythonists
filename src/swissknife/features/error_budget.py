from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class ErrorBudgetStatus:
    service: str
    target_percent: float
    window_days: float
    budget_minutes: float
    consumed_minutes: float
    burn_rate: float
    remaining_minutes: float
    hours_to_exhaustion: float | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def burn_rate(target_percent: float, bad_events: int, total_events: int) -> float:
    if total_events == 0:
        return 0.0
    allowed_failure_rate = 1 - (target_percent / 100)
    if allowed_failure_rate <= 0:
        return float("inf") if bad_events else 0.0
    observed_failure_rate = bad_events / total_events
    return round(observed_failure_rate / allowed_failure_rate, 4)


def simulate(
    service: str,
    target_percent: float,
    window_days: float,
    bad_events: int,
    total_events: int,
    elapsed_hours: float,
) -> ErrorBudgetStatus:
    window_hours = window_days * 24
    budget_minutes = round(window_hours * 60 * (1 - target_percent / 100), 4)
    rate = burn_rate(target_percent, bad_events, total_events)
    failure_rate = (bad_events / total_events) if total_events else 0.0
    consumed_minutes = round(failure_rate * elapsed_hours * 60, 4)
    remaining_minutes = round(budget_minutes - consumed_minutes, 4)

    hours_to_exhaustion: float | None = None
    if rate > 0 and budget_minutes > 0:
        consumption_per_hour = rate * (budget_minutes / window_hours)
        if consumption_per_hour > 0:
            remaining_window_hours = max(window_hours - elapsed_hours, 0.0)
            projected = max(remaining_minutes, 0.0) / consumption_per_hour
            hours_to_exhaustion = round(min(projected, remaining_window_hours), 2)

    return ErrorBudgetStatus(
        service=service,
        target_percent=target_percent,
        window_days=window_days,
        budget_minutes=budget_minutes,
        consumed_minutes=consumed_minutes,
        burn_rate=rate,
        remaining_minutes=remaining_minutes,
        hours_to_exhaustion=hours_to_exhaustion,
    )
