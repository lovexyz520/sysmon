"""子網路計算模組"""

from __future__ import annotations

import ipaddress
from typing import Any


def calculate_subnet(cidr: str) -> dict[str, Any]:
    """
    計算 CIDR 子網路資訊。

    Args:
        cidr: CIDR 表示法，如 192.168.1.0/24 或 10.0.0.1/16

    Returns:
        包含子網路詳細資訊的字典
    """
    cidr = cidr.strip()
    try:
        # strict=False 允許輸入 192.168.1.1/24（非網路位址）
        network = ipaddress.ip_network(cidr, strict=False)
        input_ip = cidr.split("/")[0]

        hosts = list(network.hosts())
        host_count = len(hosts)

        result: dict[str, Any] = {
            "input": cidr,
            "input_ip": input_ip,
            "network_address": str(network.network_address),
            "broadcast_address": str(network.broadcast_address) if network.version == 4 else "N/A（IPv6）",
            "netmask": str(network.netmask) if network.version == 4 else str(network.prefixlen),
            "prefix_length": network.prefixlen,
            "version": f"IPv{network.version}",
            "total_addresses": network.num_addresses,
            "usable_hosts": host_count,
            "first_host": str(hosts[0]) if hosts else "N/A",
            "last_host": str(hosts[-1]) if hosts else "N/A",
            "is_private": network.is_private,
            "is_global": network.is_global,
            "is_multicast": network.is_multicast,
            "is_loopback": network.is_loopback,
            "compressed": network.compressed,
        }

        # 若為 /30 以上，列出所有主機（最多 256 個）
        if host_count <= 256:
            result["host_list"] = [str(h) for h in hosts]
        else:
            result["host_list"] = [str(h) for h in hosts[:10]] + ["..."] + [str(hosts[-1])]

        return result

    except ValueError as e:
        return {"input": cidr, "error": str(e)}


def split_subnet(cidr: str, new_prefix: int) -> dict[str, Any]:
    """將子網路分割為更小的子網路"""
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        if new_prefix <= network.prefixlen:
            return {"error": f"新前綴 /{new_prefix} 必須大於原前綴 /{network.prefixlen}"}
        subnets = list(network.subnets(new_prefix=new_prefix))
        return {
            "parent": str(network),
            "new_prefix": new_prefix,
            "count": len(subnets),
            "subnets": [str(s) for s in subnets[:64]],  # 最多顯示 64 個
            "truncated": len(subnets) > 64,
        }
    except ValueError as e:
        return {"error": str(e)}
