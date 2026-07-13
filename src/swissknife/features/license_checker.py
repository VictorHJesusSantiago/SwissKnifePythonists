from __future__ import annotations

from swissknife.features.sbom import collect_packages

PERMISSIVE = {"mit", "bsd", "apache", "apache 2.0", "apache-2.0", "isc", "python software foundation license", "bsd-3-clause", "bsd-2-clause"}
COPYLEFT = {"gpl", "gplv2", "gplv3", "agpl", "lgpl", "gnu general public license", "gnu lesser general public license", "gnu affero general public license"}


def classify(license_text: str) -> str:
    normalized = (license_text or "").strip().lower()
    if not normalized or normalized in {"não informado", "unknown", "none"}:
        return "desconhecida"
    if any(token in normalized for token in COPYLEFT):
        return "copyleft"
    if any(token in normalized for token in PERMISSIVE):
        return "permissiva"
    return "outra"


def audit(allowed_categories: list[str] | None = None) -> dict[str, object]:
    allowed = set(allowed_categories or ["permissiva"])
    packages = collect_packages()
    incompatible = []
    summary: dict[str, int] = {}
    for package in packages:
        category = classify(package["license"])
        summary[category] = summary.get(category, 0) + 1
        if category not in allowed and category != "desconhecida":
            incompatible.append({"name": package["name"], "version": package["version"], "license": package["license"], "category": category})
    return {"total": len(packages), "summary": summary, "incompatible": incompatible}
