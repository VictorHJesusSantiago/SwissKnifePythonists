from __future__ import annotations

import stat
import sys
from pathlib import Path


def _mode_string(mode: int) -> str:
    return stat.filemode(mode)


def audit_path(path: str | Path) -> dict[str, object]:
    target = Path(path)
    info = target.stat()
    mode = info.st_mode
    findings: list[str] = []
    if sys.platform != "win32":
        if mode & stat.S_IWOTH:
            findings.append("gravável por outros (world-writable)")
        if target.is_file() and mode & stat.S_IXOTH and not (mode & stat.S_IXUSR):
            findings.append("executável por outros sem ser pelo dono")
        if mode & stat.S_ISUID:
            findings.append("bit SUID habilitado")
        if mode & stat.S_ISGID:
            findings.append("bit SGID habilitado")
    else:
        import os

        if not (info.st_file_attributes & 0x1):  # FILE_ATTRIBUTE_READONLY
            findings.append("gravável (sem atributo somente leitura)")
    return {
        "path": str(target),
        "mode": _mode_string(mode),
        "owner_writable": bool(mode & stat.S_IWUSR),
        "findings": findings,
        "risk": "alto" if findings else "baixo",
    }


def audit_tree(root: str | Path, pattern: str = "*") -> list[dict[str, object]]:
    results = []
    for path in Path(root).rglob(pattern):
        if path.is_dir():
            continue
        try:
            results.append(audit_path(path))
        except OSError:
            continue
    return results


def summarize(results: list[dict[str, object]]) -> dict[str, object]:
    risky = [item for item in results if item["risk"] == "alto"]
    return {"total": len(results), "risky": len(risky), "risky_paths": [item["path"] for item in risky]}
