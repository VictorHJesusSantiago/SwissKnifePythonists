from __future__ import annotations

import difflib
import functools
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class PlannedAction:
    description: str
    before: str = ""
    after: str = ""

    @property
    def diff(self) -> str:
        if not self.before and not self.after:
            return ""
        return "\n".join(
            difflib.unified_diff(
                self.before.splitlines(),
                self.after.splitlines(),
                fromfile="antes",
                tofile="depois",
                lineterm="",
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {"description": self.description, "diff": self.diff}


@dataclass(slots=True)
class DryRunPlan:
    actions: list[PlannedAction] = field(default_factory=list)

    def add(self, description: str, before: str = "", after: str = "") -> None:
        self.actions.append(PlannedAction(description, before, after))

    def to_dict(self) -> dict[str, object]:
        return {"action_count": len(self.actions), "actions": [action.to_dict() for action in self.actions]}


def dry_runnable(execute_flag_name: str = "execute") -> Callable[[Callable[..., T]], Callable[..., T | dict[str, object]]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T | dict[str, object]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T | dict[str, object]:
            execute = kwargs.get(execute_flag_name, False)
            if execute:
                return func(*args, **kwargs)
            return {"executed": False, "would_call": func.__name__, "args": [repr(arg) for arg in args], "kwargs": {k: repr(v) for k, v in kwargs.items() if k != execute_flag_name}}

        return wrapper

    return decorator
