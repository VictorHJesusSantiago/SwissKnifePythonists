from pathlib import Path

from swissknife.features.arch_diagram import build_dependency_graph, to_mermaid
from swissknife.features.changelog import Commit
from swissknife.features.code_metrics import analyze_tree
from swissknife.features.duplicate_code import find_duplicates
from swissknife.features.naming_lint import lint_tree
from swissknife.features.semantic_changelog import next_version
from swissknife.features.test_skeleton_generator import generate


def test_semantic_changelog() -> None:
    commits = [Commit("a", "feat: novo endpoint"), Commit("b", "fix: corrige bug")]
    bump = next_version("1.2.3", commits)
    assert bump.next == "1.3.0"
    assert bump.bump == "minor"


def test_code_metrics(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text("def foo():\n    return 1\n\n\ndef bar():\n    return 2\n", encoding="utf-8")
    result = analyze_tree(tmp_path)
    assert result["file_count"] == 1
    assert result["files"][0]["functions"] == 2


def test_duplicate_code(tmp_path: Path) -> None:
    block = "\n".join(f"x{i} = {i}" for i in range(8))
    (tmp_path / "a.py").write_text(block, encoding="utf-8")
    (tmp_path / "b.py").write_text(block, encoding="utf-8")
    result = find_duplicates(tmp_path, min_lines=6)
    assert result["duplicate_blocks"] >= 1


def test_test_skeleton_generator(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    package = source_root / "pkg"
    package.mkdir(parents=True)
    (package / "mod.py").write_text("def somar(a, b):\n    return a + b\n", encoding="utf-8")
    content = generate(package / "mod.py", source_root)
    assert "somar" in content
    assert "def test_somar" in content


def test_naming_lint(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text("def MinhaFuncao():\n    pass\n\n\nclass minha_classe:\n    pass\n", encoding="utf-8")
    result = lint_tree(tmp_path)
    assert result["violation_count"] >= 2


def test_arch_diagram(tmp_path: Path) -> None:
    package = tmp_path / "pkgroot"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "a.py").write_text("from pkgroot import b\n", encoding="utf-8")
    (package / "b.py").write_text("", encoding="utf-8")
    graph = build_dependency_graph(tmp_path)
    assert "pkgroot.b" in graph.get("pkgroot.a", [])
    assert "graph LR" in to_mermaid(graph)
