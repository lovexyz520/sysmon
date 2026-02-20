"""IP 資訊頁面 - 詳細 IP 地理/ISP/ASN 查詢"""

import streamlit as st
import pandas as pd
from sysmon.core.ip_info import query_ip, format_ip_info

st.title("🌐 IP 資訊查詢")
st.markdown("查詢 IP 的地理位置、ISP、ASN、代理偵測等詳細資訊。")

# ── 輸入區 ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    ip_input = st.text_input(
        "IP 位址",
        placeholder="留空自動偵測，或輸入如 8.8.8.8、2001:4860:4860::8888",
        label_visibility="collapsed",
    )
with col2:
    query_btn = st.button("🔍 查詢", use_container_width=True, type="primary")

if query_btn:
    ipinfo_token = st.session_state.get("ipinfo_token", "")

    with st.spinner("查詢中..."):
        data = query_ip(ip_input.strip(), ipinfo_token)

    if "error" in data:
        st.error(f"查詢失敗：{data['error']}")
    else:
        st.success(f"查詢完成 · 資料來源：{data.get('_source', 'ip-api.com')}")

        # ── 指標卡片 ───────────────────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("IP 位址", data.get("query", ""))
        col2.metric("國家", data.get("country", ""))
        col3.metric("城市", data.get("city", ""))
        col4.metric("地區", data.get("regionName", ""))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("時區", data.get("timezone", ""))
        col2.metric("ISP", data.get("isp", "")[:18] + "..." if len(data.get("isp", "")) > 18 else data.get("isp", ""))
        col3.metric("代理/VPN", "⚠️ 是" if data.get("proxy") else "✅ 否")
        col4.metric("資料中心", "⚠️ 是" if data.get("hosting") else "✅ 否")

        # ── 完整資訊表 ─────────────────────────────────────────────────────────
        st.markdown("#### 📊 詳細資訊")
        info_dict = format_ip_info(data)
        df = pd.DataFrame(list(info_dict.items()), columns=["欄位", "值"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ── ASN 資訊 ──────────────────────────────────────────────────────────
        if data.get("as"):
            with st.expander("🔢 ASN 詳細資訊"):
                st.write(f"**AS 號碼**：{data.get('as', '')}")
                st.write(f"**AS 名稱**：{data.get('asname', '')}")
                st.write(f"**組織**：{data.get('org', '')}")

        # ── 地圖 ──────────────────────────────────────────────────────────────
        lat = data.get("lat", 0)
        lon = data.get("lon", 0)
        if lat and lon:
            st.markdown("#### 📍 地理位置")
            df_map = pd.DataFrame({"lat": [lat], "lon": [lon]})
            st.map(df_map, zoom=8)

# ── 使用提示 ───────────────────────────────────────────────────────────────────
with st.expander("ℹ️ 使用說明"):
    st.markdown("""
    - **留空查詢**：自動偵測您的公網 IP
    - **輸入 IPv4**：如 `8.8.8.8`
    - **輸入 IPv6**：如 `2001:4860:4860::8888`
    - **進階功能**：在側邊欄輸入 ipinfo.io Token 取得更精確資訊
    - **免費限制**：ip-api.com 每分鐘限 45 次查詢
    """)
