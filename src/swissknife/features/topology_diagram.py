from __future__ import annotations

from typing import Any


def to_mermaid(assets: list[dict[str, Any]], network_label: str = "Rede") -> str:
    lines = ["graph TD", f'  NET["{network_label}"]']
    for asset in assets:
        node_id = "n" + asset["ip"].replace(".", "_")
        label = asset.get("hostname") or asset["ip"]
        lines.append(f'  NET --> {node_id}["{label}\\n{asset["ip"]}"]')
        for port in asset.get("open_ports", []):
            port_id = f"{node_id}_p{port}"
            lines.append(f'  {node_id} --> {port_id}(("porta {port}"))')
    return "\n".join(lines) + "\n"


def to_dot(assets: list[dict[str, Any]], network_label: str = "Rede") -> str:
    lines = ["digraph topology {", f'  net [label="{network_label}"];']
    for asset in assets:
        node_id = "n" + asset["ip"].replace(".", "_")
        label = asset.get("hostname") or asset["ip"]
        lines.append(f'  {node_id} [label="{label}\\n{asset["ip"]}"];')
        lines.append(f"  net -> {node_id};")
        for port in asset.get("open_ports", []):
            port_id = f"{node_id}_p{port}"
            lines.append(f'  {port_id} [label="porta {port}", shape=circle];')
            lines.append(f"  {node_id} -> {port_id};")
    lines.append("}")
    return "\n".join(lines) + "\n"
