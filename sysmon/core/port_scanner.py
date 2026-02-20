"""連接埠掃描模組（多執行緒）"""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


COMMON_PORTS: list[int] = [
    21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587,
    993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379,
    8080, 8443, 8888, 9200, 27017,
]

SERVICE_NAMES: dict[int, str] = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
    465: "SMTPS", 587: "SMTP(submission)", 993: "IMAPS", 995: "POP3S",
    1433: "MSSQL", 1521: "Oracle DB", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 8888: "Jupyter",
    9200: "Elasticsearch", 27017: "MongoDB",
}


def _scan_port(host: str, port: int, timeout: float) -> dict[str, Any]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {
                "port": port,
                "status": "open",
                "service": SERVICE_NAMES.get(port, socket.getservbyport(port, "tcp") if _has_service(port) else "unknown"),
            }
    except (ConnectionRefusedError, socket.timeout, OSError):
        return {"port": port, "status": "closed", "service": SERVICE_NAMES.get(port, "")}


def _has_service(port: int) -> bool:
    try:
        socket.getservbyport(port, "tcp")
        return True
    except OSError:
        return False


def scan_ports(
    host: str,
    ports: list[int] | None = None,
    preset: str = "common",
    timeout: float = 1.0,
    max_workers: int = 100,
) -> dict[str, Any]:
    """
    掃描指定主機的連接埠。

    Args:
        host: 目標主機名稱或 IP
        ports: 自訂連接埠列表（覆蓋 preset）
        preset: "common"（預設常見埠）或 "all"（1-1024）
        timeout: 每個連接埠的逾時秒數
        max_workers: 最大並發執行緒數
    """
    if ports:
        target_ports = ports[:1000]  # 最多 1000 個
    elif preset == "all":
        target_ports = list(range(1, 1025))
    else:
        target_ports = COMMON_PORTS

    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_scan_port, host, p, timeout): p for p in target_ports}
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda x: x["port"])
    open_ports = [r for r in results if r["status"] == "open"]

    return {
        "host": host,
        "total_scanned": len(results),
        "open_count": len(open_ports),
        "results": results,
        "open_ports": open_ports,
    }
