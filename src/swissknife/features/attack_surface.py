from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass

RISKY_SERVICES: dict[int, tuple[str, str]] = {
    21: ("FTP", "alto"),
    23: ("Telnet", "alto"),
    25: ("SMTP", "médio"),
    135: ("MSRPC", "alto"),
    139: ("NetBIOS", "alto"),
    445: ("SMB", "alto"),
    1433: ("MSSQL", "médio"),
    3306: ("MySQL", "médio"),
    3389: ("RDP", "alto"),
    5432: ("PostgreSQL", "médio"),
    5900: ("VNC", "alto"),
    6379: ("Redis", "alto"),
    9200: ("Elasticsearch", "alto"),
    27017: ("MongoDB", "alto"),
}

COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 3306, 3389, 5432, 5900, 6379, 8080, 9200, 27017]


@dataclass(slots=True)
class ExposedPort:
    port: int
    service: str
    risk: str


def scan_host(host: str, ports: list[int] | None = None, timeout: float = 0.5, workers: int = 32, authorize: bool = False) -> dict[str, object]:
    if not authorize:
        raise PermissionError("Autorização explícita necessária para varrer o host")
    selected = ports or COMMON_PORTS

    def probe(port: int) -> int | None:
        with socket.socket() as sock:
            sock.settimeout(timeout)
            return port if sock.connect_ex((host, port)) == 0 else None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        open_ports = [port for port in pool.map(probe, selected) if port is not None]
    exposed = [
        ExposedPort(port, *RISKY_SERVICES.get(port, ("desconhecido", "baixo"))) for port in sorted(open_ports)
    ]
    high_risk = [item for item in exposed if item.risk == "alto"]
    return {
        "host": host,
        "open_ports": [asdict(item) for item in exposed],
        "high_risk_count": len(high_risk),
        "surface_score": len(exposed) + 2 * len(high_risk),
    }
