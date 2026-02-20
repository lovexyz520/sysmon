"""DNS 查詢頁面 - 多類型 DNS 記錄查詢"""

import streamlit as st
import pandas as pd
from sysmon.core.dns_tools import query_dns, query_all_types, bulk_query, RECORD_TYPES, DNS_SERVERS

st.title("🔍 DNS 查詢")
st.markdown("查詢域名的各類型 DNS 記錄，支援自訂 DNS 伺服器。")

# ── 模式選擇 ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["單筆查詢", "全類型查詢", "批次查詢"])

# ── 單筆查詢 ───────────────────────────────────────────────────────────────────
with tab1:
    col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
    with col1:
        domain = st.text_input("域名", placeholder="example.com", key="dns_domain")
    with col2:
        rtype = st.selectbox("記錄類型", RECORD_TYPES, key="dns_rtype")
    with col3:
        dns_server_label = st.selectbox("DNS 伺服器", list(DNS_SERVERS.keys()), key="dns_server")
        dns_server = DNS_SERVERS[dns_server_label]
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        query_btn = st.button("🔍 查詢", key="dns_query_btn", type="primary", use_container_width=True)

    # 自訂 DNS
    if dns_server_label == "系統預設":
        custom_dns = st.text_input("自訂 DNS IP（選填）", placeholder="如 8.8.4.4", key="custom_dns")
        if custom_dns.strip():
            dns_server = custom_dns.strip()

    if query_btn and domain:
        with st.spinner(f"查詢 {domain} 的 {rtype} 記錄..."):
            result = query_dns(domain, rtype, dns_server)

        if result.get("error"):
            st.warning(f"⚠️ {result['error']}")
        else:
            st.success(f"找到 {len(result['records'])} 筆記錄")
            df = pd.DataFrame({"記錄": result["records"]})
            st.dataframe(df, use_container_width=True, hide_index=True)

# ── 全類型查詢 ─────────────────────────────────────────────────────────────────
with tab2:
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        domain_all = st.text_input("域名", placeholder="example.com", key="dns_all_domain")
    with col2:
        dns_server_all_label = st.selectbox("DNS 伺服器", list(DNS_SERVERS.keys()), key="dns_all_server")
        dns_server_all = DNS_SERVERS[dns_server_all_label]
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        query_all_btn = st.button("🔍 全部查詢", key="dns_all_btn", type="primary", use_container_width=True)

    if query_all_btn and domain_all:
        with st.spinner(f"查詢 {domain_all} 所有記錄類型..."):
            all_results = query_all_types(domain_all, dns_server_all)

        for rtype_key, res in all_results.items():
            if res.get("error") or not res.get("records"):
                continue
            with st.expander(f"**{rtype_key}** ({len(res['records'])} 筆)", expanded=True):
                for rec in res["records"]:
                    st.code(rec)

# ── 批次查詢 ───────────────────────────────────────────────────────────────────
with tab3:
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        domains_text = st.text_area(
            "多個域名（每行一個）",
            placeholder="google.com\ncloudflare.com\ngithub.com",
            height=120,
            key="dns_bulk_domains",
        )
    with col2:
        bulk_rtype = st.selectbox("記錄類型", RECORD_TYPES, key="dns_bulk_rtype")
        dns_bulk_label = st.selectbox("DNS 伺服器", list(DNS_SERVERS.keys()), key="dns_bulk_server")
        dns_bulk = DNS_SERVERS[dns_bulk_label]
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        bulk_btn = st.button("🔍 批次查詢", key="dns_bulk_btn", type="primary", use_container_width=True)

    if bulk_btn and domains_text:
        domains_list = [d.strip() for d in domains_text.strip().splitlines() if d.strip()]
        with st.spinner(f"批次查詢 {len(domains_list)} 個域名..."):
            bulk_results = bulk_query(domains_list, bulk_rtype, dns_bulk)

        rows = []
        for res in bulk_results:
            if res.get("error"):
                rows.append({"域名": res["domain"], "記錄": f"⚠️ {res['error']}"})
            else:
                for rec in res["records"]:
                    rows.append({"域名": res["domain"], "記錄": rec})

        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

with st.expander("ℹ️ 記錄類型說明"):
    st.markdown("""
    | 類型 | 說明 |
    |------|------|
    | A | IPv4 位址 |
    | AAAA | IPv6 位址 |
    | MX | 郵件伺服器 |
    | TXT | 文字記錄（SPF、DKIM 等）|
    | NS | 名稱伺服器 |
    | CNAME | 別名記錄 |
    | PTR | 反向解析 |
    | SOA | 授權起始記錄 |
    | SRV | 服務記錄 |
    | CAA | 憑證授權機構 |
    """)
