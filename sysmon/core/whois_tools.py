"""WHOIS 查詢模組"""

from __future__ import annotations

import ipaddress
from typing import Any

import whois
from ipwhois import IPWhois


def _is_ip(target: str) -> bool:
    try:
        ipaddress.ip_address(target)
        return True
    except ValueError:
        return False


def query_domain_whois(domain: str) -> dict[str, Any]:
    """查詢域名 WHOIS"""
    try:
        w = whois.whois(domain)
        result: dict[str, Any] = {
            "type": "domain",
            "domain": domain,
            "registrar": w.registrar,
            "creation_date": w.creation_date,
            "expiration_date": w.expiration_date,
            "updated_date": w.updated_date,
            "name_servers": w.name_servers,
            "status": w.status,
            "emails": w.emails,
            "org": w.org,
            "country": w.country,
            "raw": str(w),
        }
        # 統一日期為字串
        for key in ("creation_date", "expiration_date", "updated_date"):
            val = result[key]
            if isinstance(val, list):
                result[key] = val[0].strftime("%Y-%m-%d") if val else None
            elif val is not None:
                try:
                    result[key] = val.strftime("%Y-%m-%d")
                except Exception:
                    result[key] = str(val)
        return result
    except Exception as e:
        return {"type": "domain", "domain": domain, "error": str(e)}


def query_ip_whois(ip: str) -> dict[str, Any]:
    """查詢 IP WHOIS（使用 ipwhois）"""
    try:
        obj = IPWhois(ip)
        res = obj.lookup_rdap(depth=1)
        network = res.get("network", {})
        return {
            "type": "ip",
            "ip": ip,
            "asn": res.get("asn"),
            "asn_description": res.get("asn_description"),
            "asn_country_code": res.get("asn_country_code"),
            "asn_cidr": res.get("asn_cidr"),
            "network_name": network.get("name"),
            "network_cidr": network.get("cidr"),
            "network_country": network.get("country"),
            "network_start": network.get("start_address"),
            "network_end": network.get("end_address"),
            "entities": [e.get("handle") for e in res.get("entities", [])],
        }
    except Exception as e:
        return {"type": "ip", "ip": ip, "error": str(e)}


def query_whois(target: str) -> dict[str, Any]:
    """自動判斷 IP 或域名並查詢 WHOIS"""
    target = target.strip()
    if _is_ip(target):
        return query_ip_whois(target)
    return query_domain_whois(target)
