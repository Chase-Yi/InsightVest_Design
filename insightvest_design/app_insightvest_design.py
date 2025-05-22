'''
streamlit run insightvest_design/app_insightvest_design.py
'''

# main app
import os
import time

import streamlit as st
st.set_page_config(layout="wide")

from dotenv import load_dotenv
from pathlib import Path
import base64
import pandas as pd
import numpy as np
import plotly.express as px

from fancy_stock_chart_tiingo import render_fancy_stock_chart
from section3_summarizer import render_summary_ui
from section2_upload_pdf import handle_pdf_upload
from section_6_general_financial_qa import render_general_financial_qa
from rag_qa_ui import render_rag_ui
from stock_portfolio import render_portfolio_analyzer
from financial_cards_edu import render_flashcard_module
from prompt_registry import PROMPT_REGISTRY  # 确保已加载你的 prompt 库
from financial_metric import render_tiingo_statements_trend_cards

import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === 插入动态图标横条（必须放函数外顶层） ===
st.markdown("""
<style>
.ticker-container {
    width: 100%;
    background-color: #0A0F1C;
    padding: 6px 0;
    overflow: hidden;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}
.ticker-content {
    display: inline-block;
    white-space: nowrap;
    animation: scroll 30s linear infinite;
}
.ticker-content img {
    height: 28px;
    margin: 0 18px;
    vertical-align: middle;
    opacity: 0.85;
}
@keyframes scroll {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
</style>

<!-- 滚动公司图标 -->
<div class="ticker-container">
    <div class="ticker-content">
        <img src="https://logo.clearbit.com/apple.com">
        <img src="https://logo.clearbit.com/microsoft.com">
        <img src="https://logo.clearbit.com/amazon.com">
        <img src="https://logo.clearbit.com/meta.com">
        <img src="https://logo.clearbit.com/tesla.com">
        <img src="https://logo.clearbit.com/nvidia.com">
        <img src="https://logo.clearbit.com/alphabet.com">
        <img src="https://logo.clearbit.com/visa.com">
        <img src="https://logo.clearbit.com/jpmorganchase.com">
        <img src="https://logo.clearbit.com/berkshirehathaway.com">
        <img src="https://logo.clearbit.com/adobe.com">
        <img src="https://logo.clearbit.com/netflix.com">
        <img src="https://logo.clearbit.com/intel.com">
        <img src="https://logo.clearbit.com/qualcomm.com">
        <img src="https://logo.clearbit.com/paypal.com">
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: rgba(10,15,28,0.8); padding: 12px 24px; border-bottom: 1px solid rgba(255,255,255,0.05);">
    <h2 style='margin: 0; font-weight: 700; font-size: 1.5rem; color: #D4AF37;'>
        🚀 InsightVest — AI Financial Companion for Everyone
    </h2>
</div>
""", unsafe_allow_html=True)



# 插入全局样式与顶部图片栏（简约横条风格）
st.markdown("""
<style>
/* 全局背景与排版风格 */
html, body {
    margin: 0 !important;
    padding: 0 !important;
    background-color: #0A0F1C !important;
    overflow-x: hidden;
}
.stApp {
    margin: 0 !important;
    padding: 0 !important;
    background: linear-gradient(135deg, #0A0F1C, #121926, #1F2937) !important;
}

/* 标题渐变铜金 */
h1, h2, h3 {
    background: linear-gradient(90deg, #D4AF37, #C49E57);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
}

/* 文本颜色 */
p, span, label, div {
    color: #E0E0E0 !important;
}

/* 按钮样式 */
.stButton > button {
    background: linear-gradient(90deg, #D3A373, #A87738);
    color: #111827;
    font-weight: 600;
    border-radius: 10px;
    padding: 0.6rem 1.2rem;
    box-shadow: 0 4px 16px rgba(168, 119, 56, 0.2);
    transition: all 0.25s ease-in-out;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #D9B27E, #A87738);
    box-shadow: 0 6px 24px rgba(168, 119, 56, 0.35);
}

/* 侧边栏 */
section[data-testid="stSidebar"] {
    background: #0D1117 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}
.sidebar-title {
    font-size: 1.3rem;
    font-weight: 700;
    background: linear-gradient(90deg, #D3A373, #A87738);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* 警示框 */
.stAlert {
    background-color: rgba(255, 255, 255, 0.05);
    border-left: 4px solid #A87738;
    color: #F3F4F6;
}

/* 单选按钮 hover */
div[role="radiogroup"] label:hover {
    background-color: rgba(211, 163, 115, 0.2) !important;
    color: #FFFFFF !important;
}

/* 修复 ticker 顶部遮挡问题 */
.block-container {
    padding-top: 65px !important;
    max-width: 100% !important;
}
</style>
""", unsafe_allow_html=True)


# --- Embed Logo in Sidebar ---
logo_path = Path("insightvest_design/logo.png")
if logo_path.exists():
    logo_base64 = base64.b64encode(logo_path.read_bytes()).decode()
    logo_html = f"""
    <div style='text-align: center; margin-bottom: 1.5rem;'>
        <img src="data:image/png;base64,{logo_base64}" style="width: 130px; border-radius: 10px;" />
    </div>
    """
    st.sidebar.markdown(logo_html, unsafe_allow_html=True)
else:
    # Fallback if logo not found
    st.sidebar.markdown('<div class="sidebar-title">InsightVest</div>', unsafe_allow_html=True)

# --- Navigation State ---
# --- Navigation State ---
def show_home():
    st.markdown("""
        <style>
            .home-header {
                text-align: center;
                font-size: 2.5rem;
                font-weight: 800;
                background: linear-gradient(90deg, #D4AF37,#C49E57);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }
            .subtext {
                text-align: center;
                font-size: 1.1rem;
                opacity: 0.85;
                margin-bottom: 2rem;
            }
            .card-button {
                width: 100%; 
                padding: 1rem; 
                font-weight: bold; 
                font-size: 1rem; 
                background: linear-gradient(90deg, #D3A373, #A87738); 
                color: black; 
                border: none; 
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(168, 119, 56, 0.4);
                transition: all 0.3s ease;
            }
            .card-button:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 20px rgba(168, 119, 56, 0.6);
            }
            .dynamic-bg {
                background: radial-gradient(circle at top, #1F2937 0%, #0A0F1C 100%);
                padding: 3rem 2rem;
                border-radius: 16px;
                box-shadow: inset 0 0 40px rgba(255, 255, 255, 0.05);
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="dynamic-bg">
            <h1 class="home-header">🚀 Welcome to InsightVest</h1>
            <p class="subtext">Your AI-powered companion for financial insights</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄 Financial Analysis", key="nav_analysis"):
            st.session_state["section_selected"] = "analysis"
            st.rerun()
    with col2:
        if st.button("📈 Market Insights", key="nav_insights"):
            st.session_state["section_selected"] = "insights"
            st.rerun()
    with col3:
        if st.button("🎓 Financial Education", key="nav_education"):
            st.session_state["section_selected"] = "education"
            st.rerun()

    st.markdown("---")
    st.subheader("🔥 Top Movers Today")
    st.markdown("- **AAPL** +2.35% | **TSLA** +1.92% | **NVDA** -0.88%")

    st.subheader("🗞️ Market Headlines")
    st.info("US stocks open higher as inflation eases. Tech leads gains. Fed likely to pause in upcoming meeting.")

    st.markdown("---")
    st.markdown("<footer style='text-align: center; font-size: 0.85rem; opacity: 0.7;'>© 2025 InsightVest Inc. | Built with ❤️ using Streamlit</footer>", unsafe_allow_html=True)

def show_analysis():
    st.header("📄 AI-Powered Financial Analysis")
    st.info("Upload a financial report or select a company to start analysis.")
    if st.button("🔙 Back to Home", key="back_analysis"):
        st.session_state["section_selected"] = None
        st.rerun()
    # Analysis logic to be added here

def show_insights():
    st.header("📈 Market Insights")
    if st.button("🔙 Back to Home", key="back_insights"):
        st.session_state["section_selected"] = None
        st.rerun()

def show_education():
    st.markdown("## 📚 Financial Education: Learn by Flashcards")

    # === 左侧栏：选择主题 ===
    category = st.sidebar.radio(
        "📖 Choose a Term Category",
        options=[
            "📘 Stock Market Basics",
            "🏦 Risk Management Terms",
            "🧠 AI & Responsible Compliance",
            "💼 Regulatory & Legal",
            "🧪 Risk Modeling Techniques"
        ]
    )

    # === 预定义主题和路径映射（建议统一放到 /mnt/data/flashcard_sets）===
    base_path = r"insightvest_design/financial_card_data"
    category_file_map = {
        "📘 Stock Market Basics": "stock_market_basics.json",
        "🏦 Risk Management Terms": "risk_terms.json",
        "🧠 AI & Responsible Compliance": "ai_terms.json",
        "💼 Regulatory & Legal": "reg_terms.json",
        "🧪 Risk Modeling Techniques": "model_terms.json"
    }

    selected_file = os.path.join(base_path, category_file_map[category])

    # === 加载对应卡片模块 ===
    render_flashcard_module(json_path=selected_file, title=category)
    if st.button("🔙 Back to Home", key="back_analysis"):
        st.session_state["section_selected"] = None
        st.rerun()



# --- Sample Data Generator for Risk Trend Visuals ---
def create_sample_data():
    """Generate sample data for multiple-year risk analysis."""
    years = ["2021", "2022", "2023", "2024", "2025"]
    risk_types = ["Financial", "Operational", "Regulatory", "Cybersecurity", "Market", "Strategic", "Reputational"]

    dfs_by_year = {}
    for year in years:
        n_samples = np.random.randint(15, 30)
        data = {
            "Paragraph": [f"Sample paragraph {i} about risks for {year}..." for i in range(n_samples)],
            "risk_type_1": np.random.choice(risk_types, size=n_samples, p=[0.25, 0.2, 0.15, 0.15, 0.1, 0.1, 0.05]),
            "severity_1": np.random.choice(["1", "2", "3", "4", "5"], size=n_samples),
            "excerpt": [f"Key risk excerpt {i} for {year}..." for i in range(n_samples)]
        }
        df = pd.DataFrame(data)
        dfs_by_year[year] = df
    return dfs_by_year

if "section_selected" not in st.session_state:
    st.session_state["section_selected"] = None
# === Financial Analysis Section ===
if st.session_state["section_selected"] == "analysis":
    show_analysis()

    # Create left and right columns for main content
    left_col, right_col = st.columns([2, 1])

    # Left Column: Core Analysis Features
    with left_col:
        # PDF Upload
        with st.container():
            st.markdown('<div class="module-container">', unsafe_allow_html=True)
            st.subheader("📄 Upload Financial Document")

            # 上传逻辑：调用 handle_pdf_upload()
            handle_pdf_upload()

            # 展示上传结果
            if "last_uploaded_file_id" in st.session_state and st.session_state.get("last_uploaded_file_id"):
                uploaded_file = st.session_state.get("uploaded_file")
                if uploaded_file:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**File name:** {uploaded_file['name']}")
                    with col2:
                        file_size = round(uploaded_file['size'] / 1024, 2)
                        st.markdown(f"**File size:** {file_size} KB")

                    # ✅ Process 按钮 + 提取段落 + 设置状态
                    if st.button("Process Document", key="process_doc"):
                        with st.spinner("📊 Processing document..."):
                            progress_bar = st.progress(0)
                            for i in range(100):
                                time.sleep(0.01)
                                progress_bar.progress(i + 1)

                            # 检查是否已有提取结果
                            paragraphs = st.session_state.get("paragraphs", [])
                            if paragraphs and len(paragraphs) > 0:
                                st.session_state["doc_processed"] = True
                                st.success("✅ Document processed! Summary is now available below.")
                            else:
                                st.session_state["doc_processed"] = False
                                st.error("❌ No paragraphs extracted. Please upload a valid 10-K document.")

            st.markdown('</div>', unsafe_allow_html=True)

        # === 📝 Section 2: Summary Generator ===
        with st.container():
            st.markdown('<div class="module-container">', unsafe_allow_html=True)
            st.subheader("📝 Summary Generator")

            if st.session_state.get("doc_processed", True):
                render_summary_ui()
            else:
                st.info("📥 Please upload and process a document first.")

            st.markdown('</div>', unsafe_allow_html=True)

        st.subheader("🔍Choose a professional prompt template for analysis")

        all_prompt_ids = list(PROMPT_REGISTRY.keys())
        selected_prompt_ids = st.multiselect(
            "🧠 Choose Prompts for GPT Analysis",
            options=all_prompt_ids,
            default=[],
            key="selected_prompt_ids"
        )
        # 展示每个选中 Prompt 的说明（来自 PROMPT_REGISTRY）
        if selected_prompt_ids:
            st.markdown("---")
            st.markdown("### 🧾 Selected Prompt Descriptions")
            for pid in selected_prompt_ids:
                prompt_meta = PROMPT_REGISTRY.get(pid, {})
                description = prompt_meta.get("description", "No description available.")
                template = prompt_meta.get("template", "[No template provided.]")

                st.markdown(f"""
                <div style='margin-bottom: 1.5rem; padding: 1rem; background-color: #111827; border-left: 4px solid #f97316;'>
                    <h4 style='color:#facc15;'>🟠 {pid}</h4>
                    <p style='color:#9ca3af;'><b>Description:</b> {description}</p>
                    <p style='color:#d1d5db;'><b>Template:</b></p>
                    <pre style='background-color: #1f2937; color: #d1d5db; padding: 0.75rem; border-radius: 5px;'>{template}</pre>
                </div>
                """, unsafe_allow_html=True)

        ## Run GPT Analysis from selected prompt IDs
        if st.button("🔄 Run GPT Analysis", key="run_gpt_analysis"):

            # 传入你页面中用户选中的 prompt ID 列表
            selected_prompt_ids = st.session_state.get("selected_prompt_ids", [])

            if not selected_prompt_ids:
                st.warning("⚠️ Please select at least one prompt.")
            elif "paragraphs" not in st.session_state:
                st.warning("📥 Please upload and process a 10-K document first.")
            else:
                st.markdown("Enhanced Prompt Analysis")

        # Risk Trend Visuals with Sample Data
        with st.container():
            st.markdown('<div class="module-container">', unsafe_allow_html=True)
            st.subheader("📊 Risk Trend Visuals")

            # Option to use sample data
            use_sample_data = st.checkbox("Use Sample Data for Demonstration", value=True,
                                        help="Check to use pre-loaded sample data if you haven't uploaded a document.")

            if use_sample_data:
                st.info("Using sample risk data for demonstration.")

                # Generate sample data
                dfs_by_year = create_sample_data()

                # Display summary metrics
                st.markdown("### Risk Analysis Overview")
                metrics_cols = st.columns(len(dfs_by_year))
                for i, (year, df) in enumerate(sorted(dfs_by_year.items())):
                    with metrics_cols[i]:
                        total_risks = len(df)
                        avg_severity = pd.to_numeric(df["severity_1"], errors="coerce").mean()
                        top_risk = df["risk_type_1"].value_counts().idxmax() if not df.empty else "N/A"
                        st.metric(
                            label=f"📅 {year}",
                            value=f"{total_risks} Risks",
                            delta=f"{avg_severity:.1f} Avg Severity"
                        )
                        st.caption(f"Top Risk: {top_risk}")

                # Risk Trend Chart using Plotly for interactivity
                st.markdown("### Risk Type Trends Over Years")
                risk_types = sorted(
                    set(risk_type for df in dfs_by_year.values() for risk_type in df["risk_type_1"].unique()))
                selected_risks = st.multiselect(
                    "Filter Risk Types:",
                    options=risk_types,
                    default=risk_types[:3] if len(risk_types) >= 3 else risk_types
                )

                if selected_risks:
                    records = []
                    for year, df in dfs_by_year.items():
                        counts = df["risk_type_1"].value_counts()
                        for risk_type, count in counts.items():
                            if risk_type in selected_risks:
                                records.append({
                                    "Year": str(year),
                                    "Risk Type": risk_type,
                                    "Count": count
                                })

                    trend_df = pd.DataFrame(records)
                    if not trend_df.empty:
                        fig = px.line(
                            trend_df,
                            x="Year",
                            y="Count",
                            color="Risk Type",
                            markers=True,
                            title="Risk Type Trends Over Years",
                            color_discrete_sequence=px.colors.sequential.Teal
                        )
                        fig.update_layout(
                            plot_bgcolor='rgba(28, 39, 60, 0.5)',
                            paper_bgcolor='rgba(28, 39, 60, 0.5)',
                            font=dict(color="white"),
                            xaxis=dict(
                                tickcolor="white",  # Correct property for x-axis tick color
                                gridcolor="rgba(255, 255, 255, 0.1)",
                                linecolor="white",  # Correct property for axis line color
                                zerolinecolor="rgba(255, 255, 255, 0.1)"
                            ),
                            yaxis=dict(
                                tickcolor="white",  # Correct property for y-axis tick color
                                gridcolor="rgba(255, 255, 255, 0.1)",
                                linecolor="white",  # Correct property for axis line color
                                zerolinecolor="rgba(255, 255, 255, 0.1)"
                            ),
                            title_font=dict(size=18, color="white"),
                            margin=dict(l=40, r=40, t=60, b=40)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # Trend Analysis
                        if len(dfs_by_year) > 1:
                            st.markdown("### Trend Analysis")
                            trend_data = []
                            for risk_type in selected_risks:
                                yearly_counts = {}
                                for year, df in sorted(dfs_by_year.items()):
                                    count = df[df["risk_type_1"] == risk_type].shape[0]
                                    yearly_counts[year] = count
                                if len(yearly_counts) > 1:
                                    years = sorted(yearly_counts.keys())
                                    changes = []
                                    for i in range(1, len(years)):
                                        prev_count = yearly_counts[years[i - 1]]
                                        curr_count = yearly_counts[years[i]]
                                        if prev_count > 0:
                                            pct_change = (curr_count - prev_count) / prev_count * 100
                                            changes.append((years[i - 1], years[i], pct_change))
                                    trend_data.append({
                                        "risk_type": risk_type,
                                        "changes": changes
                                    })

                            for data in trend_data:
                                risk_type = data["risk_type"]
                                changes = data["changes"]
                                if changes:
                                    overall_change = sum(pct for _, _, pct in changes) / len(changes)
                                    trend_emoji = "📈" if overall_change > 10 else "📉" if overall_change < -10 else "➡️"
                                    st.markdown(f"**{trend_emoji} {risk_type} Risk:**")
                                    for prev_year, curr_year, pct_change in changes:
                                        direction = "increased" if pct_change > 0 else "decreased"
                                        st.markdown(
                                            f"• {prev_year} → {curr_year}: {direction} by "
                                            f"{'**' if abs(pct_change) > 25 else ''}"
                                            f"{abs(pct_change):.1f}%"
                                            f"{'**' if abs(pct_change) > 25 else ''}"
                                        )
                else:
                    st.warning("Please select at least one risk type to display trends.")
            else:
                if st.session_state.get("doc_processed", False):
                    st.info(
                        "Sample data is disabled. Risk trend analysis will be available once multiple documents are processed.")
                else:
                    st.info(
                        "Please upload and process a document first to enable risk trend analysis, or enable sample data.")
            st.markdown('</div>', unsafe_allow_html=True)

    # Right Column: Q&A and Auxiliary Tools
    with right_col:
        st.markdown('<div class="right-panel">', unsafe_allow_html=True)
        # === Stock Chart Module ===
        st.subheader("Fancy K-Line Chart Viewer")
        ticker = st.text_input("Enter Stock Ticker", value="AAPL", key="candlestick_input")

        if st.button("🔍 Load Candlestick Chart"):
            try:
                # Set date range
                end_date = datetime.today()
                start_date = end_date - timedelta(days=90)

                # Download data
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)

                # Flatten MultiIndex columns if necessary
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                # Validate and clean data
                expected_columns = ['Open', 'High', 'Low', 'Close']
                df.index = pd.to_datetime(df.index)
                df[expected_columns] = df[expected_columns].apply(pd.to_numeric, errors='coerce')
                df = df.dropna(subset=expected_columns)

                if df.empty:
                    st.warning("⚠️ No valid candlestick data found.")
                else:
                    # Build fancy chart
                    fig = go.Figure(data=[go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        increasing_line_color="#00FFB2",  # Neon Green
                        decreasing_line_color="#FF4C4C",  # Bright Red
                        line_width=2
                    )])

                    fig.update_layout(
                        title=f"{ticker.upper()} — Last 3 Months",
                        xaxis_title="Date",
                        yaxis_title="Price",
                        template="plotly_dark",
                        height=500,
                        font=dict(
                            family="Inter, sans-serif",
                            size=14,
                            color="white"
                        ),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(15, 23, 42, 0.9)",
                        xaxis=dict(
                            rangeslider=dict(visible=False),
                            showgrid=True,
                            gridcolor="rgba(255,255,255,0.1)",
                            zeroline=False,
                            showspikes=True,
                            spikecolor="rgba(255,255,255,0.5)",
                            spikemode="across",
                            spikesnap="cursor"
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridcolor="rgba(255,255,255,0.1)",
                            zeroline=False,
                            showspikes=True,
                            spikecolor="rgba(255,255,255,0.5)",
                            spikemode="across",
                            spikesnap="cursor"
                        ),
                        hovermode="x unified",
                        margin=dict(t=40, l=20, r=20, b=30),
                        showlegend=False
                    )

                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"❌ Error fetching or rendering chart: {str(e)}")


        # Ask General Financial Questions
        render_general_financial_qa()

        # RAG Risk QA
        render_rag_ui(default_vectorstore="mycompany.faiss")

        #finanacial metrics
        render_tiingo_statements_trend_cards()

# === Market Insights Section ===

elif st.session_state["section_selected"] == "insights":
    show_insights()
    section_options = ["📈 股票图表分析", "📊 模拟组合分析器"]
    section = st.sidebar.radio("选择功能", section_options, index=0, key="main_nav")

    if section == "📈 股票图表分析":
        render_fancy_stock_chart()
    elif section == "📊 模拟组合分析器":
        render_portfolio_analyzer()


# === Financial Education Section ===
elif st.session_state["section_selected"] == "education":
    show_education()

else:
    show_home()
