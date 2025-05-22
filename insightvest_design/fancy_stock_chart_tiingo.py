from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from matplotlib import pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import yfinance as yf
import requests
import pickle
import logging

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


def fetch_tiingo_news(ticker, start_date, end_date, api_key, auth_method='headers'):
    """获取 Tiingo 新闻数据（带缓存 + 安全返回）"""
    cache_file = os.path.join(
        NEWS_CACHE_DIR,
        f"{ticker.lower()}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pkl"
    )

    # === Step 1: 优先使用缓存 ===
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                news = pickle.load(f)
            if isinstance(news, list) and all(isinstance(item, dict) for item in news):
                logger.info(f"✅ 从缓存加载新闻数据: {cache_file}")
                return news
            else:
                logger.warning(f"⚠️ 缓存文件 {cache_file} 内容无效，将重新拉取数据")
        except Exception as e:
            logger.warning(f"⚠️ 加载新闻缓存失败: {e}，将重新获取")
    import streamlit as st


    # === Step 2: 发起 API 请求 ===
    headers = {'Content-Type': 'application/json'}
    url = "https://api.tiingo.com/tiingo/news"
    params = {
        'tickers': ticker.lower(),
        'startDate': start_date.strftime("%Y-%m-%d"),
        'endDate': end_date.strftime("%Y-%m-%d"),
        'limit': 100,
        'sortBy': 'date'
    }

    if auth_method == 'url':
        params['token'] = api_key
    else:
        headers['Authorization'] = f'Token {api_key}'

    try:
        response = requests.get(url, headers=headers, params=params)
        logger.info(f"📡 News API response: {response.status_code} | URL: {response.url}")
        response.raise_for_status()
        news = response.json()

        if not isinstance(news, list):
            st.warning("⚠️ Tiingo API 返回了非列表格式的新闻数据，可能是账户无权限或接口变更。")
            return []

        # === Step 3: 写入缓存 ===
        with open(cache_file, 'wb') as f:
            pickle.dump(news, f)
        logger.info(f"💾 已缓存新闻数据: {cache_file}")

        return news

    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            st.error("🚫 Tiingo 新闻 API 返回 403：请检查 TIINGO_API_KEY 是否正确，或确认是否开通 News API（参考 https://www.tiingo.com/pricing）")
        else:
            st.error(f"❌ Tiingo 新闻 API 错误: {e}")
        return []
    except requests.exceptions.RequestException as e:
        st.warning(f"🌐 网络请求异常：{e}")
        return []


import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def render_news_section(news: list, show_sentiment: bool = True):
    """渲染 Tiingo 新闻列表 + 情绪评分（基于 VADER）"""

    if not news or not isinstance(news, list):
        st.info("📭 无新闻数据，可能时间范围过短或该 ticker 无覆盖。")
        return

    valid_news = [n for n in news if isinstance(n, dict)]
    if not valid_news:
        st.info("📭 无有效新闻条目。")
        return

    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
    st.markdown("<h3>📰 新闻情绪快讯</h3>", unsafe_allow_html=True)

    for article in valid_news[:5]:
        title = article.get("title", "无标题")
        pub_date = article.get("publishedDate", "")[:10]
        description = article.get("description", "") or "（无摘要）"
        url = article.get("url", "#")
        source = article.get("source", "未知来源")

        # 🎯 情绪打分（compound ∈ [-1,1]）
        score = analyzer.polarity_scores(description)["compound"] if show_sentiment else 0.0
        sentiment = "🟢 利好" if score > 0.2 else "🔴 利空" if score < -0.2 else "🟡 中性"
        bar_ratio = int((score + 1) * 50)  # 转为 0–100 进度条

        st.markdown(f"""
        <p><b>{title}</b></p>
        <p style='font-size: 0.85rem; color: gray;'>{pub_date} · {source}</p>
        <p style='font-size: 0.9rem;'>{description[:120]}...</p>
        <p style='font-size: 0.85rem; color: #FFD700;'>
            情绪: {sentiment} （{score:+.2f}） · 
            <a href="{url}" target="_blank">点击阅读原文</a>
        </p>
        """, unsafe_allow_html=True)

        # 🌈 渲染情绪进度条
        st.progress(bar_ratio, text=f"{sentiment}  ({score:+.2f})")

        st.markdown("<hr style='border: 0.5px solid #444;'>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

def get_company_info_from_yfinance(ticker: str) -> dict:
    """
    使用 yfinance 获取公司行业、部门、CEO 和官网等信息
    """
    try:
        info = yf.Ticker(ticker).info
        return {
            "industry": info.get("industry", "N/A"),
            "sector": info.get("sector", "N/A"),
            "ceo": info.get("companyOfficers", [{}])[0].get("name", "N/A") if info.get("companyOfficers") else "N/A",
            "website": info.get("website", "N/A")
        }
    except Exception as e:
        return {
            "industry": "N/A",
            "sector": "N/A",
            "ceo": "N/A",
            "website": "N/A"
        }


from yfinance import Ticker


def render_company_profile(metadata: dict, fallback_ticker: str = ""):
    """渲染公司简介区域，补充 yfinance 数据作为 fallback"""

    if not metadata or not isinstance(metadata, dict):
        return

    company_name = metadata.get('name', fallback_ticker.upper())
    description = metadata.get('description', '')
    exchange = metadata.get('exchangeCode', '')
    ticker = metadata.get('ticker', fallback_ticker.upper())
    start_date = metadata.get('startDate', '')

    # 🟡 Fallback 数据来自 yfinance
    y_info = get_company_info_from_yfinance(ticker)
    industry = y_info.get('industry', 'N/A')
    sector = y_info.get('sector', 'N/A')
    ceo = y_info.get('ceo', 'N/A')
    website = y_info.get('website', 'N/A')

    if not description:
        st.info("📭 无公司简介数据。")
        return

    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
    st.markdown("<h3>🏢 公司简介</h3>", unsafe_allow_html=True)

    st.markdown(f"""
    <p style='font-size: 1.05rem; line-height: 1.7;'>{description}</p>
    <ul style='font-size: 0.9rem; color: #AAAAAA;'>
        <li><b>公司名称：</b> {company_name}</li>
        <li><b>代码：</b> {ticker} · {exchange}</li>
        <li><b>行业：</b> {industry}</li>
        <li><b>部门：</b> {sector}</li>
        <li><b>成立时间：</b> {start_date or "N/A"}</li>
        <li><b>CEO：</b> {ceo}</li>
        <li><b>官网：</b> <a href="{website}" target="_blank">{website}</a></li>
    </ul>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def get_yfinance_market_cap(ticker: str) -> str:
    """
    使用 yfinance 获取市值（marketCap），返回字符串格式（如 902.55B），失败返回 '未提供'
    """
    try:
        info = yf.Ticker(ticker).info
        cap = info.get("marketCap")
        if isinstance(cap, (int, float)) and cap > 0:
            return f"{cap / 1e9:.2f}B"
        else:
            return "未提供"
    except Exception as e:
        return "未提供"

def render_fancy_stock_chart():
    # 自定义 CSS 样式（黑金主题）
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            background: linear-gradient(to right, #BF953F, #FCF6BA, #D5AD36, #F3D261);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 1rem;
            text-shadow: 0 0 15px rgba(212, 175, 55, 0.4);
        }
        .sub-header {
            font-size: 1.5rem;
            background: linear-gradient(to right, #BF953F, #FCF6BA, #D5AD36, #F3D261);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            text-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
        }
        .info-box {
            background-color: rgba(28, 39, 60, 0.7);
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid rgba(212, 175, 55, 0.2);
        }
        .stat-container {
            display: flex;
            justify-content: space-between;
        }
        .stat-box {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
            border: 1px solid rgba(255, 215, 0, 0.2);
            box-shadow: 0 0 12px rgba(255, 215, 0, 0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            width: 100%;
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        .stat-box:hover {
            transform: translateY(-3px);
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
        }
        .stat-box h4 {
            margin: 0;
            font-size: 1.2rem;
            color: #FFD700;
        }
        .stat-box p {
            font-size: 1.6rem;
            font-weight: bold;
            margin-top: 0.5rem;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

    # 创建边栏控制面板
    with st.sidebar:
        st.markdown("<h2 class='sub-header'>⚙️ 控制面板</h2>", unsafe_allow_html=True)
        ticker = st.text_input("输入股票代码", value="AAPL",
                               key=f"stock_ticker_input_{st.session_state.get('section_selected', 'default')}")

        # 时间范围选择
        period_options = {
            "1个月": 30,
            "3个月": 90,
            "6个月": 180,
            "1年": 365,
            "2年": 730
        }
        selected_period = st.selectbox("选择时间范围", list(period_options.keys()))

        # 技术指标选择
        st.markdown("<h3 class='sub-header'>技术指标</h3>", unsafe_allow_html=True)
        show_ma = st.checkbox("移动平均线 (MA)", value=True)
        ma_periods = st.multiselect("MA周期", [5, 10, 20, 50, 100, 200], default=[20, 50, 200])

        show_volume = st.checkbox("成交量", value=True)
        show_rsi = st.checkbox("相对强弱指标 (RSI)", value=False)
        show_macd = st.checkbox("MACD指标", value=False)

        # 可视化样式
        st.markdown("<h3 class='sub-header'>可视化样式</h3>", unsafe_allow_html=True)
        chart_styles = ["传统", "现代科技", "专业交易", "暗黑模式", "清新绿色"]
        selected_style = st.selectbox("选择样式主题", chart_styles)

        # 新闻情绪选项（仅 Tiingo 可用时显示）
        show_news = st.checkbox("显示新闻情绪快讯", value=False, disabled=not USE_TIINGO)

        analyze_button = st.button("🔍 开始分析", use_container_width=True)

    # 主界面
    if analyze_button or 'data' in st.session_state:
        try:
            # 获取数据
            end_date = datetime.today()
            start_date = end_date - timedelta(days=period_options[selected_period])

            # 显示加载中信息
            with st.spinner(f"正在加载 {ticker.upper()} 的历史数据..."):
                if USE_TIINGO:
                    # 使用 Tiingo 获取数据
                    data = fetch_tiingo_prices(ticker, start_date, end_date, TIINGO_API_KEY, TIINGO_AUTH_METHOD)
                else:
                    # 使用 yfinance 获取数据
                    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)

                # 调试信息
                st.write("调试信息：原始数据预览")
                st.write(data.head())
                st.write(f"数据行数: {len(data)}")

                st.session_state.data = data
                st.session_state.ticker = ticker

            if data.empty:
                st.warning("⚠️ 没有找到该股票代码的数据，请检查后重试。")
                return

            # 检查 OHLC 列
            expected_columns = ['Open', 'High', 'Low', 'Close']
            missing_columns = [col for col in expected_columns if col not in data.columns]
            if missing_columns:
                data = data.rename(
                    columns={col.lower(): col for col in expected_columns if col.lower() in data.columns})
                missing_columns = [col for col in expected_columns if col not in data.columns]
                if missing_columns:
                    st.error(f"⚠️ 数据中缺少必要的 OHLC 列: {missing_columns}")
                    return

            # 数据清理
            data = data.dropna(subset=['Open', 'High', 'Low', 'Close'])
            if data.empty:
                st.warning("⚠️ 数据清理后没有有效数据，请选择其他股票代码或时间范围。")
                return

            # 获取股票基本信息
            try:
                if USE_TIINGO:
                    metadata = fetch_tiingo_metadata(ticker, TIINGO_API_KEY, TIINGO_AUTH_METHOD)
                    company_name = metadata.get('name', ticker.upper())
                    market_cap = metadata.get('marketCap', 0) / 1e9 if metadata.get('marketCap') else 0
                    high_52w = data['High'].max()
                    low_52w = data['Low'].min()
                    render_company_profile(metadata)
                else:
                    stock_info = yf.Ticker(ticker).info
                    company_name = stock_info.get('longName', ticker.upper())
                    market_cap = stock_info.get('marketCap', 0) / 1e9
                    high_52w = stock_info.get('fiftyTwoWeekHigh', data['High'].max())
                    low_52w = stock_info.get('fiftyTwoWeekLow', data['Low'].min())

                current_price = data['Close'].iloc[-1]
                previous_close = data['Close'].iloc[-2]
                price_change = current_price - previous_close
                price_change_percent = (price_change / previous_close) * 100
                volume = data['Volume'].iloc[-1] / 1e6

                # 价格信息显示
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"<h2>{company_name} ({ticker.upper()})</h2>", unsafe_allow_html=True)
                with col2:
                    price_color = "green" if price_change >= 0 else "red"
                    change_icon = "↑" if price_change >= 0 else "↓"
                    st.markdown(f"""
                    <div style='text-align: right'>
                        <h2 style='margin-bottom: 0px;'>${current_price:.2f}</h2>
                        <p style='color: {price_color}; font-size: 1.2rem; margin-top: 0px;'>
                            {change_icon} ${abs(price_change):.2f} ({price_change_percent:.2f}%)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                # 关键统计数据
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""<div class='stat-box'>
                        <h4>52周最高</h4>
                        <p>{high_52w:.2f}</p>
                    </div>""", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""<div class='stat-box'>
                        <h4>52周最低</h4>
                        <p>{low_52w:.2f}</p>
                    </div>""", unsafe_allow_html=True)
                with col3:
                    market_cap = get_yfinance_market_cap(ticker)
                    st.markdown(f"""<div class='stat-box'>
                            <h4>市值</h4>
                            <p>{market_cap}</p>
                        </div>""", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"""<div class='stat-box'>
                        <h4>成交量</h4>
                        <p>{volume:.1f}M</p>
                    </div>""", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"无法获取股票详细信息: {str(e)}")
                st.markdown(f"<h2>{ticker.upper()} - {selected_period}数据分析</h2>", unsafe_allow_html=True)

            # 新闻情绪快讯（仅 Tiingo 可用）
            if show_news and USE_TIINGO:
                try:
                    with st.spinner("正在加载新闻情绪数据..."):
                        news = fetch_tiingo_news(ticker, start_date, end_date, TIINGO_API_KEY, TIINGO_AUTH_METHOD)
                        if news:
                            render_news_section(news)
                        else:
                            st.info("ℹ️ 无近期新闻数据，可能需订阅 Tiingo 付费计划（https://www.tiingo.com/pricing）。")
                except Exception as e:
                    st.warning(f"无法加载新闻数据: {str(e)}")

            # 计算技术指标
            if show_ma:
                for period in ma_periods:
                    data[f'MA_{period}'] = data['Close'].rolling(window=period).mean()

            if show_rsi:
                delta = data['Close'].diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                rs = avg_gain / avg_loss.replace(0, np.nan)
                data['RSI'] = 100 - (100 / (1 + rs.fillna(0)))

            if show_macd:
                data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
                data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
                data['MACD'] = data['EMA12'] - data['EMA26']
                data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
                data['Histogram'] = data['MACD'] - data['Signal']

            # 确定子图数量
            n_rows = 1
            if show_volume:
                n_rows += 1
            if show_rsi:
                n_rows += 1
            if show_macd:
                n_rows += 1

            row_heights = [0.6]
            if show_volume:
                row_heights.append(0.1)
            if show_rsi:
                row_heights.append(0.15)
            if show_macd:
                row_heights.append(0.15)
            total_height = sum(row_heights)
            row_heights = [h / total_height for h in row_heights]

            # 创建子图
            fig = make_subplots(
                rows=n_rows,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=row_heights
            )

            # 设置图表样式
            if selected_style == "传统":
                increasing_color = 'red'
                decreasing_color = 'green'
                bg_color = 'white'
                grid_color = 'lightgrey'
                text_color = 'black'
                ma_colors = ['blue', 'orange', 'purple', 'brown', 'pink', 'cyan']
            elif selected_style == "现代科技":
                increasing_color = '#00FFAA'
                decreasing_color = '#FF5733'
                bg_color = '#111111'
                grid_color = '#333333'
                text_color = 'white'
                ma_colors = ['#00BFFF', '#FFAA00', '#AA00FF', '#FF00AA', '#00FFFF', '#FFFF00']
            elif selected_style == "专业交易":
                increasing_color = '#53B987'
                decreasing_color = '#EB4D5C'
                bg_color = '#131722'
                grid_color = '#2A2E39'
                text_color = '#D6D6D6'
                ma_colors = ['#5D7CC9', '#FFBF00', '#FF6363', '#4CAF50', '#9C27B0', '#00E5FF']
            elif selected_style == "暗黑模式":
                increasing_color = '#0ECB81'
                decreasing_color = '#F6465D'
                bg_color = '#0B0E11'
                grid_color = '#1C2030'
                text_color = '#EEF0F3'
                ma_colors = ['#7B68EE', '#FFD700', '#87CEEB', '#FF69B4', '#20B2AA', '#FF8C00']
            elif selected_style == "清新绿色":
                increasing_color = '#3D9970'
                decreasing_color = '#FF4136'
                bg_color = '#F5F8F5'
                grid_color = '#E0E5E0'
                text_color = '#2C3E50'
                ma_colors = ['#0074D9', '#FF851B', '#F012BE', '#2ECC40', '#B10DC9', '#AAAAAA']

            # 绘制 K 线图
            fig.add_trace(
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    increasing_line_color=increasing_color,
                    decreasing_line_color=decreasing_color,
                    name='K线'
                ),
                row=1, col=1
            )

            # 添加移动平均线
            if show_ma:
                for i, period in enumerate(ma_periods):
                    fig.add_trace(
                        go.Scatter(
                            x=data.index,
                            y=data[f'MA_{period}'],
                            line=dict(color=ma_colors[i % len(ma_colors)], width=1),
                            name=f'MA {period}'
                        ),
                        row=1, col=1
                    )

            # 添加成交量
            current_row = 2
            if show_volume:
                colors = [increasing_color if data['Close'].iloc[i] > data['Open'].iloc[i] else decreasing_color for i
                          in range(len(data))]
                fig.add_trace(
                    go.Bar(
                        x=data.index,
                        y=data['Volume'],
                        marker_color=colors,
                        name='成交量'
                    ),
                    row=current_row, col=1
                )
                current_row += 1

            # 添加 RSI
            if show_rsi:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['RSI'],
                        line=dict(color='#FF9900', width=1),
                        name='RSI'
                    ),
                    row=current_row, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=[70] * len(data.index),
                        line=dict(color='red', width=1, dash='dash'),
                        name='超买线'
                    ),
                    row=current_row, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=[30] * len(data.index),
                        line=dict(color='green', width=1, dash='dash'),
                        name='超卖线'
                    ),
                    row=current_row, col=1
                )
                current_row += 1

            # 添加 MACD
            if show_macd:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['MACD'],
                        line=dict(color='#FF9900', width=1),
                        name='MACD'
                    ),
                    row=current_row, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['Signal'],
                        line=dict(color='#00BFFF', width=1),
                        name='信号线'
                    ),
                    row=current_row, col=1
                )
                colors = [increasing_color if val > 0 else decreasing_color for val in data['Histogram']]
                fig.add_trace(
                    go.Bar(
                        x=data.index,
                        y=data['Histogram'],
                        marker_color=colors,
                        name='MACD柱状图'
                    ),
                    row=current_row, col=1
                )

            # 更新布局
            fig.update_layout(
                title=f"{ticker.upper()} - {selected_period}历史走势",
                xaxis_title="日期",
                yaxis_title="价格",
                xaxis_rangeslider_visible=False,
                template="plotly_white" if bg_color == 'white' else "plotly_dark",
                height=800,
                margin=dict(t=50, l=20, r=20, b=30),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                ),
                paper_bgcolor=bg_color,
                plot_bgcolor=bg_color,
                font=dict(color=text_color)
            )

            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=grid_color, zeroline=False)
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=grid_color, zeroline=False)

            # 显示图表
            st.plotly_chart(fig, use_container_width=True)

            # GPT 技术分析摘要（使用 OpenAI 密钥）
            def get_gpt_summary(prompt: str) -> str:
                from langchain.chat_models import ChatOpenAI
                try:
                    llm = ChatOpenAI(
                        model="gpt-4",
                        temperature=0.5,
                        openai_api_key=OPENAI_API_KEY
                    )
                    result = llm.invoke(prompt)
                    return result.content if hasattr(result, "content") else str(result)
                except Exception as e:
                    return f"⚠️ GPT 分析生成失败：{e}. 请检查 OPENAI_API_KEY 是否正确（https://platform.openai.com）。"

            def generate_tech_summary_gpt(ticker, current_price, ma20, ma50, rsi, macd, signal):
                ma20_str = f"{ma20:.2f}" if pd.notna(ma20) else "N/A"
                ma50_str = f"{ma50:.2f}" if pd.notna(ma50) else "N/A"
                rsi_str = f"{rsi:.2f}" if pd.notna(rsi) else "N/A"
                macd_str = f"{macd:.2f}" if pd.notna(macd) else "N/A"
                signal_str = f"{signal:.2f}" if pd.notna(signal) else "N/A"
                prompt = f"""
                你是一名金融分析师，请根据以下指标用中文写一段简洁易懂的技术分析摘要：
                股票代码：{ticker}
                当前价格：{current_price:.2f}
                MA20：{ma20_str}
                MA50：{ma50_str}
                RSI：{rsi_str}
                MACD：{macd_str}
                Signal：{signal_str}

                写作要求：
                趋势判断：用"上涨/下跌/横盘"等明确词汇，配合生活化比喻（如：像爬坡/下楼梯/平路散步）
                指标解读：每个指标都要用新手能理解的比喻说明（例如：均线好比...）
                操作建议：给出"现在适合/不适合"的明确建议，用红绿灯比喻：
                绿灯：可以考虑买入/加仓
                黄灯：建议观望等待
                红灯：考虑卖出/谨慎
                风险提示：必须包含"投资有风险"的提醒
                语言风格：像朋友聊天一样自然，避免专业术语，多用问句引发思考
                字数：250-300字，分3-4个自然段
                """
                return get_gpt_summary(prompt)

            # 显示 GPT 技术分析摘要
            if len(data) > 50:
                st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                st.markdown("<h3>📊 技术分析摘要</h3>", unsafe_allow_html=True)
                current_price = data['Close'].iloc[-1] if not data['Close'].empty else np.nan
                ma20 = data['MA_20'].iloc[-1] if show_ma and 'MA_20' in data else np.nan
                ma50 = data['MA_50'].iloc[-1] if show_ma and 'MA_50' in data else np.nan
                rsi = data['RSI'].iloc[-1] if show_rsi and 'RSI' in data else np.nan
                macd = data['MACD'].iloc[-1] if show_macd and 'MACD' in data else np.nan
                signal = data['Signal'].iloc[-1] if show_macd and 'Signal' in data else np.nan

                gpt_summary = generate_tech_summary_gpt(
                    ticker=ticker,
                    current_price=current_price,
                    ma20=ma20,
                    ma50=ma50,
                    rsi=rsi,
                    macd=macd,
                    signal=signal
                )
                st.markdown(gpt_summary)
                st.markdown("</div>", unsafe_allow_html=True)

                # 价格历史数据表格
                with st.expander("查看历史数据"):
                    st.dataframe(data.sort_index(ascending=False))

        except Exception as e:
            st.error(f"加载图表时出错: {str(e)}")
            st.write("💡 **提示**：请尝试以下操作：")
            st.write("- 检查股票代码是否正确（例如，'AAPL' 表示苹果公司）。")
            st.write("- 选择其他时间范围（如 '1个月' 或 '1年'）。")
            if not USE_TIINGO:
                st.write("- 若需使用 Tiingo 数据源，请在 .env 文件中添加 TIINGO_API_KEY（获取：https://www.tiingo.com）。")
            else:
                st.write("- 确保 Tiingo API 密钥有效，且未超出调用限制（检查 https://www.tiingo.com）。")
            st.write("调试信息（供高级用户参考）：")
            st.write(f"- 股票代码: {ticker}")
            st.write(f"- 时间范围: 从 {start_date} 到 {end_date}")
            st.write(f"- 数据是否为空: {'是' if data.empty else '否'}")
            if not data.empty:
                st.write(f"- 数据列名: {list(data.columns)}")
                st.write(f"- 数据行数: {len(data)}")
    else:
        # 首次加载界面
        st.markdown("""
        <div class='info-box'>
            <h3>👋 欢迎使用 InsightVest 股票可视化分析平台</h3>
            <p>使用左侧控制面板输入股票代码并选择您感兴趣的技术指标和时间范围，然后点击"开始分析"按钮查看详细图表和智能分析。</p>
            <p>支持的功能:</p>
            <ul>
                <li>高级 K 线图和蜡烛图展示</li>
                <li>多种移动平均线 (MA) 指标</li>
                <li>成交量分析</li>
                <li>RSI 超买超卖指标</li>
                <li>MACD 趋势指标</li>
                <li>AI 技术分析摘要（基于 GPT）</li>
                <li>新闻情绪快讯（启用 Tiingo API 后可用）</li>
                <li>多种可视化主题风格</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # 热门股票代码示例
        st.markdown("<h3 class='sub-header'>热门股票代码示例</h3>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("""
            **科技股**
            - AAPL (苹果)
            - MSFT (微软)
            - GOOGL (谷歌)
            - AMZN (亚马逊)
            """)
        with col2:
            st.markdown("""
            **金融股**
            - JPM (摩根大通)
            - BAC (美国银行)
            - V (Visa)
            - MA (万事达)
            """)
        with col3:
            st.markdown("""
            **消费股**
            - KO (可口可乐)
            - PG (宝洁)
            - MCD (麦当劳)
            - NKE (耐克)
            """)
        with col4:
            st.markdown("""
            **中国股票**
            - BABA (阿里巴巴)
            - PDD (拼多多)
            - NIO (蔚来)
            - BIDU (百度)
            """)