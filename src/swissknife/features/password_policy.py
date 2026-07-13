from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass(slots=True)
class PasswordPolicy:
    min_length: int = 12
    require_upper: bool = True
    require_lower: bool = True
    require_digit: bool = True
    require_symbol: bool = True
    max_age_days: int = 90
    history_size: int = 5
    forbidden: list[str] = field(default_factory=lambda: ["password", "senha", "123456", "qwerty"])


@dataclass(slots=True)
class PolicyResult:
    valid: bool
    violations: list[str]


def validate_password(password: str, policy: PasswordPolicy, history: list[str] | None = None) -> PolicyResult:
    violations: list[str] = []
    if len(password) < policy.min_length:
        violations.append(f"comprimento mínimo de {policy.min_length} caracteres não atingido")
    if policy.require_upper and not re.search(r"[A-Z]", password):
        violations.append("falta letra maiúscula")
    if policy.require_lower and not re.search(r"[a-z]", password):
        violations.append("falta letra minúscula")
    if policy.require_digit and not re.search(r"\d", password):
        violations.append("falta dígito")
    if policy.require_symbol and not re.search(r"[^\w\s]", password):
        violations.append("falta símbolo")
    lowered = password.lower()
    if any(word in lowered for word in policy.forbidden):
        violations.append("contém termo proibido/comum")
    if history and password in history[-policy.history_size :]:
        violations.append("senha já utilizada recentemente")
    return PolicyResult(valid=not violations, violations=violations)


def rotation_status(last_rotated: datetime, policy: PasswordPolicy, now: datetime | None = None) -> dict[str, object]:
    now = now or datetime.now(UTC)
    age_days = (now - last_rotated).days
    due = age_days >= policy.max_age_days
    return {
        "age_days": age_days,
        "max_age_days": policy.max_age_days,
        "rotation_due": due,
        "next_rotation": (last_rotated + timedelta(days=policy.max_age_days)).isoformat(),
    }
