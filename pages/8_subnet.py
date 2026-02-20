"""子網路計算頁面 - CIDR 子網路計算器"""

import streamlit as st
import pandas as pd
from sysmon.core.subnet_calc import calculate_subnet, split_subnet

st.title("🧮 子網路計算器")
st.markdown("輸入 CIDR 表示法，計算子網路位址範圍、主機數等詳細資訊。")

tab1, tab2 = st.tabs(["子網路計算", "子網路分割"])

# ── 子網路計算 ─────────────────────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        cidr_input = st.text_input(
            "CIDR 表示法",
            placeholder="192.168.1.0/24 或 10.0.0.1/16",
            label_visibility="collapsed",
        )
    with col2:
        calc_btn = st.button("🧮 計算", type="primary", use_container_width=True)

    # 常用範例
    st.caption("快速範例：")
    col1, col2, col3, col4 = st.columns(4)
    examples = ["192.168.1.0/24", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/30"]
    for col, example in zip([col1, col2, col3, col4], examples):
        if col.button(example, key=f"example_{example}"):
            cidr_input = example
            calc_btn = True

    if calc_btn and cidr_input:
        result = calculate_subnet(cidr_input.strip())

        if "error" in result:
            st.error(f"計算失敗：{result['error']}")
        else:
            # 指標卡片
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("版本", result.get("version", ""))
            col2.metric("前綴長度", f"/{result.get('prefix_length', '')} ({result.get('netmask', '')})")
            col3.metric("總位址數", f"{result.get('total_addresses', 0):,}")
            col4.metric("可用主機數", f"{result.get('usable_hosts', 0):,}")

            # 詳細資訊
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📊 位址資訊")
                info = {
                    "CIDR 表示法": result.get("compressed", ""),
                    "輸入 IP": result.get("input_ip", ""),
                    "網路位址": result.get("network_address", ""),
                    "廣播位址": result.get("broadcast_address", ""),
                    "子網路遮罩": result.get("netmask", ""),
                    "第一個主機": result.get("first_host", ""),
                    "最後一個主機": result.get("last_host", ""),
                }
                df = pd.DataFrame(list(info.items()), columns=["欄位", "值"])
                st.dataframe(df, use_container_width=True, hide_index=True)

            with col2:
                st.markdown("#### 🔍 網路屬性")
                attrs = {
                    "私有網路": "✅ 是" if result.get("is_private") else "否",
                    "全球可路由": "✅ 是" if result.get("is_global") else "否",
                    "多播位址": "是" if result.get("is_multicast") else "否",
                    "迴環位址": "是" if result.get("is_loopback") else "否",
                }
                df_attrs = pd.DataFrame(list(attrs.items()), columns=["屬性", "值"])
                st.dataframe(df_attrs, use_container_width=True, hide_index=True)

            # 主機清單
            host_list = result.get("host_list", [])
            if host_list:
                with st.expander(f"📋 主機 IP 清單（{result.get('usable_hosts', 0):,} 個）"):
                    if "..." in host_list:
                        st.info("清單過長，僅顯示前 10 筆及最後一筆")
                    cols = st.columns(4)
                    for i, h in enumerate(host_list):
                        cols[i % 4].code(h)

# ── 子網路分割 ─────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("將一個大子網路分割為多個較小的子網路。")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        parent_cidr = st.text_input("父網路 CIDR", placeholder="192.168.1.0/24", key="split_cidr")
    with col2:
        new_prefix = st.number_input("新前綴長度", min_value=1, max_value=128, value=26)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        split_btn = st.button("✂️ 分割", type="primary", use_container_width=True)

    if split_btn and parent_cidr:
        split_result = split_subnet(parent_cidr.strip(), int(new_prefix))
        if "error" in split_result:
            st.error(split_result["error"])
        else:
            st.success(f"將 `{split_result['parent']}` 分割為 **{split_result['count']:,}** 個 `/{split_result['new_prefix']}` 子網路")
            if split_result.get("truncated"):
                st.info("結果過多，僅顯示前 64 個")
            subnets = split_result.get("subnets", [])
            cols = st.columns(4)
            for i, subnet in enumerate(subnets):
                cols[i % 4].code(subnet)
