from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from swissknife.core.utils import atomic_write


@dataclass(slots=True)
class EnvVariable:
    name: str
    description: str = ""
    default: str = ""
    required: bool = False
    secret: bool = False


@dataclass(slots=True)
class EnvSchema:
    variables: list[EnvVariable] = field(default_factory=list)


def parse_env_example(path: str | Path) -> EnvSchema:
    variables = []
    text = Path(path).read_text(encoding="utf-8")
    pending_description = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            pending_description = stripped.lstrip("#").strip()
            continue
        if not stripped or "=" not in stripped:
            continue
        name, _, default = stripped.partition("=")
        variables.append(
            EnvVariable(
                name=name.strip(),
                description=pending_description,
                default=default.strip(),
                required=not default.strip(),
                secret="secret" in name.lower() or "password" in name.lower() or "token" in name.lower(),
            )
        )
        pending_description = ""
    return EnvSchema(variables)


def build_env(schema: EnvSchema, answers: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for variable in schema.variables:
        value = answers.get(variable.name, variable.default)
        if variable.required and not value:
            raise ValueError(f"Valor obrigatório ausente para {variable.name}")
        result[variable.name] = value
    return result


def write_env(schema: EnvSchema, answers: dict[str, str], output: str | Path) -> dict[str, object]:
    values = build_env(schema, answers)
    content = "\n".join(f"{key}={value}" for key, value in values.items()) + "\n"
    atomic_write(output, content)
    return {"path": str(output), "variables": len(values)}
