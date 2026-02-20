"""WHOIS 查詢頁面"""

import streamlit as st
import pandas as pd
from sysmon.core.whois_tools import query_whois

st.title("📋 WHOIS 查詢")
st.markdown("查詢域名或 IP 的 WHOIS 資訊，包含註冊商、有效期、Name Servers 等。")

col1, col2 = st.columns([4, 1])
with col1:
    target = st.text_input(
        "域名或 IP",
        placeholder="example.com 或 8.8.8.8",
        label_visibility="collapsed",
    )
with col2:
    query_btn = st.button("🔍 查詢", type="primary", use_container_width=True)

if query_btn and target:
    with st.spinner(f"查詢 {target} 的 WHOIS 資訊..."):
        result = query_whois(target.strip())

    if "error" in result:
        st.error(f"查詢失敗：{result['error']}")
    elif result.get("type") == "domain":
        st.success("域名 WHOIS 查詢完成")

        # 關鍵資訊卡片
        col1, col2, col3 = st.columns(3)
        col1.metric("📅 建立日期", result.get("creation_date") or "未知")
        col2.metric("⏳ 到期日期", result.get("expiration_date") or "未知")
        col3.metric("🔄 更新日期", result.get("updated_date") or "未知")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📝 基本資訊")
            basic_info = {
                "域名": result.get("domain", ""),
                "註冊商": result.get("registrar") or "未知",
                "組織": result.get("org") or "未知",
                "國家": result.get("country") or "未知",
                "狀態": ", ".join(result.get("status") or []) if isinstance(result.get("status"), list) else str(result.get("status") or ""),
            }
            df_basic = pd.DataFrame(list(basic_info.items()), columns=["欄位", "值"])
            st.dataframe(df_basic, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("#### 🖥️ Name Servers")
            ns_list = result.get("name_servers") or []
            if isinstance(ns_list, list):
                for ns in ns_list:
                    st.code(ns)
            else:
                st.code(str(ns_list))

        if result.get("emails"):
            with st.expander("📧 聯絡信箱"):
                emails = result["emails"]
                if isinstance(emails, list):
                    for email in emails:
                        st.write(email)
                else:
                    st.write(emails)

        with st.expander("📄 原始 WHOIS 資料"):
            st.text(result.get("raw", ""))

    elif result.get("type") == "ip":
        st.success("IP WHOIS 查詢完成")

        col1, col2, col3 = st.columns(3)
        col1.metric("ASN", result.get("asn") or "未知")
        col2.metric("國家", result.get("asn_country_code") or "未知")
        col3.metric("CIDR", result.get("asn_cidr") or "未知")

        st.markdown("#### 📊 詳細資訊")
        info = {
            "IP 位址": result.get("ip", ""),
            "ASN": result.get("asn", ""),
            "ASN 說明": result.get("asn_description", ""),
            "ASN 國家": result.get("asn_country_code", ""),
            "CIDR": result.get("asn_cidr", ""),
            "網路名稱": result.get("network_name", ""),
            "網路範圍": result.get("network_cidr", ""),
            "起始 IP": result.get("network_start", ""),
            "結束 IP": result.get("network_end", ""),
            "網路國家": result.get("network_country", ""),
        }
        df = pd.DataFrame(list(info.items()), columns=["欄位", "值"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        if result.get("entities"):
            with st.expander("🏢 相關實體"):
                for entity in result["entities"]:
                    st.write(f"• {entity}")

with st.expander("ℹ️ 使用說明"):
    st.markdown("""
    - **域名查詢**：輸入如 `google.com`、`example.org`
    - **IP 查詢**：輸入如 `8.8.8.8`（使用 RDAP 協定）
    - WHOIS 資料由各域名註冊機構提供，部分資訊可能因隱私保護而遮蔽
    """)
