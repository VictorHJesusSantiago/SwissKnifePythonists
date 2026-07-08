from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any


def audit(image: str, timeout: int = 600) -> dict[str, Any]:
    scanner = shutil.which("trivy") or shutil.which("grype")
    if not scanner:
        raise RuntimeError("Instale Trivy ou Grype para auditar imagens")
    if scanner.lower().endswith("trivy") or "trivy" in scanner.lower():
        command = [scanner, "image", "--format", "json", "--quiet", image]
    else:
        command = [scanner, image, "-o", "json"]
    process = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    if process.returncode not in (0, 1):
        raise RuntimeError(process.stderr.strip())
    report = json.loads(process.stdout)
    return {"image": image, "scanner": scanner, "report": report}
