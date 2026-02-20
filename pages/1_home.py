"""首頁 - 儀表板：顯示 IP / 位置 / ISP 摘要"""

import streamlit as st
import pandas as pd
from streamlit_javascript import st_javascript
from sysmon.core.ip_info import query_ip

st.title("🏠 SysMon 儀表板")
st.markdown("歡迎使用 SysMon 系統查詢工具，快速取得網路與系統資訊。")

# ── 功能卡片 ───────────────────────────────────────────────────────────────────
st.markdown("### 🗂️ 功能總覽")

col1, col2, col3 = st.columns(3)
with col1:
    st.info("**🌐 IP 資訊**\nIP 地理位置、ISP、ASN 查詢")
    st.info("**🔍 DNS 查詢**\nA、MX、TXT 等多類型 DNS 記錄")
    st.info("**📋 WHOIS**\n域名與 IP WHOIS 查詢")
with col2:
    st.info("**🔒 SSL 憑證**\n憑證詳情、到期日倒數")
    st.info("**🔗 網站檢測**\nHTTP 標頭、狀態碼、重定向鏈")
    st.info("**🔌 連接埠掃描**\n多執行緒連接埠掃描")
with col3:
    st.info("**🧮 子網路計算**\nCIDR 子網路計算器")
    st.info("**💻 系統資訊**\nCPU/RAM/磁碟（本機限定）")
    st.success("**免費使用**\n核心功能無需 API Key")

st.divider()

# ── 當前 IP 摘要 ───────────────────────────────────────────────────────────────
st.markdown("### 📍 您的網路資訊")

# 從瀏覽器端（客戶端）取得真實公網 IP，繞過 Streamlit Cloud 伺服器端限制
client_ip = st_javascript(
    "await fetch('https://api.ipify.org?format=json')"
    ".then(r => r.json()).then(d => d.ip).catch(() => '')"
)

# st_javascript 第一次渲染回傳 0，等 JS 執行完才有值
if not isinstance(client_ip, str) or not client_ip:
    st.info("⏳ 正在偵測您的公網 IP...")
    st.stop()

with st.spinner("查詢 IP 資訊..."):
    ipinfo_token = st.session_state.get("ipinfo_token", "")
    data = query_ip(client_ip, ipinfo_token)

if "error" in data:
    st.error(f"無法取得 IP 資訊：{data['error']}")
else:
    isp = data.get("isp", "未知")
    asn = data.get("as", "未知")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌍 公網 IP", data.get("query", "未知"))
    col2.metric("🏳️ 國家", data.get("country", "未知"))
    col3.metric("🏙️ 城市", data.get("city", "未知"))
    col4.metric("📡 ISP", isp[:20] + "..." if len(isp) > 20 else isp)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🕐 時區", data.get("timezone", "未知"))
    col2.metric("🔢 ASN", asn[:20] + "..." if len(asn) > 20 else asn)
    col3.metric("🕵️ 代理/VPN", "是" if data.get("proxy") else "否")
    col4.metric("🏢 資料中心", "是" if data.get("hosting") else "否")

    # 地圖
    lat = data.get("lat", 0)
    lon = data.get("lon", 0)
    if lat and lon:
        df = pd.DataFrame({"lat": [lat], "lon": [lon]})
        st.markdown("#### 📍 IP 位置地圖")
        st.map(df, zoom=5)

st.divider()
st.markdown(
    "💡 **提示**：在左側邊欄輸入 API Key 可解鎖 ipinfo.io 精確地理資訊、"
    "AbuseIPDB IP 信譽查詢等進階功能。"
)
