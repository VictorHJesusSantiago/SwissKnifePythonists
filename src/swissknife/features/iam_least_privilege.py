from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass(slots=True)
class UsageEvent:
    identity: str
    action: str
    resource: str


@dataclass(slots=True)
class GrantedPermission:
    identity: str
    action: str


def observed_actions(events: list[UsageEvent]) -> dict[str, set[str]]:
    usage: dict[str, set[str]] = {}
    for event in events:
        usage.setdefault(event.identity, set()).add(event.action)
    return usage


def recommend_policy(events: list[UsageEvent]) -> dict[str, object]:
    usage = observed_actions(events)
    counts = Counter(event.identity for event in events)
    return {
        identity: {
            "recommended_actions": sorted(actions),
            "observed_calls": counts[identity],
        }
        for identity, actions in usage.items()
    }


def find_excess_permissions(events: list[UsageEvent], granted: list[GrantedPermission]) -> dict[str, list[str]]:
    usage = observed_actions(events)
    excess: dict[str, list[str]] = {}
    granted_by_identity: dict[str, set[str]] = {}
    for grant in granted:
        granted_by_identity.setdefault(grant.identity, set()).add(grant.action)
    for identity, actions in granted_by_identity.items():
        unused = sorted(actions - usage.get(identity, set()))
        if unused:
            excess[identity] = unused
    return excess
