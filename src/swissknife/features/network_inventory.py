from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Asset:
    ip: str
    hostname: str | None
    open_ports: list[int]


def _probe(ip: str, ports: list[int], timeout: float) -> Asset | None:
    open_ports = []
    for port in ports:
        with socket.socket() as sock:
            sock.settimeout(timeout)
            if sock.connect_ex((ip, port)) == 0:
                open_ports.append(port)
    if not open_ports:
        return None
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except socket.herror:
        hostname = None
    return Asset(ip, hostname, open_ports)


def discover(
    network: str,
    ports: list[int] | None = None,
    timeout: float = 0.25,
    workers: int = 64,
    max_hosts: int = 1024,
) -> list[dict[str, object]]:
    subnet = ipaddress.ip_network(network, strict=False)
    hosts = list(subnet.hosts())
    if len(hosts) > max_hosts:
        raise ValueError(f"Rede possui {len(hosts)} hosts; limite explícito é {max_hosts}")
    selected = ports or [22, 80, 443, 3389]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        assets = pool.map(lambda ip: _probe(str(ip), selected, timeout), hosts)
    return [asdict(asset) for asset in assets if asset]
