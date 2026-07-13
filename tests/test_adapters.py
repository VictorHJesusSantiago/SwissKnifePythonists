from pathlib import Path

from swissknife.features.local_adapters import DirectorySnapshotProvider, JsonIdentitySystem
from swissknife.features.network_config import apply_template
from swissknife.features.people import PeoplePlan, offboard, onboard
from swissknife.features.snapshots import apply_lifecycle


class FakeDevice:
    def __init__(self) -> None:
        self.running = "hostname old\n"
        self.candidate = ""
        self.committed = False

    def get_config(self) -> str:
        return self.running

    def load_candidate(self, config: str) -> None:
        self.candidate = config

    def compare(self) -> str:
        return "changed"

    def commit(self) -> None:
        self.committed = True

    def discard(self) -> None:
        self.candidate = ""


def test_network_config_dry_run_and_commit(tmp_path: Path) -> None:
    template = tmp_path / "router.conf"
    template.write_text("hostname new\n", encoding="utf-8")
    device = FakeDevice()
    assert apply_template(device, template).changed
    assert not device.committed
    assert apply_template(device, template, execute=True).committed


def test_people_local_adapter(tmp_path: Path) -> None:
    system = JsonIdentitySystem(tmp_path / "identities.json")
    plan = PeoplePlan("ana", ["vpn", "developers"])
    onboard(plan, system, execute=True)
    assert system._load()["ana"]["enabled"] is True
    offboard(plan, system, execute=True)
    assert system._load()["ana"]["enabled"] is False


def test_local_snapshot_lifecycle(tmp_path: Path) -> None:
    provider = DirectorySnapshotProvider(tmp_path / "snapshots")
    result = apply_lifecycle(provider, "disk-1", execute=True)
    assert result["executed"] is True
    assert len(provider.list("disk-1")) == 1
