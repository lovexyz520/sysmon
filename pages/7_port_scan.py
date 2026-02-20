"""連接埠掃描頁面 - 常見/自訂連接埠掃描"""

import streamlit as st
import pandas as pd
from sysmon.core.port_scanner import scan_ports, COMMON_PORTS, SERVICE_NAMES

st.title("🔌 連接埠掃描")
st.markdown("掃描目標主機開放的 TCP 連接埠，識別執行中的服務。")

st.warning("⚠️ 請僅對您有權限掃描的主機執行此操作。未經授權的連接埠掃描可能違反法規。")

# ── 輸入區 ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    host = st.text_input(
        "目標主機",
        placeholder="192.168.1.1 或 example.com",
        label_visibility="collapsed",
    )
with col2:
    scan_btn = st.button("🔍 開始掃描", type="primary", use_container_width=True)

col1, col2, col3 = st.columns(3)
with col1:
    preset = st.selectbox(
        "掃描方案",
        ["常見連接埠", "1-1024 全掃描", "自訂連接埠"],
        key="port_preset",
    )
with col2:
    timeout = st.slider("逾時（秒）", 0.1, 3.0, 1.0, 0.1)
with col3:
    max_workers = st.slider("並發執行緒", 10, 200, 100)

custom_ports_str = ""
if preset == "自訂連接埠":
    custom_ports_str = st.text_input(
        "自訂連接埠（逗號分隔，最多 1000 個）",
        placeholder="80,443,8080,8443,3000,5000",
    )

if scan_btn and host:
    # 解析連接埠
    ports_list = None
    preset_key = "common"

    if preset == "自訂連接埠" and custom_ports_str:
        try:
            ports_list = [int(p.strip()) for p in custom_ports_str.split(",") if p.strip().isdigit()]
            if not ports_list:
                st.error("請輸入有效的連接埠號碼")
                st.stop()
        except ValueError:
            st.error("連接埠格式錯誤")
            st.stop()
    elif preset == "1-1024 全掃描":
        preset_key = "all"

    with st.spinner(f"正在掃描 {host}..."):
        result = scan_ports(
            host.strip(),
            ports=ports_list,
            preset=preset_key,
            timeout=timeout,
            max_workers=max_workers,
        )

    # 摘要指標
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("目標主機", result["host"])
    col2.metric("掃描連接埠數", result["total_scanned"])
    col3.metric("🟢 開放連接埠", result["open_count"])
    col4.metric("🔴 關閉連接埠", result["total_scanned"] - result["open_count"])

    # 開放連接埠摘要
    if result["open_ports"]:
        st.markdown("#### 🟢 開放的連接埠")
        open_df = pd.DataFrame(result["open_ports"])
        open_df.columns = ["連接埠", "狀態", "服務"]
        open_df["狀態"] = open_df["狀態"].map({"open": "🟢 開放", "closed": "🔴 關閉"})
        st.dataframe(open_df, use_container_width=True, hide_index=True)
    else:
        st.info("未發現開放的連接埠")

    # 完整結果
    with st.expander(f"📊 完整掃描結果（{result['total_scanned']} 個連接埠）"):
        all_df = pd.DataFrame(result["results"])
        all_df.columns = ["連接埠", "狀態", "服務"]
        all_df["狀態"] = all_df["狀態"].map({"open": "🟢 開放", "closed": "🔴 關閉"})
        st.dataframe(all_df, use_container_width=True, hide_index=True)

# ── 常見連接埠參考 ─────────────────────────────────────────────────────────────
with st.expander("📖 常見連接埠參考"):
    ref_data = [{"連接埠": port, "服務": name} for port, name in SERVICE_NAMES.items()]
    st.dataframe(pd.DataFrame(ref_data), use_container_width=True, hide_index=True)
