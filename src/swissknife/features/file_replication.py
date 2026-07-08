from __future__ import annotations

import shutil
from pathlib import Path

from swissknife.core.utils import checksum


def replicate(source: str | Path, destination: str | Path, overwrite: bool = False) -> dict[str, int]:
    src, dst = Path(source), Path(destination)
    if not src.is_dir():
        raise ValueError("Origem deve ser um diretório")
    copied = skipped = verified = 0
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        relative = item.relative_to(src)
        target = dst / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        source_hash = checksum(item)
        if target.exists() and not overwrite and checksum(target) == source_hash:
            skipped += 1
            continue
        temporary = target.with_suffix(target.suffix + ".partial")
        shutil.copy2(item, temporary)
        if checksum(temporary) != source_hash:
            temporary.unlink(missing_ok=True)
            raise IOError(f"Checksum inválido: {relative}")
        temporary.replace(target)
        copied += 1
        verified += 1
    return {"copied": copied, "skipped": skipped, "verified": verified}
