from __future__ import annotations

import gzip
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from swissknife.core.utils import checksum


def create_backup(source: str | Path, destination: str | Path) -> dict[str, str | int]:
    source_path, destination_dir = Path(source), Path(destination)
    if not source_path.is_file():
        raise ValueError("A origem do backup deve ser um arquivo")
    destination_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = destination_dir / f"{source_path.name}.{stamp}.gz"
    with source_path.open("rb") as src, gzip.open(target, "wb", compresslevel=6) as dst:
        shutil.copyfileobj(src, dst)
    return {"path": str(target), "bytes": target.stat().st_size, "sha256": checksum(target)}


def rotate(directory: str | Path, pattern: str = "*.gz", keep: int = 7, days: int = 30) -> list[str]:
    files = sorted(Path(directory).glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
    cutoff = datetime.now(UTC) - timedelta(days=days)
    removed = []
    for index, path in enumerate(files):
        modified = datetime.fromtimestamp(path.stat().st_mtime, UTC)
        if index >= keep and modified < cutoff:
            path.unlink()
            removed.append(str(path))
    return removed


def rotate_logs(directory: str | Path, max_bytes: int, copies: int = 5) -> list[str]:
    rotated = []
    for log in Path(directory).glob("*.log"):
        if log.stat().st_size <= max_bytes:
            continue
        oldest = log.with_suffix(log.suffix + f".{copies}")
        oldest.unlink(missing_ok=True)
        for number in range(copies - 1, 0, -1):
            previous = log.with_suffix(log.suffix + f".{number}")
            if previous.exists():
                previous.replace(log.with_suffix(log.suffix + f".{number + 1}"))
        log.replace(log.with_suffix(log.suffix + ".1"))
        log.touch()
        rotated.append(str(log))
    return rotated
