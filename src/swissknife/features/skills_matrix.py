from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SkillEntry:
    person: str
    skill: str
    level: int  # 1-5


def build_matrix(entries: list[SkillEntry]) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = {}
    for entry in entries:
        matrix.setdefault(entry.person, {})[entry.skill] = entry.level
    return matrix


def find_gaps(entries: list[SkillEntry], required_skills: list[str], min_level: int = 3) -> dict[str, list[str]]:
    matrix = build_matrix(entries)
    gaps: dict[str, list[str]] = {}
    for person, skills in matrix.items():
        missing = [skill for skill in required_skills if skills.get(skill, 0) < min_level]
        if missing:
            gaps[person] = missing
    return gaps


def bus_factor(entries: list[SkillEntry], min_level: int = 4) -> dict[str, int]:
    coverage: dict[str, int] = {}
    for entry in entries:
        if entry.level >= min_level:
            coverage[entry.skill] = coverage.get(entry.skill, 0) + 1
    return coverage


def to_markdown(entries: list[SkillEntry]) -> str:
    matrix = build_matrix(entries)
    skills = sorted({entry.skill for entry in entries})
    lines = ["| Pessoa | " + " | ".join(skills) + " |", "| --- | " + " | ".join("---" for _ in skills) + " |"]
    for person, skill_levels in matrix.items():
        row = [str(skill_levels.get(skill, "-")) for skill in skills]
        lines.append(f"| {person} | " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"
