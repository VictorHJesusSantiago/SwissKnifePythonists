from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any


class Honeypot:
    def __init__(self, host: str = "127.0.0.1", ports: list[int] | None = None):
        self.host = host
        self.ports = ports or [2222, 8081]
        self.events: list[dict[str, Any]] = []
        self._hits: defaultdict[str, int] = defaultdict(int)

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        ip = str(peer[0]) if peer else "unknown"
        self._hits[ip] += 1
        data = await reader.read(1024)
        self.events.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "source": ip,
                "bytes": len(data),
                "hits": self._hits[ip],
            }
        )
        writer.write(b"Service unavailable\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def serve(self) -> None:
        servers = [await asyncio.start_server(self._handle, self.host, port) for port in self.ports]
        await asyncio.gather(*(server.serve_forever() for server in servers))
