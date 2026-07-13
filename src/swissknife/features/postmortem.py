from __future__ import annotations

from pathlib import Path
from typing import Any

from swissknife.core.utils import atomic_write
from swissknife.features.incident_correlator import Incident


def generate(
    title: str,
    incident: Incident,
    impact: str,
    root_cause: str = "A investigar",
    action_items: list[str] | None = None,
) -> str:
    action_items = action_items or []
    lines = [
        f"# Post-mortem: {title}",
        "",
        f"- Início: {incident.started_at.isoformat()}",
        f"- Fim: {incident.ended_at.isoformat()}",
        f"- Fontes envolvidas: {', '.join(incident.sources)}",
        f"- Eventos correlacionados: {len(incident.events)}",
        "",
        "## Impacto",
        impact,
        "",
        "## Causa raiz",
        root_cause,
        "",
        "## Linha do tempo",
    ]
    for event in sorted(incident.events, key=lambda item: item.timestamp):
        lines.append(f"- `{event.timestamp.isoformat()}` [{event.source}/{event.severity}] {event.message}")
    lines.append("")
    lines.append("## Ações de acompanhamento")
    if action_items:
        lines.extend(f"- [ ] {item}" for item in action_items)
    else:
        lines.append("- [ ] Definir ações de acompanhamento")
    return "\n".join(lines) + "\n"


def write(path: str | Path, content: str) -> dict[str, Any]:
    atomic_write(path, content)
    return {"path": str(path), "bytes": len(content.encode("utf-8"))}
