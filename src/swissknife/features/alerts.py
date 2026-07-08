from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Callable

from swissknife.core.database import Database
from swissknife.core.http import request


@dataclass(slots=True)
class Alert:
    source: str
    severity: str
    title: str
    body: str

    @property
    def fingerprint(self) -> str:
        raw = f"{self.source}|{self.severity}|{self.title}".encode()
        return hashlib.sha256(raw).hexdigest()[:24]


class AlertManager:
    def __init__(self, database: Database, suppression_minutes: int = 15):
        self.database = database
        self.suppression = timedelta(minutes=suppression_minutes)

    def dispatch(self, alert: Alert, sender: Callable[[Alert], None]) -> bool:
        previous = self.database.get_state("alerts", alert.fingerprint)
        now = datetime.now(UTC)
        if previous and now - datetime.fromisoformat(previous) < self.suppression:
            return False
        sender(alert)
        self.database.set_state("alerts", alert.fingerprint, now.isoformat())
        self.database.add_event("alert", alert.source, alert.severity, {"title": alert.title})
        return True


def webhook_sender(url: str) -> Callable[[Alert], None]:
    def send(alert: Alert) -> None:
        code, _, _ = request(
            url, method="POST", payload={"text": f"[{alert.severity}] {alert.title}\n{alert.body}"}
        )
        if code >= 400:
            raise RuntimeError(f"Webhook retornou HTTP {code}")

    return send
