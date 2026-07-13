from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from swissknife.core.utils import atomic_write

DEFAULT_CHECKLIST = [
    "Conta de acesso criada",
    "Equipamento entregue",
    "Acesso a repositórios concedido",
    "Treinamento de segurança concluído",
    "Reunião 1:1 com gestor realizada",
    "Ambiente de desenvolvimento configurado",
]


@dataclass(slots=True)
class OnboardingRecord:
    person: str
    started_at: str
    checklist: dict[str, bool] = field(default_factory=lambda: {item: False for item in DEFAULT_CHECKLIST})

    @property
    def progress_percent(self) -> float:
        if not self.checklist:
            return 0.0
        done = sum(1 for value in self.checklist.values() if value)
        return round((done / len(self.checklist)) * 100, 2)

    def to_dict(self) -> dict[str, object]:
        return {"person": self.person, "started_at": self.started_at, "checklist": self.checklist, "progress_percent": self.progress_percent}


def start(database: str | Path, person: str, checklist: list[str] | None = None) -> OnboardingRecord:
    items = checklist or DEFAULT_CHECKLIST
    record = OnboardingRecord(person, datetime.now(UTC).isoformat(), {item: False for item in items})
    _save(database, record)
    return record


def complete_item(database: str | Path, person: str, item: str) -> OnboardingRecord:
    records = _load(database)
    if person not in records:
        raise ValueError(f"Onboarding de {person} não encontrado")
    record = records[person]
    if item not in record.checklist:
        raise ValueError(f"Item '{item}' não está no checklist")
    record.checklist[item] = True
    _save(database, record)
    return record


def _load(database: str | Path) -> dict[str, OnboardingRecord]:
    path = Path(database)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {person: OnboardingRecord(person, item["started_at"], item["checklist"]) for person, item in data.items()}


def _save(database: str | Path, record: OnboardingRecord) -> None:
    records = _load(database)
    records[record.person] = record
    payload = {person: {"started_at": item.started_at, "checklist": item.checklist} for person, item in records.items()}
    atomic_write(database, json.dumps(payload, indent=2, ensure_ascii=False))


def status(database: str | Path, person: str) -> dict[str, object]:
    records = _load(database)
    if person not in records:
        raise ValueError(f"Onboarding de {person} não encontrado")
    return records[person].to_dict()
