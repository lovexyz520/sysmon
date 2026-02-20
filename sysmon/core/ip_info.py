"""IP 地理/ISP 查詢模組"""

from __future__ import annotations

import requests
from typing import Any


FREE_API_URL = "http://ip-api.com/json/{ip}"
FREE_API_FIELDS = (
    "status,message,country,countryCode,region,regionName,city,zip,"
    "lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query"
)
IPIFY_URL = "https://api.ipify.org?format=json"
IPINFO_URL = "https://ipinfo.io/{ip}/json"


def get_public_ip() -> str:
    """取得本機公網 IP"""
    try:
        resp = requests.get(IPIFY_URL, timeout=5)
        resp.raise_for_status()
        return resp.json().get("ip", "")
    except Exception:
        try:
            resp = requests.get("https://api4.my-ip.io/ip.json", timeout=5)
            return resp.json().get("ip", "未知")
        except Exception:
            return "未知"


def query_ip_free(ip: str) -> dict[str, Any]:
    """使用 ip-api.com 查詢 IP 資訊（免費，每分鐘 45 次）"""
    url = FREE_API_URL.format(ip=ip if ip else "")
    try:
        resp = requests.get(url, params={"fields": FREE_API_FIELDS, "lang": "zh-TW"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "fail":
            return {"error": data.get("message", "查詢失敗")}
        return data
    except requests.RequestException as e:
        return {"error": str(e)}


def query_ip_ipinfo(ip: str, token: str) -> dict[str, Any]:
    """使用 ipinfo.io 查詢（需要 Token）"""
    url = IPINFO_URL.format(ip=ip if ip else "")
    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def query_ip(ip: str = "", ipinfo_token: str = "") -> dict[str, Any]:
    """
    查詢 IP 資訊。
    若未提供 ip，自動偵測公網 IP。
    若提供 ipinfo_token，使用 ipinfo.io；否則使用 ip-api.com。
    """
    target_ip = ip.strip() if ip else get_public_ip()

    if ipinfo_token:
        raw = query_ip_ipinfo(target_ip, ipinfo_token)
        # 統一回傳格式
        if "error" not in raw:
            loc = raw.get("loc", "0,0").split(",")
            return {
                "query": raw.get("ip", target_ip),
                "country": raw.get("country", ""),
                "city": raw.get("city", ""),
                "regionName": raw.get("region", ""),
                "timezone": raw.get("timezone", ""),
                "isp": raw.get("org", ""),
                "org": raw.get("org", ""),
                "as": raw.get("org", ""),
                "lat": float(loc[0]) if len(loc) == 2 else 0.0,
                "lon": float(loc[1]) if len(loc) == 2 else 0.0,
                "proxy": False,
                "hosting": False,
                "mobile": False,
                "_source": "ipinfo.io",
                "_raw": raw,
            }
        return raw

    data = query_ip_free(target_ip)
    if "error" not in data:
        data["_source"] = "ip-api.com"
    return data


def format_ip_info(data: dict[str, Any]) -> dict[str, str]:
    """將查詢結果格式化為易讀的鍵值對"""
    if "error" in data:
        return {"錯誤": data["error"]}

    result = {
        "IP 位址": data.get("query", ""),
        "國家": data.get("country", ""),
        "城市": data.get("city", ""),
        "地區": data.get("regionName", ""),
        "時區": data.get("timezone", ""),
        "ISP": data.get("isp", ""),
        "組織": data.get("org", ""),
        "ASN": data.get("as", ""),
        "緯度": str(data.get("lat", "")),
        "經度": str(data.get("lon", "")),
        "代理/VPN": "是" if data.get("proxy") else "否",
        "資料中心": "是" if data.get("hosting") else "否",
        "行動網路": "是" if data.get("mobile") else "否",
        "資料來源": data.get("_source", "ip-api.com"),
    }
    return result
