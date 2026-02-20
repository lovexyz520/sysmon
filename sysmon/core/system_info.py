"""系統規格查詢模組 (psutil)"""

from __future__ import annotations

import platform
import socket
from datetime import datetime, timezone
from typing import Any

import psutil


def get_cpu_info() -> dict[str, Any]:
    """取得 CPU 資訊"""
    freq = psutil.cpu_freq()
    return {
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "current_freq_mhz": round(freq.current, 1) if freq else None,
        "max_freq_mhz": round(freq.max, 1) if freq else None,
        "usage_percent": psutil.cpu_percent(interval=0.5),
        "per_core_usage": psutil.cpu_percent(interval=0.5, percpu=True),
        "architecture": platform.machine(),
        "processor": platform.processor() or "未知",
    }


def get_memory_info() -> dict[str, Any]:
    """取得記憶體資訊"""
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()

    def _fmt(bytes_val: int) -> str:
        gb = bytes_val / (1024 ** 3)
        return f"{gb:.2f} GB"

    return {
        "total": _fmt(vm.total),
        "available": _fmt(vm.available),
        "used": _fmt(vm.used),
        "percent": vm.percent,
        "swap_total": _fmt(swap.total),
        "swap_used": _fmt(swap.used),
        "swap_percent": swap.percent,
        "total_bytes": vm.total,
        "used_bytes": vm.used,
        "available_bytes": vm.available,
    }


def get_disk_info() -> list[dict[str, Any]]:
    """取得所有磁碟分割區資訊"""
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "percent": usage.percent,
            })
        except PermissionError:
            continue
    return disks


def get_network_interfaces() -> list[dict[str, Any]]:
    """取得網路介面資訊"""
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    io = psutil.net_io_counters(pernic=True)

    interfaces = []
    for name, addr_list in addrs.items():
        ipv4 = ""
        ipv6 = ""
        mac = ""
        for addr in addr_list:
            if addr.family == 2:   # AF_INET
                ipv4 = addr.address
            elif addr.family == 23 or addr.family == 10:  # AF_INET6
                ipv6 = addr.address.split("%")[0]
            elif addr.family == -1 or addr.family == 18:  # AF_LINK / AF_PACKET
                mac = addr.address

        stat = stats.get(name)
        nic_io = io.get(name)

        interfaces.append({
            "name": name,
            "ipv4": ipv4,
            "ipv6": ipv6,
            "mac": mac,
            "is_up": stat.isup if stat else False,
            "speed_mbps": stat.speed if stat else 0,
            "bytes_sent_mb": round(nic_io.bytes_sent / (1024 ** 2), 2) if nic_io else 0,
            "bytes_recv_mb": round(nic_io.bytes_recv / (1024 ** 2), 2) if nic_io else 0,
        })
    return interfaces


def get_os_info() -> dict[str, Any]:
    """取得作業系統資訊"""
    boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
    now = datetime.now(timezone.utc)
    uptime_seconds = int((now - boot_time).total_seconds())
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return {
        "os_name": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "hostname": socket.gethostname(),
        "architecture": platform.architecture()[0],
        "python_version": platform.python_version(),
        "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "uptime": f"{hours}h {minutes}m {seconds}s",
    }


def get_all_system_info() -> dict[str, Any]:
    """取得所有系統資訊"""
    return {
        "os": get_os_info(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disks": get_disk_info(),
        "network_interfaces": get_network_interfaces(),
    }
