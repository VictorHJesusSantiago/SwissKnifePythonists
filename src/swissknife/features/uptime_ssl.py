from __future__ import annotations

import socket
import ssl
from datetime import UTC, datetime
from urllib.parse import urlparse

from swissknife.core.http import request
from swissknife.core.models import Result, Status


def inspect(url: str, timeout: float = 10, warning_days: int = 30) -> Result:
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        raise ValueError(f"URL inválida: {url}")
    try:
        code, _, elapsed = request(url, timeout=timeout, retries=0)
        metrics: dict[str, float | int | str] = {
            "status_code": code,
            "latency_ms": round(elapsed * 1000, 2),
        }
        status = Status.OK if code < 400 else Status.CRITICAL
        message = f"HTTP {code}"
        if parsed.scheme == "https":
            context = ssl.create_default_context()
            with socket.create_connection((host, parsed.port or 443), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as secure:
                    certificate = secure.getpeercert()
            not_after = certificate.get("notAfter") if certificate else None
            if not isinstance(not_after, str):
                raise RuntimeError("Certificado não informou a data de expiração")
            expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=UTC)
            remaining = (expires - datetime.now(UTC)).days
            metrics.update(ssl_days=remaining, ssl_expires=expires.isoformat())
            if remaining < 0:
                status, message = Status.CRITICAL, "Certificado expirado"
            elif remaining <= warning_days and status == Status.OK:
                status, message = Status.WARNING, "Certificado próximo do vencimento"
        return Result(url, status, message, metrics)
    except Exception as exc:
        return Result(url, Status.CRITICAL, str(exc))
