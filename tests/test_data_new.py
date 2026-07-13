from swissknife.features.data_dictionary import generate as generate_dictionary
from swissknife.features.data_masking import apply_masking, mask_credit_card, mask_document
from swissknife.features.data_profiler import profile_dataset
from swissknife.features.dataset_diff import diff, schema_diff
from swissknife.features.dedup import deduplicate
from swissknife.features.schema_validator import FieldSchema, Schema, validate_dataset


def test_schema_validator() -> None:
    schema = Schema([FieldSchema("id", "integer"), FieldSchema("name", "string")])
    rows = [{"id": 1, "name": "Ana"}, {"id": "x", "extra": True}]
    result = validate_dataset(rows, schema)
    assert result["valid"] is False
    assert result["error_count"] >= 2


def test_data_dictionary() -> None:
    rows = [{"id": 1, "email": "a@example.com"}, {"id": 2, "email": None}]
    dictionary = generate_dictionary(rows)
    assert dictionary["row_count"] == 2
    email_field = next(field for field in dictionary["fields"] if field["name"] == "email")
    assert email_field["nullable"] is True


def test_dedup() -> None:
    rows = [{"name": "Joao Silva"}, {"name": "Joao Silva "}, {"name": "Maria Souza"}]
    result = deduplicate(rows, ["name"], threshold=0.9)
    assert result["clean_count"] == 2


def test_dataset_diff() -> None:
    left = [{"id": 1, "value": "a"}]
    right = [{"id": 1, "value": "b"}, {"id": 2, "value": "c"}]
    result = diff(left, right, "id")
    assert len(result["added"]) == 1
    assert len(result["modified"]) == 1
    assert schema_diff(left, right)["common_columns"] == ["id", "value"]


def test_data_masking() -> None:
    assert mask_credit_card("4111111111111111").endswith("1111")
    assert mask_document("123.456.789-09").count("*") > 0
    rows = [{"cpf": "123.456.789-09"}]
    masked = apply_masking(rows, {"cpf": "document"})
    assert masked[0]["cpf"] != rows[0]["cpf"]


def test_data_profiler() -> None:
    rows = [{"age": 20}, {"age": 25}, {"age": None}]
    profile = profile_dataset(rows)
    assert profile["columns"]["age"]["null_count"] == 1
