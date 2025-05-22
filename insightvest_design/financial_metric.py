
import os

# --- 你需要将 TIINGO_API_KEY 设置为环境变量或直接填写 ---
TIINGO_API_KEY = os.getenv("TIINGO_API_KEY")

import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from dotenv import load_dotenv

# === 加载 Tiingo API Key ===
load_dotenv()

# === 安全绘图函数 ===
# === 绘图函数 ===
def plot_trend(df, metric, ylabel):
    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.plot(df["Year"], df[metric], marker="o", linewidth=2, color="#fbbf24")
    ax.set_title(f"{metric} Trend", fontsize=14)
    ax.set_ylabel(ylabel)
    ax.set_xticks(df["Year"])
    ax.grid(True, linestyle='--', alpha=0.4)
    return fig

# === 兼容字段的稳定获取函数 ===
def get_tiingo_statements_data_final(ticker="AAPL"):
    url = f"https://api.tiingo.com/tiingo/fundamentals/{ticker}/statements"
    params = {"token": TIINGO_API_KEY}

    try:
        res = requests.get(url, params=params)
        if res.status_code != 200:
            st.error(f"❌ Tiingo API error {res.status_code}: {res.text}")
            return pd.DataFrame()

        data = res.json()
        if not isinstance(data, list) or len(data) == 0:
            st.warning("No statement data found.")
            return pd.DataFrame()

        records = []
        for item in data:
            if not isinstance(item, dict):
                continue
            if item.get("quarter") != 4 or not item.get("year"):
                continue

            year = item["year"]
            statement_data = item.get("statementData")
            if not isinstance(statement_data, dict):
                continue

            income = statement_data.get("incomeStatement", [])
            balance = statement_data.get("balanceSheet", [])

            def extract(data_list, *codes):
                for code in codes:
                    for d in data_list:
                        if d.get("dataCode") == code:
                            return d.get("value")
                return None

            revenue = extract(income, "revenue")
            net_income = extract(income, "netinc", "consolidatedIncome")
            eps = extract(income, "eps", "epsDil")
            equity = extract(balance, "equity")

            if None in [revenue, net_income, eps, equity] or equity == 0:
                continue

            roe = (net_income / equity) * 100
            records.append({
                "Year": year,
                "Revenue": revenue / 1e6,
                "Net Income": net_income / 1e6,
                "EPS": eps,
                "ROE": roe
            })

        if not records:
            st.warning("No complete annual records found.")
            return pd.DataFrame()

        df = pd.DataFrame(records).dropna()
        df["Year"] = df["Year"].astype(int)
        return df.sort_values("Year").reset_index(drop=True)

    except Exception as e:
        st.error(f"❌ Failed to fetch statements data: {e}")
        return pd.DataFrame()

# === UI 主入口 ===
def render_tiingo_statements_trend_cards():
    st.markdown("""
    <div style="padding:1.5rem;background-color:#1F2937;border-radius:12px;margin-bottom:1.5rem;">
        <h3 style="color:#fbbf24;">📊 Key Financial Trends (from Tiingo /statements)</h3>
        <p style="color:#f3f4f6;">Powered by official income & balance sheet data. Supports AAPL, MSFT, TSLA, etc.</p>
    </div>
    """, unsafe_allow_html=True)

    ticker = st.text_input("Enter Stock Ticker", value="AAPL")
    if st.button("📥 Load Annual Statement Trends"):
        with st.spinner("Fetching financial statement data..."):
            df = get_tiingo_statements_data_final(ticker)
            if df.empty:
                st.warning("No valid data available.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.pyplot(plot_trend(df, "Revenue", "Million USD"))
                    st.pyplot(plot_trend(df, "EPS", "USD"))
                with col2:
                    st.pyplot(plot_trend(df, "Net Income", "Million USD"))
                    st.pyplot(plot_trend(df, "ROE", "%"))

