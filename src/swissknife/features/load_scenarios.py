from __future__ import annotations

import json
from pathlib import Path


LOCUST_TEMPLATE = '''from locust import HttpUser, between, task

class GeneratedUser(HttpUser):
    wait_time = between({wait_min}, {wait_max})

{tasks}
'''


def generate(spec_path: str | Path, output: str | Path) -> str:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    tasks = []
    for index, endpoint in enumerate(spec["endpoints"], 1):
        method = endpoint.get("method", "GET").lower()
        weight = endpoint.get("weight", 1)
        tasks.append(
            f'    @task({weight})\n    def endpoint_{index}(self):\n'
            f'        self.client.{method}({endpoint["path"]!r}, name={endpoint.get("name", endpoint["path"])!r})\n'
        )
    content = LOCUST_TEMPLATE.format(
        wait_min=spec.get("wait_min", 1), wait_max=spec.get("wait_max", 3), tasks="\n".join(tasks)
    )
    Path(output).write_text(content, encoding="utf-8")
    return content
