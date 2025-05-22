from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date

from matplotlib import pyplot as plt
import requests
import logging

import plotly.graph_objects as go

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取 API 密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TIINGO_API_KEY = os.getenv("TIINGO_API_KEY")

# 检查 OpenAI 密钥
if not OPENAI_API_KEY:
    st.error("⚠️ 请在 .env 文件中设置 OPENAI_API_KEY，例如：OPENAI_API_KEY=sk-your_key")
    st.stop()

# 检查 Tiingo 密钥，决定数据源
USE_TIINGO = TIINGO_API_KEY is not None
if not USE_TIINGO:
    st.info("ℹ️ 未检测到 TIINGO_API_KEY，将使用 yfinance 获取股票数据。")

# Tiingo 认证方式（'url' 或 'headers'）
TIINGO_AUTH_METHOD = 'headers'  # 推荐使用 'headers' 提高安全性

# 缓存文件路径
PRICE_CACHE_DIR = "cache/prices"
NEWS_CACHE_DIR = "cache/news"
os.makedirs(PRICE_CACHE_DIR, exist_ok=True)
os.makedirs(NEWS_CACHE_DIR, exist_ok=True)


def fetch_tiingo_prices(ticker, start_date, end_date, api_key, auth_method='headers'):
    """使用 Tiingo API 获取历史价格数据，带缓存"""
    cache_file = os.path.join(PRICE_CACHE_DIR,
                              f"{ticker.lower()}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv")

    # 检查缓存
    if os.path.exists(cache_file):
        try:
            data = pd.read_csv(cache_file, parse_dates=['date'], index_col='date')
            logger.info(f"从缓存加载价格数据: {cache_file}")
            return data
        except Exception as e:
            logger.warning(f"缓存加载失败: {e}, 重新获取数据")

    headers = {'Content-Type': 'application/json'}
    base_url = f"https://api.tiingo.com/tiingo/daily/{ticker.lower()}/prices"
    params = {
        'startDate': start_date.strftime("%Y-%m-%d"),
        'endDate': end_date.strftime("%Y-%m-%d")
    }

    if auth_method == 'url':
        params['token'] = api_key
        url = base_url
    else:
        headers['Authorization'] = f'Token {api_key}'
        url = base_url

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if not data:
            st.warning(f"无价格数据返回: {ticker}")
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'adjClose': 'Adj Close'
        })
        # 缓存数据
        df.to_csv(cache_file)
        logger.info(f"价格数据已缓存: {cache_file}")
        return df
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            st.error(
                "⚠️ Tiingo API 返回 403 Forbidden：请检查 TIINGO_API_KEY 是否有效，或确认您的账户是否支持价格数据（访问 https://www.tiingo.com）。")
        else:
            st.error(f"Tiingo API 错误: {e}")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"网络错误: {e}")
        return pd.DataFrame()


def fetch_tiingo_metadata(ticker, api_key, auth_method='headers'):
    """获取 Tiingo 公司元数据"""
    headers = {'Content-Type': 'application/json'}
    url = f"https://api.tiingo.com/tiingo/daily/{ticker.lower()}"

    if auth_method == 'url':
        params = {'token': api_key}
    else:
        headers['Authorization'] = f'Token {api_key}'
        params = {}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            st.error("⚠️ Tiingo 元数据 403 Forbidden：请检查 TIINGO_API_KEY 或账户权限（https://www.tiingo.com）。")
        return {}
    except requests.exceptions.RequestException as e:
        st.warning(f"无法获取 Tiingo 元数据: {e}")
        return {}
# ✅ 美化后的 Portfolio Analyzer 组件
def render_portfolio_analyzer():
    st.markdown("## 💼 Advanced Portfolio Analyzer (Tiingo Version)")

    num_assets = st.slider("How many stocks in your portfolio?", min_value=2, max_value=10, value=3)
    default_tickers = ["AAPL", "MSFT", "TSLA", "GOOGL", "NVDA", "META", "AMZN", "NFLX", "JPM", "BRK-B"]
    tickers, raw_weights = [], []

    cols = st.columns(5)
    for i in range(num_assets):
        with cols[i % 5]:
            ticker = st.text_input(f"Ticker {i+1}", value=default_tickers[i], key=f"tick_{i}")
            weight = st.number_input(f"Weight %", min_value=0.0, value=10.0, step=1.0, key=f"weight_{i}")
        tickers.append(ticker.upper())
        raw_weights.append(weight)

    total_raw = sum(raw_weights)
    weights = [(w / total_raw) * 100 for w in raw_weights] if total_raw > 0 else [0] * len(raw_weights)
    weights_array = np.array(weights) / 100
    st.caption(f"🔁 Auto-normalized weights: {', '.join([f'{round(w, 1)}%' for w in weights])} → Total = 100%")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date(2022, 1, 1))
    with col2:
        end_date = st.date_input("End Date", value=date.today())

    if st.button("🚀 Run Full Analysis"):
        st.info("Fetching data from Tiingo...")
        price_dfs = {}
        for t in tickers + ["SPY"]:
            df = fetch_tiingo_prices(t, start_date, end_date, TIINGO_API_KEY, TIINGO_AUTH_METHOD)
            if df is not None and not df.empty:
                price_dfs[t] = df
            else:
                st.error(f"❌ Failed to load data for {t}")
                return

        price_close = pd.concat([price_dfs[t]["Adj Close"].rename(t) for t in tickers + ["SPY"]], axis=1).dropna()
        normed = price_close[tickers].div(price_close[tickers].iloc[0])
        portfolio_nav = (normed * weights_array).sum(axis=1)

        # --- NAV 对比 ---
        st.subheader("📈 Portfolio vs SPY ($10,000 base)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=portfolio_nav.index, y=portfolio_nav * 10000, name="Portfolio", line=dict(color="#fbbf24", width=3)))
        fig.add_trace(go.Scatter(x=price_close.index, y=price_close["SPY"] / price_close["SPY"].iloc[0] * 10000,
                                 name="SPY", line=dict(color="#60a5fa", dash="dash")))
        fig.update_layout(template="plotly_dark", height=450, legend=dict(orientation="h", x=0, y=1.1))
        st.plotly_chart(fig, use_container_width=True)

        # --- 技术图卡每支股票 ---
        st.subheader("📊 Individual Stock Technical Charts")
        for t in tickers:
            st.markdown(f"#### {t}")
            df = price_dfs[t].copy()
            df["MA20"] = df["Close"].rolling(20).mean()
            df["MA50"] = df["Close"].rolling(50).mean()
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
                name="Candles", increasing_line_color="#00ff9a", decreasing_line_color="#ff4b4b"))
            fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], mode="lines", name="MA20",
                                     line=dict(color="#facc15", width=1.5)))
            fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], mode="lines", name="MA50",
                                     line=dict(color="#3b82f6", width=1.5)))
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=30, b=20),
                              xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        # --- 股票绩效表 ---
        st.subheader("📋 Asset Performance Summary")
        stats = []
        for i, t in enumerate(tickers):
            ret = price_close[t].pct_change().dropna()
            total = price_close[t].iloc[-1] / price_close[t].iloc[0] - 1
            annual = (1 + total) ** (252 / len(ret)) - 1
            vol = ret.std() * np.sqrt(252)
            sharpe = annual / vol if vol > 0 else 0
            stats.append({
                "Ticker": t,
                "Weight %": f"{weights[i]:.1f}%",
                "Total Return": f"{total*100:.2f}%",
                "Annualized Return": f"{annual*100:.2f}%",
                "Volatility": f"{vol*100:.2f}%",
                "Sharpe Ratio": f"{sharpe:.2f}"
            })
        st.dataframe(pd.DataFrame(stats))

        # --- 风险雷达图 ---
        st.subheader("🧭 Risk Contribution Radar")
        metric = st.selectbox("Radar Metric", ["Volatility", "Sharpe Ratio"])
        radar_values = []
        for i, t in enumerate(tickers):
            ret = price_close[t].pct_change().dropna()
            if metric == "Volatility":
                val = ret.std() * np.sqrt(252)
            else:
                ann = (1 + (price_close[t].iloc[-1] / price_close[t].iloc[0] - 1)) ** (252 / len(ret)) - 1
                vol = ret.std() * np.sqrt(252)
                val = ann / vol if vol > 0 else 0
            radar_values.append(val)

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_values + [radar_values[0]],
            theta=tickers + [tickers[0]],
            fill='toself',
            line=dict(color="#fbbf24")
        ))
        fig_radar.update_layout(template="plotly_dark", height=500, margin=dict(t=30))
        st.plotly_chart(fig_radar, use_container_width=True)



