"""SSL 憑證頁面 - 憑證詳情 + 到期倒數"""

import streamlit as st
import pandas as pd
from sysmon.core.ssl_tools import query_ssl

st.title("🔒 SSL 憑證查詢")
st.markdown("查詢網站 SSL/TLS 憑證詳情、SAN 清單、憑證鏈及到期倒數。")

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    hostname = st.text_input(
        "主機名稱",
        placeholder="example.com（無需 https://）",
        label_visibility="collapsed",
    )
with col2:
    port = st.number_input("連接埠", value=443, min_value=1, max_value=65535)
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    query_btn = st.button("🔒 查詢", type="primary", use_container_width=True)

if query_btn and hostname:
    with st.spinner(f"連線至 {hostname}:{port} 取得憑證..."):
        result = query_ssl(hostname.strip(), int(port))

    if "error" in result:
        st.error(f"查詢失敗：{result['error']}")
    else:
        days_left = result.get("days_left", 0)

        # 到期狀態
        if result.get("is_expired"):
            st.error(f"❌ 憑證已到期 {abs(days_left)} 天！")
        elif result.get("is_expiring_soon"):
            st.warning(f"⚠️ 憑證即將到期！剩餘 {days_left} 天")
        else:
            st.success(f"✅ 憑證有效，剩餘 {days_left} 天")

        # 指標卡片
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("主機", result.get("hostname", ""))
        col2.metric("剩餘天數", f"{days_left} 天")
        col3.metric("到期日", result.get("not_after", "")[:10])
        col4.metric("版本", result.get("version", ""))

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📜 憑證主體")
            subject = result.get("subject", {})
            sub_df = pd.DataFrame(list(subject.items()), columns=["欄位", "值"])
            st.dataframe(sub_df, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("#### 🏢 頒發者")
            issuer = result.get("issuer", {})
            iss_df = pd.DataFrame(list(issuer.items()), columns=["欄位", "值"])
            st.dataframe(iss_df, use_container_width=True, hide_index=True)

        # 有效期
        st.markdown("#### 📅 有效期")
        col1, col2, col3 = st.columns(3)
        col1.metric("生效日期", result.get("not_before", "")[:10])
        col2.metric("到期日期", result.get("not_after", "")[:10])
        col3.metric("序號", result.get("serial_number", "")[:16] + "...")

        # SAN
        san_list = result.get("san", [])
        if san_list:
            with st.expander(f"🌐 SAN 清單（{len(san_list)} 個域名）", expanded=True):
                cols = st.columns(3)
                for i, san in enumerate(san_list):
                    cols[i % 3].code(san)

        # 技術詳情
        with st.expander("🔧 技術詳情"):
            st.write(f"**簽章演算法 OID**：{result.get('signature_algorithm', '')}")
            st.write(f"**序號（完整）**：{result.get('serial_number', '')}")

with st.expander("ℹ️ 使用說明"):
    st.markdown("""
    - 輸入主機名稱（無需 `https://`），如 `google.com`
    - 預設連接埠 443（HTTPS），可修改為其他 TLS 連接埠
    - 到期不足 **30 天**顯示警告，已到期顯示錯誤
    - SAN（Subject Alternative Names）列出憑證覆蓋的所有域名
    """)
