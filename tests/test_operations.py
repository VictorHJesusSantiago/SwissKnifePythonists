from pathlib import Path

from swissknife.features.backups import create_backup
from swissknife.features.capacity import linear_forecast
from swissknife.features.config_sync import deep_merge
from swissknife.features.file_replication import replicate
from swissknife.features.slo import SLO, calculate


def test_backup_and_replication(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_text("abc", encoding="utf-8")
    destination = tmp_path / "destination"
    assert replicate(source, destination)["copied"] == 1
    assert replicate(source, destination)["skipped"] == 1
    result = create_backup(source / "a.txt", tmp_path / "backups")
    assert Path(str(result["path"])).exists()


def test_slo_and_capacity() -> None:
    result = calculate(SLO("api", 99.0), 995, 1000)
    assert result["achieved_percent"] == 99.5
    forecast = linear_forecast([10, 20, 30], 100)
    assert forecast["hours_to_capacity"] == 7


def test_deep_merge() -> None:
    assert deep_merge({"a": {"b": 1, "c": 2}}, {"a": {"b": 3}}) == {
        "a": {"b": 3, "c": 2}
    }
