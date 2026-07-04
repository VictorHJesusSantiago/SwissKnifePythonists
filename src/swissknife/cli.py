from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import typer

from swissknife import __version__
from swissknife.core.config import load_mapping

app = typer.Typer(
    name="skp",
    help="SwissKnife Pythonists — automação de operações, segurança, dados e cloud.",
    no_args_is_help=True,
)


def emit(value: object) -> None:
    typer.echo(json.dumps(value, indent=2, ensure_ascii=False, default=str))


@app.callback()
def main(version: Annotated[bool, typer.Option("--version", help="Exibe a versão.")] = False) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()


@app.command("health")
def health(config: Path, workers: int = 10) -> None:
    """Executa health-checks definidos em YAML/JSON."""
    from swissknife.features.dashboard import targets_from_file
    from swissknife.features.health import check_all

    emit([result.to_dict() for result in check_all(targets_from_file(config), workers)])


@app.command("dashboard")
def dashboard(config: Path, host: str = "127.0.0.1", port: int = 8090) -> None:
    """Inicia dashboard web local de health-check."""
    from swissknife.features.dashboard import serve

    typer.echo(f"Dashboard em http://{host}:{port}")
    serve(config, host, port)


@app.command("deploy")
def deploy(config: Path, environment: str, execute: bool = False) -> None:
    """Executa ou simula um pipeline de deploy padronizado."""
    from swissknife.features.deploy import DeployPlan

    emit(DeployPlan.load(config, environment).execute(execute))


@app.command("backup")
def backup(source: Path, destination: Path) -> None:
    from swissknife.features.backups import create_backup

    emit(create_backup(source, destination))


@app.command("rotate-backups")
def rotate_backups(directory: Path, keep: int = 7, days: int = 30) -> None:
    from swissknife.features.backups import rotate

    emit({"removed": rotate(directory, keep=keep, days=days)})


@app.command("rotate-logs")
def rotate_logs(directory: Path, max_bytes: int = 10_000_000, copies: int = 5) -> None:
    from swissknife.features.backups import rotate_logs as action

    emit({"rotated": action(directory, max_bytes, copies)})


@app.command("inventory")
def inventory(network: str, ports: str = "22,80,443,3389", authorize: bool = False) -> None:
    """Inventaria uma rede autorizada por sondagem TCP."""
    from swissknife.features.network_inventory import discover

    if not authorize:
        raise typer.BadParameter("Use --authorize para confirmar autorização sobre a rede")
    emit(discover(network, [int(value) for value in ports.split(",")]))


@app.command("uptime")
def uptime(url: str, warning_days: int = 30) -> None:
    from swissknife.features.uptime_ssl import inspect

    emit(inspect(url, warning_days=warning_days).to_dict())


@app.command("dependencies")
def dependencies(path: Path = Path(".")) -> None:
    from swissknife.features.dependency_scanner import scan

    emit(scan(path))


vault_app = typer.Typer(help="Cofre local de segredos.")
app.add_typer(vault_app, name="vault")


def get_vault(path: Path):
    from swissknife.features.vault import SecretVault

    password = os.getenv("SKP_MASTER_PASSWORD")
    if not password:
        password = typer.prompt("Senha mestra", hide_input=True)
    return SecretVault(path, password)


@vault_app.command("set")
def vault_set(name: str, path: Path = Path(".skp/vault.json")) -> None:
    value = typer.prompt("Valor", hide_input=True)
    get_vault(path).set(name, value)
    typer.echo("Segredo armazenado.")


@vault_app.command("get")
def vault_get(name: str, path: Path = Path(".skp/vault.json")) -> None:
    typer.echo(get_vault(path).get(name))


@vault_app.command("list")
def vault_list(path: Path = Path(".skp/vault.json")) -> None:
    emit(get_vault(path).names())


@app.command("report")
def report(input_csv: Path, output_html: Path = Path("reports/report.html")) -> None:
    from swissknife.features.reports import generate

    emit(generate(input_csv, output_html))


@app.command("etl")
def etl(source: Path, mapping: Path, database: Path, table: str) -> None:
    from swissknife.features.etl import extract_csv, extract_json, load_sqlite, transform

    records = extract_json(source) if source.suffix.lower() == ".json" else extract_csv(source)
    emit({"loaded": load_sqlite(transform(records, load_mapping(mapping)), database, table)})


@app.command("faq")
def faq(knowledge_base: Path, question: str) -> None:
    from dataclasses import asdict
    from swissknife.features.faq_bot import FAQ

    emit(asdict(FAQ.load(knowledge_base).answer(question)))


@app.command("cloud-costs")
def cloud_costs(input_json: Path) -> None:
    from swissknife.features.cloud_costs import ResourceCost, optimize

    items = json.loads(input_json.read_text(encoding="utf-8"))
    emit(optimize(ResourceCost(**item) for item in items))


@app.command("cloud-tags")
def cloud_tags(input_json: Path, required: str = "Owner,Environment,CostCenter") -> None:
    from swissknife.features.cloud_tags import CloudResource, audit

    items = json.loads(input_json.read_text(encoding="utf-8"))
    emit(audit((CloudResource(**item) for item in items), required.split(",")))


@app.command("docker-audit")
def docker_audit(image: str) -> None:
    from swissknife.features.docker_audit import audit

    emit(audit(image))


@app.command("test-data")
def test_data(count: int, database: Path = Path("test-data.db"), seed: int = 42) -> None:
    from swissknife.features.test_data import generate_customers, persist_sqlite

    emit({"generated": persist_sqlite(generate_customers(count, seed), database), "database": str(database)})


@app.command("anonymize")
def anonymize(source: Path, rules: Path, output: Path, secret: str = "") -> None:
    from swissknife.core.utils import atomic_write
    from swissknife.features.anonymizer import anonymize_rows

    key = secret or os.getenv("SKP_ANONYMIZATION_KEY", "")
    if len(key) < 8:
        raise typer.BadParameter("Informe --secret ou SKP_ANONYMIZATION_KEY com 8+ caracteres")
    rows = json.loads(source.read_text(encoding="utf-8"))
    result = anonymize_rows(rows, load_mapping(rules), key)
    atomic_write(output, json.dumps(result, indent=2, ensure_ascii=False))
    emit({"rows": len(result), "output": str(output)})


@app.command("hardening")
def hardening() -> None:
    from dataclasses import asdict
    from swissknife.features.hardening import scan

    emit([asdict(item) for item in scan()])


@app.command("phishing")
def phishing(subject: str, body_file: Path) -> None:
    from dataclasses import asdict
    from swissknife.features.phishing import classify

    emit(asdict(classify(subject, body_file.read_text(encoding="utf-8"))))


@app.command("iac-policy")
def iac_policy(plan: Path, fail_on_violation: bool = True) -> None:
    from dataclasses import asdict
    from swissknife.features.iac_policy import validate

    violations = validate(plan)
    emit([asdict(item) for item in violations])
    if violations and fail_on_violation:
        raise typer.Exit(2)


@app.command("config-sync")
def config_sync(base: Path, overlay: Path, output: Path) -> None:
    from swissknife.features.config_sync import synchronize

    emit(synchronize(base, overlay, output))


@app.command("slo")
def slo(service: str, target: float, good: int, total: int, window_days: int = 30) -> None:
    from swissknife.features.slo import SLO, calculate

    emit(calculate(SLO(service, target, window_days), good, total))


@app.command("replicate")
def replicate(source: Path, destination: Path, overwrite: bool = False) -> None:
    from swissknife.features.file_replication import replicate as action

    emit(action(source, destination, overwrite))


@app.command("wiki-search")
def wiki_search(root: Path, query: str, limit: int = 5) -> None:
    from swissknife.features.wiki import WikiIndex

    emit(WikiIndex(root).search(query, limit))


@app.command("capacity")
def capacity(samples: str, limit: float, interval_hours: float = 1) -> None:
    from swissknife.features.capacity import linear_forecast

    emit(linear_forecast([float(x) for x in samples.split(",")], limit, interval_hours))


@app.command("tech-debt")
def tech_debt(root: Path = Path("."), threshold: int = 10) -> None:
    from swissknife.features.tech_debt import scan

    emit(scan(root, threshold))


@app.command("code-docs")
def code_docs(source: Path = Path("src"), output: Path = Path("docs/API.md")) -> None:
    from swissknife.features.code_docs import generate

    emit(generate(source, output))


@app.command("load-scenario")
def load_scenario(spec: Path, output: Path = Path("locustfile.py")) -> None:
    """Gera um cenário Locust a partir de JSON."""
    from swissknife.features.load_scenarios import generate

    generate(spec, output)
    emit({"output": str(output)})


@app.command("packet-capture")
def packet_capture(
    interface: str = "", count: int = 100, timeout: int = 30, bpf: str = "", authorize: bool = False
) -> None:
    """Captura e resume tráfego de uma interface autorizada."""
    from swissknife.features.packet_analyzer import capture

    if not authorize:
        raise typer.BadParameter("Use --authorize para confirmar autorização")
    emit(capture(interface or None, count, timeout, bpf))


@app.command("honeypot")
def honeypot(host: str = "127.0.0.1", ports: str = "2222,8081") -> None:
    """Inicia honeypot TCP interno em primeiro plano."""
    import asyncio
    from swissknife.features.honeypot import Honeypot

    asyncio.run(Honeypot(host, [int(item) for item in ports.split(",")]).serve())


@app.command("rotate-credential")
def rotate_credential(
    identity: str, vault_path: Path = Path(".skp/vault.json"), length: int = 32
) -> None:
    """Rotaciona uma credencial e guarda o novo valor no cofre."""
    from dataclasses import asdict
    from swissknife.features.credential_rotation import rotate
    from swissknife.features.local_adapters import VaultCredentialProvider

    rotation, _ = rotate(identity, VaultCredentialProvider(get_vault(vault_path)), length)
    emit(asdict(rotation))


@app.command("snapshots-local")
def snapshots_local(
    resource_id: str,
    directory: Path = Path(".skp/snapshots"),
    retention_days: int = 30,
    execute: bool = False,
) -> None:
    """Simula ou aplica ciclo de vida em um provedor local de snapshots."""
    from swissknife.features.local_adapters import DirectorySnapshotProvider
    from swissknife.features.snapshots import apply_lifecycle

    emit(apply_lifecycle(DirectorySnapshotProvider(directory), resource_id, retention_days, execute))


@app.command("people")
def people(
    action: str,
    user: str,
    groups: str,
    database: Path = Path(".skp/identities.json"),
    execute: bool = False,
) -> None:
    """Simula/aplica onboarding ou offboarding no diretório local."""
    from swissknife.features.local_adapters import JsonIdentitySystem
    from swissknife.features.people import PeoplePlan, offboard, onboard

    plan = PeoplePlan(user, [item for item in groups.split(",") if item])
    system = JsonIdentitySystem(database)
    if action == "onboard":
        emit(onboard(plan, system, execute))
    elif action == "offboard":
        emit(offboard(plan, system, execute))
    else:
        raise typer.BadParameter("action deve ser onboard ou offboard")


if __name__ == "__main__":
    app()
