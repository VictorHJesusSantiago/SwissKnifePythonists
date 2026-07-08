from __future__ import annotations

import hashlib
import hmac
from typing import Any


def pseudonymize(value: Any, secret: str, prefix: str = "anon") -> str:
    digest = hmac.new(secret.encode(), str(value).encode(), hashlib.sha256).hexdigest()[:16]
    return f"{prefix}_{digest}"


def mask_email(value: str) -> str:
    local, separator, domain = value.partition("@")
    if not separator:
        return "***"
    return f"{local[:1]}***@{domain}"


def anonymize_rows(
    rows: list[dict[str, Any]], rules: dict[str, str], secret: str
) -> list[dict[str, Any]]:
    output = []
    for original in rows:
        row = dict(original)
        for column, rule in rules.items():
            if column not in row or row[column] is None:
                continue
            if rule == "hash":
                row[column] = pseudonymize(row[column], secret)
            elif rule == "email":
                row[column] = mask_email(str(row[column]))
            elif rule == "redact":
                row[column] = "[REDACTED]"
            elif rule == "null":
                row[column] = None
            else:
                raise ValueError(f"Regra desconhecida: {rule}")
        output.append(row)
    return output
