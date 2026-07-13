from datetime import datetime, timedelta
from pathlib import Path

from swissknife.features.anomaly_detector import analyze
from swissknife.features.error_budget import simulate
from swissknife.features.incident_correlator import Event, correlate, multi_source_incidents
from swissknife.features.postmortem import generate
from swissknife.features.resource_monitor import Thresholds, check, disk_usage
from swissknife.features.sla_tracker import record, summarize


def test_anomaly_detector(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    lines = [f"2026-01-01 00:00:{i:02d} INFO latency={10 + (i % 3)}" for i in range(20)]
    lines.append("2026-01-01 00:01:00 ERROR latency=999")
    log.write_text("\n".join(lines), encoding="utf-8")
    result = analyze(log, z_threshold=2.5)
    assert result["baseline"]["count"] == 21
    assert len(result["anomalies"]) >= 1


def test_incident_correlator() -> None:
    base = datetime(2026, 1, 1, 12, 0, 0)
    events = [
        Event("api", "erro 500", base),
        Event("db", "timeout", base + timedelta(seconds=30)),
        Event("api", "recuperado", base + timedelta(hours=2)),
    ]
    incidents = correlate(events, window_seconds=300)
    assert len(incidents) == 2
    assert len(multi_source_incidents(incidents)) == 1


def test_postmortem() -> None:
    base = datetime(2026, 1, 1, 12, 0, 0)
    from swissknife.features.incident_correlator import Incident

    incident = Incident([Event("api", "erro 500", base)])
    content = generate("Queda da API", incident, impact="Usuários impactados por 10 minutos")
    assert "Post-mortem" in content
    assert "erro 500" in content


def test_resource_monitor() -> None:
    usage = disk_usage(".")
    assert usage["total_gb"] > 0
    result = check(".", Thresholds(disk_percent=1000, memory_percent=1000, load_per_cpu=1000))
    assert result.status.value == "ok"


def test_sla_tracker(tmp_path: Path) -> None:
    database = tmp_path / "sla.db"
    record(database, "api", 990, 1000)
    record(database, "api", 995, 1000)
    summary = summarize(database, "api")
    assert summary["total"] == 2000
    assert summary["achieved_percent"] == 99.25


def test_error_budget() -> None:
    status = simulate("api", 99.9, 30, bad_events=10, total_events=10000, elapsed_hours=100)
    assert status.burn_rate > 0
    assert status.budget_minutes > 0
