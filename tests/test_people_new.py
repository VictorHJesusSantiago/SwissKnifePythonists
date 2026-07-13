from pathlib import Path

from swissknife.features.feedback_templates import get_template, list_templates, render
from swissknife.features.onboarding_tracker import complete_item, start, status
from swissknife.features.skills_matrix import SkillEntry, bus_factor, find_gaps


def test_skills_matrix() -> None:
    entries = [
        SkillEntry("Ana", "Python", 5),
        SkillEntry("Ana", "Kubernetes", 2),
        SkillEntry("Bruno", "Python", 4),
    ]
    gaps = find_gaps(entries, ["Python", "Kubernetes"], min_level=3)
    assert gaps["Ana"] == ["Kubernetes"]
    assert gaps["Bruno"] == ["Kubernetes"]
    assert bus_factor(entries, min_level=4)["Python"] == 2


def test_onboarding_tracker(tmp_path: Path) -> None:
    database = tmp_path / "onboarding.json"
    start(database, "Carla", checklist=["Conta criada", "Equipamento entregue"])
    complete_item(database, "Carla", "Conta criada")
    result = status(database, "Carla")
    assert result["progress_percent"] == 50.0


def test_feedback_templates() -> None:
    assert "1:1" in list_templates()
    questions = get_template("1:1")
    assert len(questions) > 0
    assert "1:1" in render("1:1")
