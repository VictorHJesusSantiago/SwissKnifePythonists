from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


class CredentialProvider(Protocol):
    def update(self, identity: str, secret: str) -> None: ...


@dataclass(slots=True)
class Rotation:
    identity: str
    rotated_at: str
    length: int


def generate_secret(length: int = 32) -> str:
    if length < 16:
        raise ValueError("Credenciais devem ter no mínimo 16 caracteres")
    alphabet = string.ascii_letters + string.digits + "!@#$%_-"
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(length))
        if any(c.islower() for c in value) and any(c.isupper() for c in value) and any(
            c.isdigit() for c in value
        ):
            return value


def rotate(identity: str, provider: CredentialProvider, length: int = 32) -> tuple[Rotation, str]:
    secret = generate_secret(length)
    provider.update(identity, secret)
    return Rotation(identity, datetime.now(UTC).isoformat(), length), secret
