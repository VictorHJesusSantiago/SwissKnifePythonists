from datetime import UTC, datetime, timedelta
from pathlib import Path

from swissknife.features.attack_surface import scan_host
from swissknife.features.license_checker import classify
from swissknife.features.password_policy import PasswordPolicy, rotation_status, validate_password
from swissknife.features.sbom import build_sbom
from swissknife.features.secret_scanner import scan


def test_secret_scanner(tmp_path: Path) -> None:
    target = tmp_path / "config.py"
    target.write_text('AWS_KEY = "AKIAABCDEFGHIJKLMNOP"\npassword = "supersecretvalue123"\n', encoding="utf-8")
    result = scan(tmp_path)
    assert result["total"] >= 1


def test_password_policy() -> None:
    policy = PasswordPolicy()
    weak = validate_password("senha123", policy)
    assert weak.valid is False
    strong = validate_password("Tr0ub4dor&3xtra!", policy)
    assert strong.valid is True
    status = rotation_status(datetime.now(UTC) - timedelta(days=100), policy)
    assert status["rotation_due"] is True


def test_attack_surface() -> None:
    result = scan_host("127.0.0.1", ports=[65530], timeout=0.1, authorize=True)
    assert result["host"] == "127.0.0.1"
    assert "surface_score" in result


def test_sbom() -> None:
    sbom = build_sbom("meu-projeto", packages=[{"name": "pkg", "version": "1.0", "license": "MIT"}])
    assert sbom["componentCount"] == 1
    assert sbom["components"][0]["name"] == "pkg"


def test_license_classify() -> None:
    assert classify("MIT License") == "permissiva"
    assert classify("GPL-3.0") == "copyleft"
    assert classify("") == "desconhecida"
