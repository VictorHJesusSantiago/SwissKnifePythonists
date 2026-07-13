from swissknife.features.cidr_calculator import contains, describe, overlaps, split, summarize
from swissknife.features.firewall_validator import validate
from swissknife.features.latency_tester import measure
from swissknife.features.topology_diagram import to_dot, to_mermaid


def test_cidr_calculator() -> None:
    info = describe("192.168.1.0/24")
    assert info["usable_hosts"] == 254
    subnets = split("192.168.1.0/24", 26)
    assert len(subnets) == 4
    assert contains("192.168.1.0/24", "192.168.1.10")
    assert overlaps("192.168.1.0/24", "192.168.1.128/25")
    assert summarize(["192.168.0.0/25", "192.168.0.128/25"]) == ["192.168.0.0/24"]


def test_firewall_validator() -> None:
    rules = "allow tcp from 0.0.0.0/0 to any port 3389\nallow tcp from 10.0.0.0/8 to any port 443\n"
    violations = validate(rules)
    assert len(violations) == 1
    assert "3389" in violations[0].reason


def test_topology_diagram() -> None:
    assets = [{"ip": "10.0.0.5", "hostname": "web01", "open_ports": [80, 443]}]
    mermaid = to_mermaid(assets)
    dot = to_dot(assets)
    assert "web01" in mermaid
    assert "digraph" in dot


def test_latency_tester() -> None:
    report = measure("127.0.0.1", port=65530, count=2, timeout=0.1)
    assert report.sent == 2
    assert report.loss_percent == 100.0
