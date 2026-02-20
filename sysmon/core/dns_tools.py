"""DNS 解析模組"""

from __future__ import annotations

import dns.resolver
import dns.reversename
import dns.exception
from typing import Any


RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "PTR", "SOA", "SRV", "CAA"]

DNS_SERVERS = {
    "Google (8.8.8.8)": "8.8.8.8",
    "Cloudflare (1.1.1.1)": "1.1.1.1",
    "OpenDNS (208.67.222.222)": "208.67.222.222",
    "系統預設": None,
}


def _make_resolver(dns_server: str | None = None) -> dns.resolver.Resolver:
    resolver = dns.resolver.Resolver()
    if dns_server:
        resolver.nameservers = [dns_server]
    resolver.timeout = 5
    resolver.lifetime = 10
    return resolver


def query_dns(domain: str, record_type: str = "A", dns_server: str | None = None) -> dict[str, Any]:
    """查詢單一 DNS 記錄"""
    resolver = _make_resolver(dns_server)
    results: list[str] = []
    error: str | None = None

    try:
        if record_type == "PTR":
            rev = dns.reversename.from_address(domain)
            answers = resolver.resolve(rev, "PTR")
        else:
            answers = resolver.resolve(domain, record_type)

        for rdata in answers:
            if record_type == "MX":
                results.append(f"{rdata.preference} {rdata.exchange}")
            elif record_type == "SOA":
                results.append(
                    f"mname={rdata.mname} rname={rdata.rname} "
                    f"serial={rdata.serial} refresh={rdata.refresh} "
                    f"retry={rdata.retry} expire={rdata.expire} minimum={rdata.minimum}"
                )
            elif record_type == "SRV":
                results.append(f"{rdata.priority} {rdata.weight} {rdata.port} {rdata.target}")
            elif record_type == "CAA":
                results.append(f"{rdata.flags} {rdata.tag.decode()} {rdata.value.decode()}")
            elif record_type == "TXT":
                results.append(b"".join(rdata.strings).decode(errors="replace"))
            else:
                results.append(str(rdata))
    except dns.resolver.NXDOMAIN:
        error = f"域名不存在：{domain}"
    except dns.resolver.NoAnswer:
        error = f"無 {record_type} 記錄"
    except dns.resolver.Timeout:
        error = "查詢超時"
    except dns.exception.DNSException as e:
        error = str(e)
    except Exception as e:
        error = f"查詢失敗：{e}"

    return {
        "domain": domain,
        "type": record_type,
        "records": results,
        "error": error,
        "dns_server": dns_server or "系統預設",
    }


def query_all_types(domain: str, dns_server: str | None = None) -> dict[str, Any]:
    """查詢所有 DNS 記錄類型"""
    results = {}
    for rtype in RECORD_TYPES:
        results[rtype] = query_dns(domain, rtype, dns_server)
    return results


def bulk_query(domains: list[str], record_type: str = "A", dns_server: str | None = None) -> list[dict[str, Any]]:
    """批次查詢多個域名"""
    return [query_dns(d.strip(), record_type, dns_server) for d in domains if d.strip()]
