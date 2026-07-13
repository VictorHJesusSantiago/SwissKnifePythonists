from __future__ import annotations

import ctypes
import os
import shutil
import sys
from dataclasses import dataclass

from swissknife.core.models import Result, Status


@dataclass(slots=True)
class Thresholds:
    disk_percent: float = 90.0
    memory_percent: float = 90.0
    load_per_cpu: float = 1.5


def disk_usage(path: str = ".") -> dict[str, float]:
    total, used, free = shutil.disk_usage(path)
    return {
        "total_gb": round(total / (1024**3), 2),
        "used_gb": round(used / (1024**3), 2),
        "free_gb": round(free / (1024**3), 2),
        "used_percent": round((used / total) * 100, 2),
    }


def memory_usage() -> dict[str, float]:
    if sys.platform.startswith("win"):
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(MemoryStatusEx)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))  # type: ignore[attr-defined]
        total = status.ullTotalPhys
        avail = status.ullAvailPhys
        used_percent = float(status.dwMemoryLoad)
    else:
        info: dict[str, int] = {}
        try:
            with open("/proc/meminfo", encoding="utf-8") as stream:
                for line in stream:
                    key, _, value = line.partition(":")
                    info[key.strip()] = int(value.strip().split()[0]) * 1024
        except FileNotFoundError:
            return {"total_gb": 0.0, "available_gb": 0.0, "used_percent": 0.0}
        total = info.get("MemTotal", 0)
        avail = info.get("MemAvailable", info.get("MemFree", 0))
        used_percent = round(((total - avail) / total) * 100, 2) if total else 0.0
    return {
        "total_gb": round(total / (1024**3), 2),
        "available_gb": round(avail / (1024**3), 2),
        "used_percent": round(used_percent, 2),
    }


def load_average() -> dict[str, float | None]:
    cpu_count = os.cpu_count() or 1
    try:
        load1, load5, load15 = os.getloadavg()
    except (AttributeError, OSError):
        return {"load1": None, "load5": None, "load15": None, "per_cpu": None, "cpu_count": cpu_count}
    return {
        "load1": round(load1, 2),
        "load5": round(load5, 2),
        "load15": round(load15, 2),
        "per_cpu": round(load1 / cpu_count, 2),
        "cpu_count": cpu_count,
    }


def check(path: str = ".", thresholds: Thresholds | None = None) -> Result:
    thresholds = thresholds or Thresholds()
    disk = disk_usage(path)
    memory = memory_usage()
    load = load_average()
    metrics: dict[str, float | int | str] = {
        "disk_used_percent": disk["used_percent"],
        "memory_used_percent": memory["used_percent"],
    }
    if load["per_cpu"] is not None:
        metrics["load_per_cpu"] = load["per_cpu"]
    status = Status.OK
    reasons: list[str] = []
    if disk["used_percent"] >= thresholds.disk_percent:
        status = Status.CRITICAL
        reasons.append(f"disco em {disk['used_percent']}%")
    if memory["used_percent"] >= thresholds.memory_percent:
        status = Status.CRITICAL
        reasons.append(f"memória em {memory['used_percent']}%")
    if load["per_cpu"] is not None and load["per_cpu"] >= thresholds.load_per_cpu:
        status = Status.WARNING if status == Status.OK else status
        reasons.append(f"carga por CPU em {load['per_cpu']}")
    message = "; ".join(reasons) if reasons else "Recursos dentro dos limites"
    return Result("recursos-locais", status, message, metrics, details={"disk": disk, "memory": memory, "load": load})
