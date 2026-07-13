from __future__ import annotations

import json
from pathlib import Path

DEFAULT_LOCALE = "pt-BR"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "pt-BR": {
        "health.ok": "Serviço disponível",
        "health.critical": "Serviço indisponível",
        "vault.stored": "Segredo armazenado.",
        "cli.version": "Versão",
    },
    "en-US": {
        "health.ok": "Service available",
        "health.critical": "Service unavailable",
        "vault.stored": "Secret stored.",
        "cli.version": "Version",
    },
    "es-ES": {
        "health.ok": "Servicio disponible",
        "health.critical": "Servicio no disponible",
        "vault.stored": "Secreto almacenado.",
        "cli.version": "Versión",
    },
}


class Translator:
    def __init__(self, locale: str = DEFAULT_LOCALE) -> None:
        if locale not in TRANSLATIONS:
            raise ValueError(f"Locale '{locale}' não suportado. Opções: {', '.join(TRANSLATIONS)}")
        self.locale = locale

    def t(self, key: str, **params: object) -> str:
        catalog = TRANSLATIONS[self.locale]
        template = catalog.get(key, TRANSLATIONS[DEFAULT_LOCALE].get(key, key))
        return template.format(**params) if params else template


def load_custom_catalog(path: str | Path) -> dict[str, str]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def register_locale(locale: str, catalog: dict[str, str]) -> None:
    TRANSLATIONS[locale] = catalog


def available_locales() -> list[str]:
    return sorted(TRANSLATIONS)
