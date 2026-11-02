"""Actual host telemetry; unavailable readings are None, never simulated.

This host may be a Linux development machine rather than the user's Mac.
The Darwin path uses only fixed native command arguments and never asks for
accessibility, microphone, or other permissions.
"""
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

_sample_lock = threading.Lock()
_previous_cpu = None


def _command(args: list[str]) -> str | None:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=3,
                              check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _linux_metrics() -> dict:
    global _previous_cpu
    result = {}
    try:
        line = Path("/proc/stat").read_text().splitlines()[0]
        values = [int(value) for value in line.split()[1:]]
        # guest/guest_nice are included in user/nice; count first eight fields.
        total, idle = sum(values[:8]), values[3] + values[4]
        with _sample_lock:
            previous, _previous_cpu = _previous_cpu, (total, idle)
        if previous and total > previous[0]:
            result["cpu_percent"] = round(100 * (1 - (idle-previous[1]) / (total-previous[0])), 1)
    except (OSError, ValueError, IndexError):
        pass
    try:
        memory = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            memory[key] = int(value.split()[0]) * 1024
        total = memory["MemTotal"]
        used = total - memory["MemAvailable"]
        result.update(memory_total_bytes=total, memory_used_bytes=used,
                      memory_percent=round(used/total * 100, 1))
    except (OSError, KeyError, ValueError):
        pass
    try:
        result["uptime_seconds"] = int(float(Path("/proc/uptime").read_text().split()[0]))
    except (OSError, ValueError, IndexError):
        pass
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith("model name"):
                result["cpu_name"] = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    # Container constraints are shown separately instead of silently presenting
    # host RAM or CPU counts as the resources available to the application.
    try:
        maximum = Path("/sys/fs/cgroup/memory.max").read_text().strip()
        current = Path("/sys/fs/cgroup/memory.current").read_text().strip()
        if maximum != "max":
            result["container_memory_limit_bytes"] = int(maximum)
            result["container_memory_used_bytes"] = int(current)
    except (OSError, ValueError):
        pass
    return result


def _mac_metrics() -> dict:
    result = {}
    name = _command(["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"])
    if name:
        result["cpu_name"] = name
    total_text = _command(["/usr/sbin/sysctl", "-n", "hw.memsize"])
    try:
        total = int(total_text) if total_text else None
        if total:
            result["memory_total_bytes"] = total
        pages_text = _command(["/usr/bin/vm_stat"])
        if total and pages_text:
            page_match = re.search(r"page size of (\d+) bytes", pages_text)
            if page_match:
                page_size = int(page_match.group(1))
                pages = {key.strip(): int(value) for key, value in
                         re.findall(r"^([^:\n]+):\s*(\d+)\.", pages_text, flags=re.M)}
                available = sum(pages.get(key, 0) for key in
                                ["Pages free", "Pages inactive", "Pages speculative"]) * page_size
                used = max(0, total - available)
                result.update(memory_used_bytes=used, memory_percent=round(used/total * 100, 1),
                              memory_measurement="estimated from vm_stat")
    except ValueError:
        pass
    boot = _command(["/usr/sbin/sysctl", "-n", "kern.boottime"])
    if boot:
        match = re.search(r"sec\s*=\s*(\d+)", boot)
        if match:
            result["uptime_seconds"] = max(0, int(time.time()-int(match.group(1))))
    # top reports a real instantaneous sample; using one bounded native call
    # avoids kernel/private APIs and any third-party dependency.
    top = _command(["/usr/bin/top", "-l", "1", "-n", "0"])
    if top:
        match = re.search(r"CPU usage:\s*([\d.]+)% user,\s*([\d.]+)% sys", top)
        if match:
            result["cpu_percent"] = round(float(match.group(1))+float(match.group(2)), 1)
    return result


def snapshot(data_dir: str | Path | None = None) -> dict:
    system = platform.system()
    result = {
        "platform": platform.platform(), "system": system,
        "release": platform.release(), "architecture": platform.machine(),
        "python_version": platform.python_version(), "hostname": platform.node(),
        "is_macos": system == "Darwin", "macos_version": platform.mac_ver()[0] or None,
        "cpu_name": platform.processor() or None, "cpu_count": os.cpu_count(),
        "cpu_percent": None, "load_average": None,
        "memory_total_bytes": None, "memory_used_bytes": None, "memory_percent": None,
        "disk_total_bytes": None, "disk_free_bytes": None, "disk_percent": None,
        "uptime_seconds": None,
    }
    try:
        result["load_average"] = list(os.getloadavg())
    except (AttributeError, OSError):
        pass
    if system == "Linux":
        result.update(_linux_metrics())
    elif system == "Darwin":
        result.update(_mac_metrics())
    disk_path = Path(data_dir) if data_dir else Path.home()
    try:
        disk = shutil.disk_usage(disk_path)
        result.update(disk_total_bytes=disk.total, disk_free_bytes=disk.free,
                      disk_percent=round(disk.used/disk.total * 100, 1))
    except OSError:
        pass
    result["machine"] = result["architecture"]
    result["python"] = result["python_version"]
    total, used = result["memory_total_bytes"], result["memory_used_bytes"]
    result["memory"] = {"total": total, "available": total-used if total is not None and used is not None else None,
                        "percent": result["memory_percent"]}
    result["disk"] = {"total": result["disk_total_bytes"], "free": result["disk_free_bytes"],
                      "percent": result["disk_percent"]}
    return result
