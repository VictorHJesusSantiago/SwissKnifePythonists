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


def _load_plugins() -> list[str]:
    """Carrega plugins de SKP_PLUGINS_DIR (padrão: .skp/plugins) sem alterar o core."""
    from swissknife.features.plugin_system import load_into

    plugins_dir = Path(os.getenv("SKP_PLUGINS_DIR", ".skp/plugins"))
    if not plugins_dir.exists():
        return []
    try:
        return load_into(app, plugins_dir)
    except Exception as exc:  # plugin de terceiros não deve derrubar o CLI
        typer.echo(f"Aviso: falha ao carregar plugins de {plugins_dir}: {exc}", err=True)
        return []


_load_plugins()


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


# --- Observabilidade -------------------------------------------------------


@app.command("anomaly-detect")
def anomaly_detect(log_file: Path, z_threshold: float = 3.0) -> None:
    from swissknife.features.anomaly_detector import analyze

    emit(analyze(log_file, z_threshold))


@app.command("incident-correlate")
def incident_correlate(events_json: Path, window_seconds: float = 300) -> None:
    from datetime import datetime

    from swissknife.features.incident_correlator import Event, correlate

    raw = json.loads(events_json.read_text(encoding="utf-8"))
    events = [Event(item["source"], item["message"], datetime.fromisoformat(item["timestamp"]), item.get("severity", "info")) for item in raw]
    emit([incident.to_dict() for incident in correlate(events, window_seconds)])


@app.command("postmortem")
def postmortem_cmd(events_json: Path, title: str, impact: str, output: Path, root_cause: str = "A investigar") -> None:
    from datetime import datetime

    from swissknife.features.incident_correlator import Event, Incident
    from swissknife.features.postmortem import generate, write

    raw = json.loads(events_json.read_text(encoding="utf-8"))
    events = [Event(item["source"], item["message"], datetime.fromisoformat(item["timestamp"]), item.get("severity", "info")) for item in raw]
    content = generate(title, Incident(events), impact, root_cause)
    emit(write(output, content))


@app.command("resource-check")
def resource_check(path: str = ".", disk_percent: float = 90, memory_percent: float = 90, load_per_cpu: float = 1.5) -> None:
    from swissknife.features.resource_monitor import Thresholds, check

    emit(check(path, Thresholds(disk_percent, memory_percent, load_per_cpu)).to_dict())


@app.command("sla-record")
def sla_record(database: Path, service: str, good: int, total: int) -> None:
    from swissknife.features.sla_tracker import record

    emit(record(database, service, good, total))


@app.command("sla-history")
def sla_history_cmd(database: Path, service: str) -> None:
    from swissknife.features.sla_tracker import summarize

    emit(summarize(database, service))


@app.command("error-budget")
def error_budget_cmd(
    service: str, target_percent: float, window_days: float, bad_events: int, total_events: int, elapsed_hours: float
) -> None:
    from swissknife.features.error_budget import simulate

    emit(simulate(service, target_percent, window_days, bad_events, total_events, elapsed_hours).to_dict())


# --- Operações ---------------------------------------------------------


@app.command("changelog")
def changelog_cmd(revision_range: str = "", version: str = "Não lançado", repo: str = ".") -> None:
    from swissknife.features.changelog import generate

    typer.echo(generate(revision_range, version, repo))


@app.command("deploy-record")
def deploy_record(database: Path, environment: str, version: str, artifact: str, status: str = "success") -> None:
    from swissknife.features.rollback_assistant import record_deploy

    emit(record_deploy(database, environment, version, artifact, status))


@app.command("rollback-plan")
def rollback_plan_cmd(database: Path, environment: str) -> None:
    from swissknife.features.rollback_assistant import plan_rollback

    emit(plan_rollback(database, environment))


@app.command("config-snapshot")
def config_snapshot(config: Path, output: Path) -> None:
    from swissknife.core.config import load_mapping
    from swissknife.features.config_drift import snapshot

    emit(snapshot(load_mapping(config), output))


@app.command("config-drift")
def config_drift_cmd(baseline: Path, current: Path) -> None:
    from swissknife.core.config import load_mapping
    from swissknife.features.config_drift import compare

    emit(compare(baseline, load_mapping(current)))


@app.command("runbook")
def runbook_cmd(script: Path, output: Path, title: str = "") -> None:
    from swissknife.core.utils import atomic_write
    from swissknife.features.runbook_generator import generate

    content = generate(script, title)
    atomic_write(output, content)
    emit({"output": str(output)})


@app.command("maintenance-schedule")
def maintenance_schedule_cmd(database: Path, title: str, starts_at: str, ends_at: str, affected: str) -> None:
    from datetime import datetime

    from swissknife.features.maintenance_scheduler import schedule

    emit(
        schedule(
            database,
            title,
            datetime.fromisoformat(starts_at),
            datetime.fromisoformat(ends_at),
            [item for item in affected.split(",") if item],
        )
    )


@app.command("maintenance-list")
def maintenance_list_cmd(database: Path, upcoming_only: bool = False) -> None:
    from dataclasses import asdict

    from swissknife.features.maintenance_scheduler import list_windows

    emit([asdict(window) for window in list_windows(database, upcoming_only)])


@app.command("maintenance-notify")
def maintenance_notify_cmd(database: Path, window_id: int, notifications_dir: Path = Path(".skp/notifications")) -> None:
    from swissknife.features.maintenance_scheduler import notify

    emit(notify(database, window_id, notifications_dir))


@app.command("permission-audit")
def permission_audit_cmd(root: Path = Path(".")) -> None:
    from swissknife.features.permission_audit import audit_tree, summarize

    results = audit_tree(root)
    emit({"summary": summarize(results), "results": results})


# --- Segurança -----------------------------------------------------------


@app.command("secret-scan")
def secret_scan_cmd(root: Path = Path(".")) -> None:
    from swissknife.features.secret_scanner import scan

    emit(scan(root))


@app.command("password-check")
def password_check_cmd(password: str = typer.Option(..., prompt=True, hide_input=True)) -> None:
    from swissknife.features.password_policy import PasswordPolicy, validate_password

    result = validate_password(password, PasswordPolicy())
    emit({"valid": result.valid, "violations": result.violations})


@app.command("attack-surface")
def attack_surface_cmd(host: str, ports: str = "", authorize: bool = False) -> None:
    from swissknife.features.attack_surface import scan_host

    if not authorize:
        raise typer.BadParameter("Use --authorize para confirmar autorização sobre o host")
    selected_ports = [int(item) for item in ports.split(",")] if ports else None
    emit(scan_host(host, selected_ports, authorize=authorize))


@app.command("sbom")
def sbom_cmd(output: Path = Path("sbom.json"), component: str = "projeto") -> None:
    from swissknife.features.sbom import write_sbom

    emit(write_sbom(output, component))


@app.command("license-check")
def license_check_cmd(allowed: str = "permissiva") -> None:
    from swissknife.features.license_checker import audit

    emit(audit(allowed.split(",")))


# --- Rede ------------------------------------------------------------------


@app.command("cidr")
def cidr_cmd(cidr: str, split_prefix: int = 0) -> None:
    from swissknife.features.cidr_calculator import describe, split

    if split_prefix:
        emit(split(cidr, split_prefix))
    else:
        emit(describe(cidr))


@app.command("firewall-validate")
def firewall_validate_cmd(rules_file: Path) -> None:
    from dataclasses import asdict

    from swissknife.features.firewall_validator import validate

    violations = validate(rules_file.read_text(encoding="utf-8"))
    emit([asdict(violation) for violation in violations])


@app.command("topology-diagram")
def topology_diagram_cmd(assets_json: Path, output: Path, format_name: str = "mermaid") -> None:
    from swissknife.core.utils import atomic_write
    from swissknife.features.topology_diagram import to_dot, to_mermaid

    assets = json.loads(assets_json.read_text(encoding="utf-8"))
    content = to_mermaid(assets) if format_name == "mermaid" else to_dot(assets)
    atomic_write(output, content)
    emit({"output": str(output)})


@app.command("latency-test")
def latency_test_cmd(host: str, port: int = 443, count: int = 4) -> None:
    from swissknife.features.latency_tester import measure

    emit(measure(host, port, count).to_dict())


# --- Cloud -----------------------------------------------------------------


@app.command("cost-whatif")
def cost_whatif_cmd(resources_json: Path, hours: float = 730) -> None:
    from swissknife.features.cost_whatif import PricedResource, estimate

    items = json.loads(resources_json.read_text(encoding="utf-8"))
    emit(estimate([PricedResource(**item) for item in items], hours))


@app.command("iam-least-privilege")
def iam_least_privilege_cmd(events_json: Path) -> None:
    from swissknife.features.iam_least_privilege import UsageEvent, recommend_policy

    items = json.loads(events_json.read_text(encoding="utf-8"))
    emit(recommend_policy([UsageEvent(**item) for item in items]))


@app.command("orphan-resources")
def orphan_resources_cmd(resources_json: Path, idle_days: int = 30) -> None:
    from datetime import datetime

    from swissknife.features.orphan_resources import CloudResourceRecord, find_orphans

    items = json.loads(resources_json.read_text(encoding="utf-8"))
    records = [
        CloudResourceRecord(
            item["resource_id"],
            item["resource_type"],
            item.get("attached_to"),
            datetime.fromisoformat(item["last_used_at"]) if item.get("last_used_at") else None,
            item.get("monthly_cost", 0.0),
        )
        for item in items
    ]
    emit(find_orphans(records, idle_days))


# --- Dados -----------------------------------------------------------------


@app.command("schema-validate")
def schema_validate_cmd(rows_json: Path, schema_json: Path) -> None:
    from swissknife.features.schema_validator import FieldSchema, Schema, validate_dataset

    rows = json.loads(rows_json.read_text(encoding="utf-8"))
    schema_fields = json.loads(schema_json.read_text(encoding="utf-8"))
    schema = Schema([FieldSchema(**field_spec) for field_spec in schema_fields])
    emit(validate_dataset(rows, schema))


@app.command("data-dictionary")
def data_dictionary_cmd(rows_json: Path, output: Path = Path("docs/data-dictionary.md")) -> None:
    from swissknife.core.utils import atomic_write
    from swissknife.features.data_dictionary import generate, to_markdown

    rows = json.loads(rows_json.read_text(encoding="utf-8"))
    dictionary = generate(rows)
    atomic_write(output, to_markdown(dictionary))
    emit(dictionary)


@app.command("dedup")
def dedup_cmd(rows_json: Path, fields: str, threshold: float = 0.9) -> None:
    from swissknife.features.dedup import deduplicate

    rows = json.loads(rows_json.read_text(encoding="utf-8"))
    emit(deduplicate(rows, fields.split(","), threshold))


@app.command("dataset-diff")
def dataset_diff_cmd(left_json: Path, right_json: Path, key_field: str) -> None:
    from swissknife.features.dataset_diff import diff

    left = json.loads(left_json.read_text(encoding="utf-8"))
    right = json.loads(right_json.read_text(encoding="utf-8"))
    emit(diff(left, right, key_field))


@app.command("data-mask")
def data_mask_cmd(rows_json: Path, rules_json: Path, output: Path) -> None:
    from swissknife.core.utils import atomic_write
    from swissknife.features.data_masking import apply_masking

    rows = json.loads(rows_json.read_text(encoding="utf-8"))
    rules = json.loads(rules_json.read_text(encoding="utf-8"))
    masked = apply_masking(rows, rules)
    atomic_write(output, json.dumps(masked, indent=2, ensure_ascii=False))
    emit({"rows": len(masked), "output": str(output)})


@app.command("data-profile")
def data_profile_cmd(rows_json: Path) -> None:
    from swissknife.features.data_profiler import profile_dataset

    rows = json.loads(rows_json.read_text(encoding="utf-8"))
    emit(profile_dataset(rows))


# --- Engenharia --------------------------------------------------------


@app.command("semantic-changelog")
def semantic_changelog_cmd(current_version: str, revision_range: str = "", repo: str = ".") -> None:
    from swissknife.features.semantic_changelog import plan_release

    emit(plan_release(current_version, revision_range, repo))


@app.command("code-metrics")
def code_metrics_cmd(root: Path = Path(".")) -> None:
    from swissknife.features.code_metrics import analyze_tree

    emit(analyze_tree(root))


@app.command("duplicate-code")
def duplicate_code_cmd(root: Path = Path("."), min_lines: int = 6) -> None:
    from swissknife.features.duplicate_code import find_duplicates

    emit(find_duplicates(root, min_lines))


@app.command("test-skeleton")
def test_skeleton_cmd(source_file: Path, source_root: Path = Path("src"), output: Path | None = None) -> None:
    from swissknife.core.utils import atomic_write
    from swissknife.features.test_skeleton_generator import generate

    content = generate(source_file, source_root)
    if output is not None:
        atomic_write(output, content)
        emit({"output": str(output)})
    else:
        typer.echo(content)


@app.command("naming-lint")
def naming_lint_cmd(root: Path = Path(".")) -> None:
    from swissknife.features.naming_lint import lint_tree

    emit(lint_tree(root))


@app.command("arch-diagram")
def arch_diagram_cmd(source_root: Path = Path("src"), output: Path = Path("docs/arch-diagram.mmd")) -> None:
    from swissknife.core.utils import atomic_write
    from swissknife.features.arch_diagram import build_dependency_graph, to_mermaid

    graph = build_dependency_graph(source_root)
    atomic_write(output, to_mermaid(graph))
    emit({"output": str(output), "modules": len(graph)})


@app.command("coverage-gaps")
def coverage_gaps_cmd(coverage_xml: Path, threshold: float = 80.0) -> None:
    from swissknife.features.coverage_gaps import find_gaps, parse_coverage_xml

    coverage = parse_coverage_xml(coverage_xml)
    emit({"overall_percent": coverage["overall_percent"], "gaps": find_gaps(coverage, threshold)})


# --- Pessoas ---------------------------------------------------------------


@app.command("skills-matrix")
def skills_matrix_cmd(entries_json: Path, output: Path = Path("docs/skills-matrix.md")) -> None:
    from swissknife.core.utils import atomic_write
    from swissknife.features.skills_matrix import SkillEntry, to_markdown

    items = json.loads(entries_json.read_text(encoding="utf-8"))
    entries = [SkillEntry(**item) for item in items]
    atomic_write(output, to_markdown(entries))
    emit({"output": str(output), "people": len({entry.person for entry in entries})})


@app.command("onboarding-start")
def onboarding_start_cmd(database: Path, person: str) -> None:
    from swissknife.features.onboarding_tracker import start

    emit(start(database, person).to_dict())


@app.command("onboarding-complete")
def onboarding_complete_cmd(database: Path, person: str, item: str) -> None:
    from swissknife.features.onboarding_tracker import complete_item

    emit(complete_item(database, person, item).to_dict())


@app.command("onboarding-status")
def onboarding_status_cmd(database: Path, person: str) -> None:
    from swissknife.features.onboarding_tracker import status

    emit(status(database, person))


@app.command("feedback-template")
def feedback_template_cmd(name: str) -> None:
    from swissknife.features.feedback_templates import render

    typer.echo(render(name))


# --- Transversal -------------------------------------------------------


@app.command("export")
def export_cmd(rows_json: Path, output: Path, format_name: str = "markdown", title: str = "Relatório") -> None:
    from swissknife.features.universal_exporter import export

    rows = json.loads(rows_json.read_text(encoding="utf-8"))
    emit(export(rows, output, format_name, title))


@app.command("audit-log-record")
def audit_log_record_cmd(log_path: Path, actor: str, command: str, arguments_json: str = "{}") -> None:
    from swissknife.features.audit_log import record

    secret = os.getenv("SKP_AUDIT_SECRET", "")
    if len(secret) < 8:
        raise typer.BadParameter("Defina SKP_AUDIT_SECRET com 8+ caracteres")
    emit(record(log_path, secret, actor, command, json.loads(arguments_json)))


@app.command("audit-log-verify")
def audit_log_verify_cmd(log_path: Path) -> None:
    from swissknife.features.audit_log import verify

    secret = os.getenv("SKP_AUDIT_SECRET", "")
    if len(secret) < 8:
        raise typer.BadParameter("Defina SKP_AUDIT_SECRET com 8+ caracteres")
    emit(verify(log_path, secret))


@app.command("env-wizard")
def env_wizard_cmd(env_example: Path, answers_json: Path, output: Path = Path(".env")) -> None:
    from swissknife.features.env_wizard import parse_env_example, write_env

    schema = parse_env_example(env_example)
    answers = json.loads(answers_json.read_text(encoding="utf-8"))
    emit(write_env(schema, answers, output))


@app.command("translate")
def translate_cmd(key: str, locale: str = "pt-BR") -> None:
    from swissknife.features.i18n import Translator

    typer.echo(Translator(locale).t(key))


if __name__ == "__main__":
    app()
