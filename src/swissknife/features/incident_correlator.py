from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Event:
    source: str
    message: str
    timestamp: datetime
    severity: str = "info"


@dataclass(slots=True)
class Incident:
    events: list[Event] = field(default_factory=list)

    @property
    def sources(self) -> list[str]:
        return sorted({event.source for event in self.events})

    @property
    def started_at(self) -> datetime:
        return min(event.timestamp for event in self.events)

    @property
    def ended_at(self) -> datetime:
        return max(event.timestamp for event in self.events)

    def to_dict(self) -> dict[str, object]:
        return {
            "sources": self.sources,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "event_count": len(self.events),
            "events": [
                {
                    "source": event.source,
                    "message": event.message,
                    "timestamp": event.timestamp.isoformat(),
                    "severity": event.severity,
                }
                for event in sorted(self.events, key=lambda item: item.timestamp)
            ],
        }


def correlate(events: list[Event], window_seconds: float = 300) -> list[Incident]:
    ordered = sorted(events, key=lambda event: event.timestamp)
    incidents: list[Incident] = []
    current: Incident | None = None
    for event in ordered:
        if current is not None and (event.timestamp - current.ended_at).total_seconds() <= window_seconds:
            current.events.append(event)
        else:
            current = Incident([event])
            incidents.append(current)
    return incidents


def multi_source_incidents(incidents: list[Incident], min_sources: int = 2) -> list[Incident]:
    return [incident for incident in incidents if len(incident.sources) >= min_sources]
