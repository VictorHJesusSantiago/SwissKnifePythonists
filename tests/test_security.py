from pathlib import Path

from swissknife.features.anonymizer import anonymize_rows, mask_email, pseudonymize
from swissknife.features.credential_rotation import generate_secret
from swissknife.features.iac_policy import validate
from swissknife.features.phishing import classify


def test_anonymization_is_deterministic() -> None:
    assert pseudonymize("123", "segredo-forte") == pseudonymize("123", "segredo-forte")
    assert mask_email("ana@example.com") == "a***@example.com"
    rows = anonymize_rows([{"cpf": "1"}], {"cpf": "hash"}, "segredo")
    assert rows[0]["cpf"] != "1"


def test_secret_quality() -> None:
    secret = generate_secret()
    assert len(secret) == 32
    assert any(character.isdigit() for character in secret)


def test_phishing_classifier() -> None:
    result = classify("Urgente: conta bloqueada", "Clique e confirme sua senha immediately")
    assert result.label == "phishing"
    assert result.probability > 0.5


def test_iac_policy_example_is_valid() -> None:
    assert validate(Path("examples/terraform-plan.json")) == []
