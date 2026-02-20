"""網站檢測頁面 - HTTP 標頭 / 狀態碼 / 重定向鏈"""

import streamlit as st
import pandas as pd
from sysmon.core.web_tools import check_website, DEFAULT_UA

st.title("🔗 網站檢測")
st.markdown("分析網站 HTTP 標頭、狀態碼、重定向鏈、回應時間等資訊。")

col1, col2 = st.columns([4, 1])
with col1:
    url_input = st.text_input(
        "URL",
        placeholder="https://example.com 或 example.com",
        label_visibility="collapsed",
    )
with col2:
    check_btn = st.button("🔍 檢測", type="primary", use_container_width=True)

with st.expander("⚙️ 進階選項"):
    user_agent = st.text_input("User-Agent", value=DEFAULT_UA)
    timeout = st.slider("逾時（秒）", 5, 60, 15)

if check_btn and url_input:
    with st.spinner(f"正在檢測 {url_input}..."):
        result = check_website(url_input.strip(), user_agent, timeout)

    if "error" in result:
        st.error(f"檢測失敗：{result['error']}")
    else:
        status = result.get("status_code", 0)
        status_color = "🟢" if 200 <= status < 300 else "🟡" if 300 <= status < 400 else "🔴"

        # 指標卡片
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("狀態碼", f"{status_color} {status} {result.get('status_text', '')}")
        col2.metric("回應時間", f"{result.get('response_time_ms', 0):.0f} ms")
        col3.metric("內容大小", f"{result.get('content_length', 0) / 1024:.1f} KB")
        col4.metric("伺服器", result.get("server", "未知"))

        # 頁面標題
        if result.get("title"):
            st.info(f"📄 頁面標題：**{result['title']}**")

        # 重定向鏈
        redirect_chain = result.get("redirect_chain", [])
        if redirect_chain:
            st.markdown("#### 🔄 重定向鏈")
            for i, r in enumerate(redirect_chain):
                st.write(f"`{r['status_code']} {r['status_text']}` → {r['url']}")
            st.write(f"最終 URL：`{result.get('url', '')}`")

        # HTTP 標頭
        st.markdown("#### 📋 HTTP 回應標頭")
        headers = result.get("headers", {})
        if headers:
            # 重要標頭置頂
            priority_headers = [
                "content-type", "server", "x-powered-by", "strict-transport-security",
                "content-security-policy", "x-frame-options", "x-xss-protection",
                "cache-control", "etag", "last-modified", "set-cookie",
            ]
            rows = []
            for key in priority_headers:
                if key in headers:
                    rows.append({"標頭": key, "值": headers[key]})
            for key, val in headers.items():
                if key not in priority_headers:
                    rows.append({"標頭": key, "值": val})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # 安全標頭分析
        with st.expander("🔐 安全標頭分析"):
            security_headers = {
                "Strict-Transport-Security": "strict-transport-security",
                "Content-Security-Policy": "content-security-policy",
                "X-Frame-Options": "x-frame-options",
                "X-XSS-Protection": "x-xss-protection",
                "X-Content-Type-Options": "x-content-type-options",
                "Referrer-Policy": "referrer-policy",
            }
            for display_name, header_key in security_headers.items():
                if header_key in headers:
                    st.success(f"✅ {display_name}：`{headers[header_key]}`")
                else:
                    st.warning(f"⚠️ {display_name}：**未設定**")

with st.expander("ℹ️ 使用說明"):
    st.markdown("""
    - 輸入完整 URL（含 `https://`）或裸域名
    - **重定向鏈**：顯示每一步的狀態碼與目標 URL
    - **安全標頭分析**：檢查常見 HTTP 安全標頭是否設定
    - SSL 驗證警告已停用（可檢測自簽憑證網站）
    """)
