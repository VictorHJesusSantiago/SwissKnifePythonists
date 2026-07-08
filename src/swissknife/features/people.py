from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class IdentitySystem(Protocol):
    def grant(self, user: str, group: str) -> None: ...
    def revoke(self, user: str, group: str) -> None: ...
    def disable(self, user: str) -> None: ...


@dataclass(slots=True)
class PeoplePlan:
    user: str
    groups: list[str] = field(default_factory=list)


def onboard(plan: PeoplePlan, system: IdentitySystem, execute: bool = False) -> list[str]:
    actions = [f"grant:{plan.user}:{group}" for group in plan.groups]
    if execute:
        for group in plan.groups:
            system.grant(plan.user, group)
    return actions


def offboard(plan: PeoplePlan, system: IdentitySystem, execute: bool = False) -> list[str]:
    actions = [f"revoke:{plan.user}:{group}" for group in plan.groups] + [f"disable:{plan.user}"]
    if execute:
        for group in plan.groups:
            system.revoke(plan.user, group)
        system.disable(plan.user)
    return actions
