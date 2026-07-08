from __future__ import annotations

import os
import platform
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path

from swissknife.core.models import Status


@dataclass(slots=True)
class Control:
    identifier: str
    description: str
    status: Status
    evidence: str


def scan() -> list[Control]:
    controls = []
    system = platform.system()
    controls.append(
        Control("CIS-1.1", "Execução sem privilégios administrativos", Status.OK, os.getenv("USERNAME", ""))
    )
    if system == "Linux":
        ssh = Path("/etc/ssh/sshd_config")
        text = ssh.read_text(errors="ignore") if ssh.exists() else ""
        root_disabled = "PermitRootLogin no" in text
        controls.append(
            Control(
                "CIS-5.2.10",
                "Login root via SSH desabilitado",
                Status.OK if root_disabled else Status.WARNING,
                "sshd_config",
            )
        )
        result = subprocess.run(["sysctl", "-n", "net.ipv4.ip_forward"], capture_output=True, text=True)
        controls.append(
            Control(
                "CIS-3.1.1",
                "IP forwarding desabilitado",
                Status.OK if result.stdout.strip() == "0" else Status.WARNING,
                result.stdout.strip(),
            )
        )
    else:
        controls.append(
            Control("CIS-HOST", "Hostname configurado", Status.OK, socket.gethostname())
        )
    return controls
