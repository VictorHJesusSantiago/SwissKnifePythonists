from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def scan(path: str | Path = ".", timeout: int = 300) -> dict[str, Any]:
    command = [sys.executable, "-m", "pip_audit", "--format", "json", "--progress-spinner", "off"]
    requirements = Path(path)
    if requirements.is_file():
        command.extend(["-r", str(requirements)])
    process = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    if process.returncode not in (0, 1):
        if "No module named pip_audit" in process.stderr:
            raise RuntimeError("Instale pip-audit para executar a varredura")
        raise RuntimeError(process.stderr.strip())
    findings = json.loads(process.stdout or "[]")
    vulnerabilities = sum(len(item.get("vulns", [])) for item in findings)
    return {"dependencies": len(findings), "vulnerabilities": vulnerabilities, "findings": findings}
