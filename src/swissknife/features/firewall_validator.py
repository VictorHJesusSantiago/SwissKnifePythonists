from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass

RULE_PATTERN = re.compile(
    r"^(?P<action>allow|deny)\s+(?P<protocol>tcp|udp|any)\s+from\s+(?P<source>\S+)\s+to\s+(?P<destination>\S+)\s+port\s+(?P<port>[\d,\-]+)$",
    re.I,
)


@dataclass(slots=True)
class FirewallRule:
    action: str
    protocol: str
    source: str
    destination: str
    port: str
    line_number: int


@dataclass(slots=True)
class Violation:
    line_number: int
    rule_text: str
    reason: str


RISKY_PORTS = {22, 23, 3389, 445, 3306, 5432, 6379, 27017}


def parse_rules(text: str) -> list[FirewallRule]:
    rules = []
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = RULE_PATTERN.match(line)
        if match:
            rules.append(FirewallRule(line_number=line_number, **match.groupdict()))
    return rules


def _expand_ports(port_spec: str) -> set[int]:
    ports: set[int] = set()
    for chunk in port_spec.split(","):
        if "-" in chunk:
            start, end = chunk.split("-", 1)
            ports.update(range(int(start), int(end) + 1))
        else:
            ports.add(int(chunk))
    return ports


def validate(text: str) -> list[Violation]:
    violations: list[Violation] = []
    for rule in parse_rules(text):
        if rule.action.lower() != "allow":
            continue
        is_open_source = rule.source in ("0.0.0.0/0", "any", "*")
        try:
            network = ipaddress.ip_network(rule.source, strict=False)
            is_open_source = is_open_source or network.num_addresses > 65536
        except ValueError:
            pass
        if not is_open_source:
            continue
        ports = _expand_ports(rule.port)
        risky_hit = ports & RISKY_PORTS
        if risky_hit:
            violations.append(
                Violation(
                    rule.line_number,
                    f"allow {rule.protocol} from {rule.source} to {rule.destination} port {rule.port}",
                    f"origem irrestrita liberando porta(s) sensível(is): {sorted(risky_hit)}",
                )
            )
    return violations
