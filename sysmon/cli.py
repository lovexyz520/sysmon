"""SysMon CLI 入口 (Typer + Rich)"""

from __future__ import annotations

import subprocess
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    name="sysmon",
    help="SysMon 系統查詢工具 - 網路/系統資訊查詢平台",
    rich_markup_mode="rich",
)
console = Console()


def _table(title: str, rows: dict) -> Table:
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("欄位", style="cyan", no_wrap=True)
    table.add_column("值", style="white")
    for key, val in rows.items():
        if val is None:
            val = ""
        table.add_row(str(key), str(val))
    return table


# ── ip ────────────────────────────────────────────────────────────────────────
@app.command()
def ip(
    address: Optional[str] = typer.Argument(None, help="IP 位址（留空自動偵測）"),
    token: str = typer.Option("", "--token", "-t", help="ipinfo.io Token（選填）"),
):
    """查詢 IP 地理位置、ISP、ASN 等資訊"""
    from sysmon.core.ip_info import query_ip, format_ip_info

    with console.status(f"查詢 {address or '公網 IP'}..."):
        data = query_ip(address or "", token)

    if "error" in data:
        console.print(f"[red]錯誤：{data['error']}[/red]")
        raise typer.Exit(1)

    formatted = format_ip_info(data)
    table = _table(f"IP 資訊 — {data.get('query', '')}", formatted)
    console.print(table)


# ── dns ────────────────────────────────────────────────────────────────────────
@app.command()
def dns(
    domain: str = typer.Argument(..., help="域名"),
    record_type: str = typer.Option("A", "--type", "-t", help="DNS 記錄類型"),
    server: Optional[str] = typer.Option(None, "--server", "-s", help="DNS 伺服器 IP"),
):
    """查詢 DNS 記錄"""
    from sysmon.core.dns_tools import query_dns

    record_type = record_type.upper()
    with console.status(f"查詢 {domain} 的 {record_type} 記錄..."):
        result = query_dns(domain, record_type, server)

    if result.get("error"):
        console.print(f"[yellow]⚠️  {result['error']}[/yellow]")
        return

    table = Table(title=f"DNS {record_type} — {domain}", show_header=True, header_style="bold cyan")
    table.add_column("記錄", style="white")
    for rec in result.get("records", []):
        table.add_row(rec)
    console.print(table)
    console.print(f"[dim]DNS 伺服器：{result.get('dns_server', '系統預設')}[/dim]")


# ── whois ────────────────────────────────────────────────────────────────────
@app.command()
def whois(
    target: str = typer.Argument(..., help="域名或 IP"),
):
    """查詢 WHOIS 資訊"""
    from sysmon.core.whois_tools import query_whois

    with console.status(f"查詢 {target} 的 WHOIS..."):
        result = query_whois(target)

    if "error" in result:
        console.print(f"[red]錯誤：{result['error']}[/red]")
        raise typer.Exit(1)

    if result.get("type") == "domain":
        rows = {
            "域名": result.get("domain", ""),
            "註冊商": result.get("registrar", ""),
            "建立日期": result.get("creation_date", ""),
            "到期日期": result.get("expiration_date", ""),
            "更新日期": result.get("updated_date", ""),
            "組織": result.get("org", ""),
            "國家": result.get("country", ""),
            "Name Servers": ", ".join(result.get("name_servers") or []),
        }
    else:
        rows = {
            "IP": result.get("ip", ""),
            "ASN": result.get("asn", ""),
            "ASN 說明": result.get("asn_description", ""),
            "ASN 國家": result.get("asn_country_code", ""),
            "CIDR": result.get("asn_cidr", ""),
            "網路名稱": result.get("network_name", ""),
            "網路範圍": result.get("network_cidr", ""),
        }
    console.print(_table(f"WHOIS — {target}", rows))


# ── ssl ────────────────────────────────────────────────────────────────────────
@app.command()
def ssl(
    hostname: str = typer.Argument(..., help="主機名稱（無需 https://）"),
    port: int = typer.Option(443, "--port", "-p", help="連接埠（預設 443）"),
):
    """查詢 SSL/TLS 憑證詳情"""
    from sysmon.core.ssl_tools import query_ssl

    with console.status(f"連線 {hostname}:{port} 取得憑證..."):
        result = query_ssl(hostname, port)

    if "error" in result:
        console.print(f"[red]錯誤：{result['error']}[/red]")
        raise typer.Exit(1)

    days = result.get("days_left", 0)
    if result.get("is_expired"):
        status_str = f"[red]❌ 已到期 {abs(days)} 天[/red]"
    elif result.get("is_expiring_soon"):
        status_str = f"[yellow]⚠️  即將到期，剩餘 {days} 天[/yellow]"
    else:
        status_str = f"[green]✅ 有效，剩餘 {days} 天[/green]"

    rows = {
        "主機": result.get("hostname", ""),
        "狀態": f"{days} 天",
        "到期日": result.get("not_after", "")[:10],
        "生效日": result.get("not_before", "")[:10],
        "主體 CN": result.get("subject", {}).get("CN", ""),
        "頒發者 O": result.get("issuer", {}).get("O", ""),
        "SAN 數量": len(result.get("san", [])),
        "序號": result.get("serial_number", "")[:16] + "...",
    }
    console.print(_table(f"SSL 憑證 — {hostname}", rows))
    console.print(status_str)

    san = result.get("san", [])
    if san:
        console.print(f"\n[cyan]SAN 清單：[/cyan]")
        for s in san[:10]:
            console.print(f"  • {s}")
        if len(san) > 10:
            console.print(f"  ... 共 {len(san)} 個")


# ── web ────────────────────────────────────────────────────────────────────────
@app.command()
def web(
    url: str = typer.Argument(..., help="目標 URL"),
    user_agent: str = typer.Option("", "--ua", help="自訂 User-Agent"),
    timeout: int = typer.Option(15, "--timeout", help="逾時秒數"),
):
    """HTTP 網站檢測：狀態碼、標頭、重定向鏈"""
    from sysmon.core.web_tools import check_website, DEFAULT_UA

    ua = user_agent or DEFAULT_UA
    with console.status(f"檢測 {url}..."):
        result = check_website(url, ua, timeout)

    if "error" in result:
        console.print(f"[red]錯誤：{result['error']}[/red]")
        raise typer.Exit(1)

    status = result.get("status_code", 0)
    color = "green" if 200 <= status < 300 else "yellow" if 300 <= status < 400 else "red"
    console.print(Panel(
        f"[{color}]{status} {result.get('status_text', '')}[/{color}]  "
        f"| {result.get('response_time_ms', 0):.0f} ms  "
        f"| {result.get('content_length', 0) / 1024:.1f} KB  "
        f"| Server: {result.get('server', 'N/A')}",
        title=f"🌐 {result.get('url', url)}",
    ))

    if result.get("title"):
        console.print(f"[dim]頁面標題：{result['title']}[/dim]")

    # 重定向鏈
    for r in result.get("redirect_chain", []):
        console.print(f"  [yellow]↳ {r['status_code']} {r['status_text']}[/yellow] → {r['url']}")

    # 重要標頭
    headers = result.get("headers", {})
    table = Table(title="HTTP 標頭", show_header=True, header_style="bold cyan")
    table.add_column("標頭", style="cyan")
    table.add_column("值", style="white", no_wrap=False)
    priority = ["content-type", "server", "x-powered-by", "strict-transport-security",
                "content-security-policy", "x-frame-options", "cache-control"]
    for h in priority:
        if h in headers:
            table.add_row(h, headers[h][:80])
    console.print(table)


# ── scan ────────────────────────────────────────────────────────────────────────
@app.command()
def scan(
    host: str = typer.Argument(..., help="目標主機"),
    preset: str = typer.Option("common", "--preset", help="掃描方案：common / all"),
    ports: str = typer.Option("", "--ports", help="自訂連接埠（逗號分隔）"),
    timeout: float = typer.Option(1.0, "--timeout", help="每埠逾時秒數"),
):
    """TCP 連接埠掃描"""
    from sysmon.core.port_scanner import scan_ports

    ports_list = None
    if ports:
        try:
            ports_list = [int(p.strip()) for p in ports.split(",") if p.strip().isdigit()]
        except ValueError:
            console.print("[red]連接埠格式錯誤[/red]")
            raise typer.Exit(1)

    console.print(f"[cyan]掃描 {host}...[/cyan]")
    with console.status("掃描中（可能需要一點時間）..."):
        result = scan_ports(host, ports_list, preset, timeout)

    console.print(f"掃描完成：{result['total_scanned']} 個連接埠，[green]{result['open_count']} 個開放[/green]")

    table = Table(title=f"開放的連接埠 — {host}", show_header=True, header_style="bold cyan")
    table.add_column("連接埠", style="cyan")
    table.add_column("服務", style="white")
    for p in result.get("open_ports", []):
        table.add_row(str(p["port"]), p.get("service", ""))
    console.print(table)


# ── subnet ────────────────────────────────────────────────────────────────────
@app.command()
def subnet(
    cidr: str = typer.Argument(..., help="CIDR 表示法，如 192.168.1.0/24"),
):
    """子網路 CIDR 計算"""
    from sysmon.core.subnet_calc import calculate_subnet

    result = calculate_subnet(cidr)
    if "error" in result:
        console.print(f"[red]錯誤：{result['error']}[/red]")
        raise typer.Exit(1)

    rows = {
        "CIDR": result.get("compressed", ""),
        "版本": result.get("version", ""),
        "網路位址": result.get("network_address", ""),
        "廣播位址": result.get("broadcast_address", ""),
        "子網路遮罩": result.get("netmask", ""),
        "前綴長度": f"/{result.get('prefix_length', '')}",
        "總位址數": f"{result.get('total_addresses', 0):,}",
        "可用主機數": f"{result.get('usable_hosts', 0):,}",
        "第一個主機": result.get("first_host", ""),
        "最後一個主機": result.get("last_host", ""),
        "私有網路": "是" if result.get("is_private") else "否",
    }
    console.print(_table(f"子網路計算 — {cidr}", rows))


# ── system ────────────────────────────────────────────────────────────────────
@app.command()
def system():
    """顯示本機系統資訊（OS、CPU、RAM、磁碟）"""
    from sysmon.core.system_info import get_all_system_info

    with console.status("讀取系統資訊..."):
        info = get_all_system_info()

    # OS
    os_i = info["os"]
    console.print(Panel(
        f"[cyan]{os_i['os_name']} {os_i['os_release']}[/cyan]  |  "
        f"主機：{os_i['hostname']}  |  上線：{os_i['uptime']}  |  "
        f"架構：{os_i['architecture']}",
        title="🖥️  作業系統",
    ))

    # CPU
    cpu = info["cpu"]
    cpu_rows = {
        "實體核心": cpu.get("physical_cores", ""),
        "邏輯核心": cpu.get("logical_cores", ""),
        "當前頻率": f"{cpu.get('current_freq_mhz', 0)} MHz",
        "最大頻率": f"{cpu.get('max_freq_mhz', 0)} MHz",
        "CPU 使用率": f"{cpu.get('usage_percent', 0):.1f}%",
        "處理器": cpu.get("processor", ""),
    }
    console.print(_table("⚡ CPU", cpu_rows))

    # RAM
    mem = info["memory"]
    mem_rows = {
        "總量": mem.get("total", ""),
        "已使用": mem.get("used", ""),
        "可用": mem.get("available", ""),
        "使用率": f"{mem.get('percent', 0):.1f}%",
        "Swap 總量": mem.get("swap_total", ""),
        "Swap 使用率": f"{mem.get('swap_percent', 0):.1f}%",
    }
    console.print(_table("💾 記憶體", mem_rows))

    # 磁碟
    disk_table = Table(title="💿 磁碟", show_header=True, header_style="bold cyan")
    disk_table.add_column("裝置", style="cyan")
    disk_table.add_column("掛載點")
    disk_table.add_column("總量 (GB)")
    disk_table.add_column("已用 (GB)")
    disk_table.add_column("使用率 %")
    for d in info["disks"]:
        disk_table.add_row(
            d.get("device", ""),
            d.get("mountpoint", ""),
            str(d.get("total_gb", 0)),
            str(d.get("used_gb", 0)),
            f"{d.get('percent', 0):.1f}%",
        )
    console.print(disk_table)


# ── network ────────────────────────────────────────────────────────────────────
@app.command()
def network():
    """顯示本機網路介面資訊"""
    from sysmon.core.system_info import get_network_interfaces

    with console.status("讀取網路介面..."):
        interfaces = get_network_interfaces()

    table = Table(title="🌐 網路介面", show_header=True, header_style="bold cyan")
    table.add_column("介面", style="cyan")
    table.add_column("IPv4")
    table.add_column("IPv6")
    table.add_column("MAC")
    table.add_column("狀態")
    table.add_column("速度 Mbps")
    table.add_column("上傳 MB")
    table.add_column("下載 MB")

    for n in interfaces:
        if not n.get("ipv4") and not n.get("mac"):
            continue
        table.add_row(
            n.get("name", ""),
            n.get("ipv4", ""),
            n.get("ipv6", "")[:20],
            n.get("mac", ""),
            "[green]啟用[/green]" if n.get("is_up") else "[red]停用[/red]",
            str(n.get("speed_mbps", 0)),
            str(n.get("bytes_sent_mb", 0)),
            str(n.get("bytes_recv_mb", 0)),
        )
    console.print(table)


# ── serve ────────────────────────────────────────────────────────────────────
@app.command()
def serve(
    port: int = typer.Option(8501, "--port", "-p", help="監聽連接埠"),
):
    """啟動 Streamlit Web 介面（本機）"""
    import os
    import pathlib

    # 找到 app.py 的位置（與此 CLI 模組同一專案根目錄）
    pkg_dir = pathlib.Path(__file__).parent.parent
    app_path = pkg_dir / "app.py"

    if not app_path.exists():
        console.print(f"[red]找不到 app.py：{app_path}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]啟動 SysMon Web 介面於 http://localhost:{port}[/cyan]")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path), f"--server.port={port}"],
        check=False,
    )


if __name__ == "__main__":
    app()
