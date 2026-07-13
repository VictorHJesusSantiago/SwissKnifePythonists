from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

CATEGORY_PATTERNS: dict[str, re.Pattern[str]] = {
    "Funcionalidades": re.compile(r"^feat(\(.+\))?!?:", re.I),
    "Correções": re.compile(r"^fix(\(.+\))?!?:", re.I),
    "Documentação": re.compile(r"^docs(\(.+\))?!?:", re.I),
    "Refatorações": re.compile(r"^refactor(\(.+\))?!?:", re.I),
    "Performance": re.compile(r"^perf(\(.+\))?!?:", re.I),
    "Testes": re.compile(r"^test(\(.+\))?!?:", re.I),
    "Manutenção": re.compile(r"^chore(\(.+\))?!?:", re.I),
}


@dataclass(slots=True)
class Commit:
    hash: str
    subject: str

    @property
    def category(self) -> str:
        for category, pattern in CATEGORY_PATTERNS.items():
            if pattern.match(self.subject):
                return category
        return "Outros"

    @property
    def breaking(self) -> bool:
        return "!" in self.subject.split(":", 1)[0] or "BREAKING CHANGE" in self.subject


def read_commits(revision_range: str = "", repo: str = ".") -> list[Commit]:
    command = ["git", "-C", repo, "log", "--pretty=format:%h%x1f%s"]
    if revision_range:
        command.append(revision_range)
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    commits: list[Commit] = []
    for line in process.stdout.splitlines():
        if "\x1f" not in line:
            continue
        commit_hash, subject = line.split("\x1f", 1)
        commits.append(Commit(commit_hash, subject))
    return commits


def render(commits: list[Commit], version: str = "Não lançado") -> str:
    grouped: dict[str, list[Commit]] = {}
    breaking: list[Commit] = []
    for commit in commits:
        grouped.setdefault(commit.category, []).append(commit)
        if commit.breaking:
            breaking.append(commit)
    lines = [f"## {version}", ""]
    if breaking:
        lines.append("### ⚠ Mudanças incompatíveis")
        lines.extend(f"- {commit.subject} ({commit.hash})" for commit in breaking)
        lines.append("")
    for category in [*CATEGORY_PATTERNS.keys(), "Outros"]:
        items = grouped.get(category)
        if not items:
            continue
        lines.append(f"### {category}")
        lines.extend(f"- {commit.subject} ({commit.hash})" for commit in items)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def generate(revision_range: str = "", version: str = "Não lançado", repo: str = ".") -> str:
    return render(read_commits(revision_range, repo), version)
