import json
from pathlib import Path

from swissknife.features.audit_log import record, verify
from swissknife.features.dry_run import DryRunPlan, dry_runnable
from swissknife.features.env_wizard import build_env, parse_env_example, write_env
from swissknife.features.i18n import Translator, available_locales
from swissknife.features.plugin_system import discover_plugins
from swissknife.features.universal_exporter import export, to_csv, to_html, to_markdown_table


def test_plugin_system(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    (plugins_dir / "hello.py").write_text(
        "def register(app):\n    app.registered = True\n", encoding="utf-8"
    )
    plugins = discover_plugins(plugins_dir)
    assert len(plugins) == 1
    assert plugins[0].name == "hello"


def test_universal_exporter(tmp_path: Path) -> None:
    rows = [{"nome": "Ana", "idade": 30}]
    assert "Ana" in to_markdown_table(rows)
    assert "<table" in to_html(rows)
    assert "Ana" in to_csv(rows)
    output = tmp_path / "relatorio.md"
    result = export(rows, output, "markdown")
    assert result["rows"] == 1
    assert output.exists()


def test_dry_run() -> None:
    plan = DryRunPlan()
    plan.add("Atualizar arquivo de configuração", before="a=1", after="a=2")
    assert "a=1" in plan.actions[0].diff

    @dry_runnable()
    def apagar_tudo(execute: bool = False) -> str:
        return "apagado"

    preview = apagar_tudo(execute=False)
    assert preview["executed"] is False
    assert apagar_tudo(execute=True) == "apagado"


def test_audit_log(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    record(log_path, "segredo123", "victor", "deploy", {"env": "prod"})
    record(log_path, "segredo123", "victor", "rollback", {"env": "prod"})
    result = verify(log_path, "segredo123")
    assert result["valid"] is True
    assert result["entries"] == 2

    tampered = log_path.read_text(encoding="utf-8").splitlines()
    entry = json.loads(tampered[0])
    entry["command"] = "adulterado"
    tampered[0] = json.dumps(entry)
    log_path.write_text("\n".join(tampered) + "\n", encoding="utf-8")
    broken = verify(log_path, "segredo123")
    assert broken["valid"] is False


def test_env_wizard(tmp_path: Path) -> None:
    example = tmp_path / ".env.example"
    example.write_text("# Chave da API\nAPI_TOKEN=\n# Ambiente\nENVIRONMENT=dev\n", encoding="utf-8")
    schema = parse_env_example(example)
    values = build_env(schema, {"API_TOKEN": "abc123"})
    assert values["ENVIRONMENT"] == "dev"
    output = tmp_path / ".env"
    result = write_env(schema, {"API_TOKEN": "abc123"}, output)
    assert result["variables"] == 2
    assert output.exists()


def test_i18n() -> None:
    assert "pt-BR" in available_locales()
    assert Translator("en-US").t("health.ok") == "Service available"
    assert Translator("pt-BR").t("health.ok") == "Serviço disponível"
