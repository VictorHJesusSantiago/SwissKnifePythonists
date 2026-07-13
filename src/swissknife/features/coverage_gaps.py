from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree


def parse_coverage_xml(path: str | Path) -> dict[str, object]:
    tree = ElementTree.parse(path)
    root = tree.getroot()
    files = []
    for class_element in root.iter("class"):
        filename = class_element.get("filename", "")
        lines = class_element.find("lines")
        if lines is None:
            continue
        total = 0
        covered = 0
        missing: list[int] = []
        for line in lines.findall("line"):
            total += 1
            hits = int(line.get("hits", "0"))
            if hits > 0:
                covered += 1
            else:
                missing.append(int(line.get("number", "0")))
        percent = round((covered / total) * 100, 2) if total else 100.0
        files.append({"filename": filename, "line_rate": percent, "missing_lines": missing})
    overall = float(root.get("line-rate", "0")) * 100
    return {"overall_percent": round(overall, 2), "files": files}


def find_gaps(coverage: dict[str, object], threshold: float = 80.0) -> list[dict[str, object]]:
    return [item for item in coverage["files"] if item["line_rate"] < threshold]  # type: ignore[index]
