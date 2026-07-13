from __future__ import annotations

import socket
import statistics
import time
from dataclasses import asdict, dataclass


@dataclass(slots=True)
class LatencySample:
    sequence: int
    success: bool
    latency_ms: float | None


@dataclass(slots=True)
class LatencyReport:
    host: str
    port: int
    sent: int
    received: int
    loss_percent: float
    min_ms: float | None
    avg_ms: float | None
    max_ms: float | None
    jitter_ms: float | None
    samples: list[LatencySample]

    def to_dict(self) -> dict[str, object]:
        return {
            "host": self.host,
            "port": self.port,
            "sent": self.sent,
            "received": self.received,
            "loss_percent": self.loss_percent,
            "min_ms": self.min_ms,
            "avg_ms": self.avg_ms,
            "max_ms": self.max_ms,
            "jitter_ms": self.jitter_ms,
            "samples": [asdict(sample) for sample in self.samples],
        }


def measure(host: str, port: int = 443, count: int = 4, timeout: float = 2.0) -> LatencyReport:
    samples: list[LatencySample] = []
    for sequence in range(1, count + 1):
        started = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=timeout):
                elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            samples.append(LatencySample(sequence, True, elapsed_ms))
        except OSError:
            samples.append(LatencySample(sequence, False, None))
    latencies = [sample.latency_ms for sample in samples if sample.latency_ms is not None]
    received = len(latencies)
    jitter = round(statistics.pstdev(latencies), 3) if len(latencies) > 1 else 0.0 if latencies else None
    return LatencyReport(
        host=host,
        port=port,
        sent=count,
        received=received,
        loss_percent=round((1 - received / count) * 100, 2) if count else 0.0,
        min_ms=min(latencies) if latencies else None,
        avg_ms=round(statistics.fmean(latencies), 3) if latencies else None,
        max_ms=max(latencies) if latencies else None,
        jitter_ms=jitter,
        samples=samples,
    )
