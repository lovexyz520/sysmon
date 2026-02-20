"""SysMon 系統查詢工具 - Streamlit 主入口"""

import streamlit as st

st.set_page_config(
    page_title="SysMon 系統查詢",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 側邊欄 API Key 設定 ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🖥️ SysMon")
    st.markdown("系統與網路資訊查詢平台")
    st.divider()

    st.markdown("### 🔑 API Key 設定（選填）")
    st.caption("輸入 API Key 解鎖進階功能")

    with st.expander("ipinfo.io Token"):
        ipinfo_token = st.text_input(
            "ipinfo.io Token",
            type="password",
            key="ipinfo_token",
            placeholder="your_token_here",
            label_visibility="collapsed",
        )
        st.caption("[取得免費 Token](https://ipinfo.io/signup)")

    with st.expander("AbuseIPDB API Key"):
        abuseipdb_key = st.text_input(
            "AbuseIPDB Key",
            type="password",
            key="abuseipdb_key",
            placeholder="your_api_key",
            label_visibility="collapsed",
        )
        st.caption("[取得 API Key](https://www.abuseipdb.com/api)")

    with st.expander("VirusTotal API Key"):
        virustotal_key = st.text_input(
            "VirusTotal Key",
            type="password",
            key="virustotal_key",
            placeholder="your_api_key",
            label_visibility="collapsed",
        )
        st.caption("[取得 API Key](https://www.virustotal.com/gui/my-apikey)")

    st.divider()
    st.caption("v0.1.0 · 繁體中文介面")
    st.caption("© 2024 SysMon")

# ── 主頁面導覽 ────────────────────────────────────────────────────────────────
pages = [
    st.Page("pages/1_home.py", title="首頁", icon="🏠"),
    st.Page("pages/2_ip_info.py", title="IP 資訊", icon="🌐"),
    st.Page("pages/3_dns.py", title="DNS 查詢", icon="🔍"),
    st.Page("pages/4_whois.py", title="WHOIS", icon="📋"),
    st.Page("pages/5_ssl.py", title="SSL 憑證", icon="🔒"),
    st.Page("pages/6_web_check.py", title="網站檢測", icon="🔗"),
    st.Page("pages/7_port_scan.py", title="連接埠掃描", icon="🔌"),
    st.Page("pages/8_subnet.py", title="子網路計算", icon="🧮"),
    st.Page("pages/9_system.py", title="系統資訊", icon="💻"),
]

pg = st.navigation(pages)
pg.run()
