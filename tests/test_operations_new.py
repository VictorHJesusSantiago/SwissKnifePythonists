from datetime import datetime, timedelta
from pathlib import Path

from swissknife.features.changelog import Commit, render
from swissknife.features.config_drift import compare, snapshot
from swissknife.features.maintenance_scheduler import list_windows, notify, schedule
from swissknife.features.permission_audit import audit_path, audit_tree
from swissknife.features.rollback_assistant import plan_rollback, record_deploy
from swissknife.features.runbook_generator import generate


def test_changelog_render() -> None:
    commits = [Commit("abc123", "feat: novo recurso"), Commit("def456", "fix: corrige bug")]
    text = render(commits, version="1.1.0")
    assert "Funcionalidades" in text
    assert "Correções" in text


def test_rollback_assistant(tmp_path: Path) -> None:
    database = tmp_path / "deploys.db"
    record_deploy(database, "prod", "1.0.0", "app-1.0.0.tar.gz")
    record_deploy(database, "prod", "1.1.0", "app-1.1.0.tar.gz")
    plan = plan_rollback(database, "prod")
    assert plan["possible"] is True
    assert plan["target_version"] == "1.0.0"


def test_config_drift(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    snapshot({"a": 1, "b": {"c": 2}}, baseline)
    result = compare(baseline, {"a": 1, "b": {"c": 3}, "d": 4})
    assert result["drifted"] is True
    assert "b.c" in result["changed"]
    assert "d" in result["added"]


def test_runbook_generator(tmp_path: Path) -> None:
    script = tmp_path / "script.py"
    script.write_text('"""Realiza rotina de manutenção."""\n\ndef executar():\n    """Executa a rotina."""\n    pass\n', encoding="utf-8")
    content = generate(script)
    assert "Runbook" in content
    assert "executar" in content


def test_maintenance_scheduler(tmp_path: Path) -> None:
    database = tmp_path / "maintenance.db"
    now = datetime(2026, 1, 1, 10, 0, 0)
    created = schedule(database, "Upgrade de banco", now, now + timedelta(hours=1), ["api", "db"])
    windows = list_windows(database)
    assert len(windows) == 1
    result = notify(database, created["id"], tmp_path / "notifications")
    assert Path(result["path"]).exists()


def test_permission_audit(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    target.write_text("dado", encoding="utf-8")
    result = audit_path(target)
    assert result["path"] == str(target)
    assert isinstance(audit_tree(tmp_path), list)
