from __future__ import annotations

import re
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\S*\s+.*?(?P<value>-?\d+(\.\d+)?)"
)


@dataclass(slots=True)
class LogPoint:
    timestamp: str
    value: float
    line: str


@dataclass(slots=True)
class Anomaly:
    timestamp: str
    value: float
    z_score: float
    line: str


def parse_log(path: str | Path, pattern: re.Pattern[str] = DEFAULT_PATTERN) -> list[LogPoint]:
    points: list[LogPoint] = []
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        points.append(LogPoint(match.group("timestamp"), float(match.group("value")), line.strip()))
    return points


def detect_anomalies(points: list[LogPoint], z_threshold: float = 3.0) -> list[Anomaly]:
    if len(points) < 2:
        return []
    values = [point.value for point in points]
    mean = statistics.fmean(values)
    stdev = statistics.pstdev(values)
    if stdev == 0:
        return []
    anomalies: list[Anomaly] = []
    for point in points:
        z_score = (point.value - mean) / stdev
        if abs(z_score) >= z_threshold:
            anomalies.append(Anomaly(point.timestamp, point.value, round(z_score, 3), point.line))
    return anomalies


def analyze(path: str | Path, z_threshold: float = 3.0, pattern: re.Pattern[str] = DEFAULT_PATTERN) -> dict[str, object]:
    points = parse_log(path, pattern)
    anomalies = detect_anomalies(points, z_threshold)
    values = [point.value for point in points]
    baseline = {
        "count": len(values),
        "mean": round(statistics.fmean(values), 4) if values else 0.0,
        "stdev": round(statistics.pstdev(values), 4) if len(values) > 1 else 0.0,
    }
    return {
        "baseline": baseline,
        "anomalies": [asdict(anomaly) for anomaly in anomalies],
        "anomaly_rate": round(len(anomalies) / len(values), 4) if values else 0.0,
    }
