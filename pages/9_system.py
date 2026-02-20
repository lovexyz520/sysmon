"""系統資訊頁面 - 本機 CPU/RAM/磁碟（本機限定）"""

import os
import streamlit as st
import pandas as pd

# 雲端部署偵測
IS_CLOUD = bool(
    os.environ.get("STREAMLIT_SHARING_MODE")
    or os.environ.get("IS_STREAMLIT_CLOUD")
    or os.environ.get("STREAMLIT_SERVER_HEADLESS")
)

st.title("💻 系統資訊")

if IS_CLOUD:
    st.warning(
        "⚠️ **此功能需在本機執行**\n\n"
        "系統資訊頁面需要直接存取本機硬體，無法在 Streamlit Cloud 上使用。\n\n"
        "請在本機執行以下指令：\n"
        "```bash\n"
        "uv run sysmon system\n"
        "# 或啟動本機 Web 版：\n"
        "uv run sysmon serve\n"
        "```"
    )
    st.stop()

from sysmon.core.system_info import (
    get_os_info, get_cpu_info, get_memory_info,
    get_disk_info, get_network_interfaces,
)
import plotly.graph_objects as go

st.markdown("顯示本機 CPU、RAM、磁碟、網路介面及作業系統資訊。")

# ── 作業系統 ───────────────────────────────────────────────────────────────────
with st.spinner("讀取系統資訊..."):
    os_info = get_os_info()
    cpu_info = get_cpu_info()
    mem_info = get_memory_info()
    disks = get_disk_info()
    nets = get_network_interfaces()

st.markdown("### 🖥️ 作業系統")
col1, col2, col3, col4 = st.columns(4)
col1.metric("系統", os_info.get("os_name", ""))
col2.metric("版本", os_info.get("os_release", ""))
col3.metric("主機名稱", os_info.get("hostname", ""))
col4.metric("開機時間", os_info.get("uptime", ""))
st.caption(f"OS 版本：{os_info.get('os_version', '')} | Python {os_info.get('python_version', '')} | 架構：{os_info.get('architecture', '')}")

st.divider()

# ── CPU ────────────────────────────────────────────────────────────────────────
st.markdown("### ⚡ CPU")
col1, col2, col3, col4 = st.columns(4)
col1.metric("實體核心", cpu_info.get("physical_cores", ""))
col2.metric("邏輯核心", cpu_info.get("logical_cores", ""))
col3.metric("當前頻率", f"{cpu_info.get('current_freq_mhz', 0)} MHz")
col4.metric("最大頻率", f"{cpu_info.get('max_freq_mhz', 0)} MHz")

st.caption(f"處理器：{cpu_info.get('processor', '')} | 架構：{cpu_info.get('architecture', '')}")

# CPU 使用率環形圖
cpu_usage = cpu_info.get("usage_percent", 0)
fig_cpu = go.Figure(go.Indicator(
    mode="gauge+number",
    value=cpu_usage,
    title={"text": "CPU 使用率 (%)"},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": "#00B4D8"},
        "steps": [
            {"range": [0, 50], "color": "#1A2744"},
            {"range": [50, 80], "color": "#2D4A7A"},
            {"range": [80, 100], "color": "#4A1A2D"},
        ],
        "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 90},
    }
))
fig_cpu.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)", font_color="#E0E6ED")

# 每核使用率
per_core = cpu_info.get("per_core_usage", [])
fig_cores = go.Figure(go.Bar(
    x=[f"核心 {i}" for i in range(len(per_core))],
    y=per_core,
    marker_color="#00B4D8",
))
fig_cores.update_layout(
    title="每核心使用率 (%)",
    height=200,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#E0E6ED",
    yaxis={"range": [0, 100]},
)

col1, col2 = st.columns([1, 2])
with col1:
    st.plotly_chart(fig_cpu, use_container_width=True)
with col2:
    st.plotly_chart(fig_cores, use_container_width=True)

st.divider()

# ── RAM ────────────────────────────────────────────────────────────────────────
st.markdown("### 💾 記憶體")
col1, col2, col3, col4 = st.columns(4)
col1.metric("總量", mem_info.get("total", ""))
col2.metric("已使用", mem_info.get("used", ""))
col3.metric("可用", mem_info.get("available", ""))
col4.metric("使用率", f"{mem_info.get('percent', 0):.1f}%")

# 環形圖
used_bytes = mem_info.get("used_bytes", 0)
avail_bytes = mem_info.get("available_bytes", 0)
fig_mem = go.Figure(go.Pie(
    labels=["已使用", "可用"],
    values=[used_bytes, avail_bytes],
    hole=0.6,
    marker_colors=["#00B4D8", "#1A2744"],
))
fig_mem.update_layout(
    height=250,
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#E0E6ED",
    showlegend=True,
)
col1, col2 = st.columns([1, 2])
with col1:
    st.plotly_chart(fig_mem, use_container_width=True)
with col2:
    swap_data = {
        "Swap 總量": mem_info.get("swap_total", ""),
        "Swap 已用": mem_info.get("swap_used", ""),
        "Swap 使用率": f"{mem_info.get('swap_percent', 0):.1f}%",
    }
    st.markdown("#### Swap 記憶體")
    st.dataframe(
        pd.DataFrame(list(swap_data.items()), columns=["項目", "值"]),
        use_container_width=True, hide_index=True
    )

st.divider()

# ── 磁碟 ───────────────────────────────────────────────────────────────────────
st.markdown("### 💿 磁碟")
if disks:
    disk_rows = []
    for d in disks:
        disk_rows.append({
            "裝置": d.get("device", ""),
            "掛載點": d.get("mountpoint", ""),
            "檔案系統": d.get("fstype", ""),
            "總量 (GB)": d.get("total_gb", 0),
            "已用 (GB)": d.get("used_gb", 0),
            "剩餘 (GB)": d.get("free_gb", 0),
            "使用率 (%)": d.get("percent", 0),
        })
    st.dataframe(pd.DataFrame(disk_rows), use_container_width=True, hide_index=True)

    # 磁碟使用率圖
    for d in disks:
        st.progress(
            d.get("percent", 0) / 100,
            text=f"{d.get('mountpoint', '')} — {d.get('used_gb', 0):.1f} / {d.get('total_gb', 0):.1f} GB ({d.get('percent', 0):.1f}%)",
        )

st.divider()

# ── 網路介面 ───────────────────────────────────────────────────────────────────
st.markdown("### 🌐 網路介面")
if nets:
    net_rows = []
    for n in nets:
        if not n.get("ipv4") and not n.get("mac"):
            continue
        net_rows.append({
            "介面": n.get("name", ""),
            "IPv4": n.get("ipv4", ""),
            "IPv6": n.get("ipv6", "")[:30] + "..." if len(n.get("ipv6", "")) > 30 else n.get("ipv6", ""),
            "MAC": n.get("mac", ""),
            "狀態": "🟢 啟用" if n.get("is_up") else "🔴 停用",
            "速度 (Mbps)": n.get("speed_mbps", 0),
            "上傳 (MB)": n.get("bytes_sent_mb", 0),
            "下載 (MB)": n.get("bytes_recv_mb", 0),
        })
    st.dataframe(pd.DataFrame(net_rows), use_container_width=True, hide_index=True)
