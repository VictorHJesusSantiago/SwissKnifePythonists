from pathlib import Path

from swissknife.features.code_docs import generate
from swissknife.features.etl import load_sqlite, transform
from swissknife.features.faq_bot import FAQ
from swissknife.features.tech_debt import scan
from swissknife.features.test_data import generate_customers
from swissknife.features.wiki import WikiIndex


def test_etl_and_synthetic_data(tmp_path: Path) -> None:
    rows = generate_customers(5)
    transformed = transform(rows, {"id": "customer_id", "name": "name"})
    assert load_sqlite(transformed, tmp_path / "data.db", "customers") == 5


def test_faq_and_wiki() -> None:
    answer = FAQ.load("examples/faq.json").answer("Esqueci minha senha de acesso")
    assert answer.category == "acesso"
    assert WikiIndex("docs").search("deploy execução")


def test_debt_and_documentation(tmp_path: Path) -> None:
    debt = scan("src", threshold=100)
    assert "score" in debt
    output = tmp_path / "API.md"
    result = generate("src/swissknife/core", output)
    assert result["modules"] > 0
    assert output.exists()
