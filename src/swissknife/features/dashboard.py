from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from swissknife.core.config import load_mapping
from swissknife.features.health import HealthTarget, check_all


PAGE = """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>Health Dashboard</title>
<style>body{font:15px system-ui;background:#0d1117;color:#e6edf3;margin:2rem}
h1{color:#58a6ff}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}
.card{padding:1rem;border:1px solid #30363d;border-radius:10px;background:#161b22}
.ok{border-left:6px solid #3fb950}.warning{border-left:6px solid #d29922}
.critical{border-left:6px solid #f85149}small{color:#8b949e}</style>
<h1>SwissKnife · Health</h1><p id="updated"></p><div class="grid" id="grid"></div>
<script>async function refresh(){let r=await fetch('/api/health'),data=await r.json();
grid.innerHTML=data.map(x=>`<article class="card ${x.status}"><h2>${x.name}</h2>
<p>${x.message}</p><small>${JSON.stringify(x.metrics)}</small></article>`).join('');
updated.textContent='Atualizado em '+new Date().toLocaleString()}refresh();setInterval(refresh,30000)</script>"""


def targets_from_file(path: str | Path) -> list[HealthTarget]:
    config = load_mapping(path)
    return [HealthTarget(**item) for item in config.get("targets", [])]


def serve(config_path: str | Path, host: str = "127.0.0.1", port: int = 8090) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/api/health":
                payload = json.dumps(
                    [item.to_dict() for item in check_all(targets_from_file(config_path))],
                    ensure_ascii=False,
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
            elif self.path in {"/", "/index.html"}:
                payload = PAGE.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
            else:
                payload = b'{"error":"not found"}'
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            return

    ThreadingHTTPServer((host, port), Handler).serve_forever()
