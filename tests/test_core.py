from pathlib import Path

from swissknife.core.database import Database
from swissknife.core.models import Result, Status
from swissknife.core.utils import atomic_write, checksum


def test_result_serialization() -> None:
    value = Result("api", Status.OK, "Tudo certo", {"latency": 12})
    assert value.to_dict()["status"] == "ok"
    assert "timestamp" in value.to_dict()


def test_database_state_and_events(tmp_path: Path) -> None:
    database = Database(tmp_path / "state.db")
    database.set_state("test", "answer", {"value": 42})
    assert database.get_state("test", "answer") == {"value": 42}
    database.add_event("check", "api", "ok", {"latency": 10})
    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1


def test_atomic_write_and_checksum(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "value.txt"
    atomic_write(target, "conteúdo")
    assert target.read_text(encoding="utf-8") == "conteúdo"
    assert len(checksum(target)) == 64
