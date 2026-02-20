"""首頁 - 儀表板：顯示 IP / 位置 / ISP 摘要"""

import ipaddress
import streamlit as st
from sysmon.core.ip_info import query_ip, get_public_ip


def _get_client_ip() -> str:
    """從 Streamlit request headers 取得客戶端真實公網 IP。
    優先順序：CF-Connecting-IP（Cloudflare）→ X-Forwarded-For → X-Real-IP
    過濾掉私有/迴環位址，避免傳入 ip-api.com 導致 private range 錯誤。
    """
    def is_public(ip: str) -> bool:
        try:
            addr = ipaddress.ip_address(ip)
            return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_unspecified)
        except ValueError:
            return False

    try:
        headers = st.context.headers
        # Cloudflare 直接給真實 client IP
        cf_ip = headers.get("CF-Connecting-IP", "").strip()
        if cf_ip and is_public(cf_ip):
            return cf_ip
        # 標準代理 header，逐一檢查每個 IP
        for candidate in headers.get("X-Forwarded-For", "").split(","):
            candidate = candidate.strip()
            if candidate and is_public(candidate):
                return candidate
        # nginx 代理 header
        real_ip = headers.get("X-Real-IP", "").strip()
        if real_ip and is_public(real_ip):
            return real_ip
    except Exception:
        pass
    return ""


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

with st.spinner("正在偵測公網 IP..."):
    detected_ip = _get_client_ip()
    ipinfo_token = st.session_state.get("ipinfo_token", "")
    data = query_ip(detected_ip, ipinfo_token)

# ── 暫時 Debug（確認 headers 後可移除）─────────────────────────────────────────
with st.expander("🛠️ Debug: Request Headers（確認後請移除）"):
    try:
        all_headers = dict(st.context.headers)
        st.write(f"**偵測到的 IP**：`{detected_ip or '（未偵測到，使用 fallback）'}`")
        st.json(all_headers)
    except Exception as e:
        st.write(f"無法讀取 headers：{e}")

if "error" in data:
    st.error(f"無法取得 IP 資訊：{data['error']}")
else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌍 公網 IP", data.get("query", "未知"))
    col2.metric("🏳️ 國家", data.get("country", "未知"))
    col3.metric("🏙️ 城市", data.get("city", "未知"))
    col4.metric("📡 ISP", data.get("isp", "未知")[:20] + "..." if len(data.get("isp", "")) > 20 else data.get("isp", "未知"))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🕐 時區", data.get("timezone", "未知"))
    col2.metric("🔢 ASN", data.get("as", "未知")[:20] + "..." if len(data.get("as", "")) > 20 else data.get("as", "未知"))
    col3.metric("🕵️ 代理/VPN", "是" if data.get("proxy") else "否")
    col4.metric("🏢 資料中心", "是" if data.get("hosting") else "否")

    # 地圖
    lat = data.get("lat", 0)
    lon = data.get("lon", 0)
    if lat and lon:
        import pandas as pd
        df = pd.DataFrame({"lat": [lat], "lon": [lon]})
        st.markdown("#### 📍 IP 位置地圖")
        st.map(df, zoom=5)

st.divider()
st.markdown(
    "💡 **提示**：在左側邊欄輸入 API Key 可解鎖 ipinfo.io 精確地理資訊、"
    "AbuseIPDB IP 信譽查詢等進階功能。"
)
