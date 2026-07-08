from __future__ import annotations

from collections import Counter
from typing import Any


def capture(interface: str | None = None, count: int = 100, timeout: int = 30, bpf: str = "") -> dict[str, Any]:
    try:
        from scapy.all import IP, TCP, UDP, sniff
    except ImportError as exc:
        raise RuntimeError("Instale scapy para capturar pacotes") from exc
    packets = sniff(iface=interface, count=count, timeout=timeout, filter=bpf or None, store=True)
    protocols: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    destinations: Counter[str] = Counter()
    bytes_total = 0
    for packet in packets:
        bytes_total += len(packet)
        if IP in packet:
            sources[packet[IP].src] += 1
            destinations[packet[IP].dst] += 1
        protocols["TCP" if TCP in packet else "UDP" if UDP in packet else packet.name] += 1
    return {
        "packets": len(packets),
        "bytes": bytes_total,
        "protocols": protocols.most_common(),
        "top_sources": sources.most_common(10),
        "top_destinations": destinations.most_common(10),
    }
