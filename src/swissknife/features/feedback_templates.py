from __future__ import annotations

TEMPLATES: dict[str, list[str]] = {
    "1:1": [
        "O que está indo bem desde nossa última conversa?",
        "O que está te bloqueando ou te preocupando?",
        "Como você avalia sua carga de trabalho atual?",
        "Que apoio você precisa de mim ou da equipe?",
        "Quais são seus objetivos de curto prazo?",
    ],
    "feedback_positivo": [
        "Situação: descreva o contexto específico.",
        "Comportamento: o que a pessoa fez.",
        "Impacto: por que isso importou.",
        "Reforço: como continuar fazendo isso.",
    ],
    "feedback_construtivo": [
        "Situação: descreva o contexto específico.",
        "Comportamento observado: o que aconteceu, sem julgamento.",
        "Impacto: efeito concreto do comportamento.",
        "Próximo passo sugerido: o que fazer diferente.",
    ],
    "avaliacao_desempenho": [
        "Principais conquistas do período.",
        "Áreas de desenvolvimento identificadas.",
        "Alinhamento com metas da equipe/empresa.",
        "Plano de desenvolvimento para o próximo ciclo.",
    ],
}


def get_template(name: str) -> list[str]:
    if name not in TEMPLATES:
        raise ValueError(f"Template '{name}' não encontrado. Opções: {', '.join(TEMPLATES)}")
    return TEMPLATES[name]


def render(name: str, title: str = "") -> str:
    questions = get_template(name)
    heading = title or name.replace("_", " ").title()
    lines = [f"# {heading}", ""]
    lines.extend(f"- {question}" for question in questions)
    return "\n".join(lines) + "\n"


def list_templates() -> list[str]:
    return sorted(TEMPLATES)
