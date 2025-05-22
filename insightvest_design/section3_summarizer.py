# section3_summarizer.py

import streamlit as st
import bleach
import json
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import time

# === 常量定义 ===
MAX_PARAGRAPHS = 30
MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.1
BEGINNER_TOKENS = 512
PROFESSIONAL_TOKENS = 1024

# === 提示词模板 ===
BEGINNER_PROMPT = """
You are a financial analyst creating a summary for beginner investors with no financial background.

Summarize the company's 10-K report in 300-500 words using simple, clear language. Avoid technical jargon and explain any necessary terms in plain English. Structure the summary as follows:
1. **What the Company Does**
2. **Key Financial Results**
3. **Management's Outlook**
4. **Why It Matters**
Content:
{content}
"""

PROFESSIONAL_PROMPT = """
You are a senior equity research analyst at a top investment firm.

Summarize the company's 10-K report in 500-700 words using concise, analytical language suitable for professional investors. Structure the summary as follows:
1. **Business Model and Operations**
2. **Segment Performance**
3. **Key Risks and Opportunities**
4. **Forward-looking Commentary**
5. **Industry Context**
Content:
{content}
"""

# === 辅助函数 ===
def safe_markdown(text):
    cleaned = bleach.clean(text, tags=['div', 'h2', 'h4'], attributes={'div': ['style', 'class'], 'h2': ['style', 'class'], 'h4': ['style', 'class']})
    st.markdown(cleaned, unsafe_allow_html=True)

def filter_relevant_paragraphs(paragraphs):
    keywords = ["management's discussion", "risk factors", "financial condition"]
    return [p for p in paragraphs if any(kw.lower() in p.lower() for kw in keywords)][:MAX_PARAGRAPHS]

@st.cache_data
def generate_summary(paragraphs, summary_mode):
    prompt = ChatPromptTemplate.from_template(
        BEGINNER_PROMPT if summary_mode == "Beginner-friendly Summary" else PROFESSIONAL_PROMPT
    )
    max_tokens = BEGINNER_TOKENS if summary_mode == "Beginner-friendly Summary" else PROFESSIONAL_TOKENS
    full_text = "\n".join(paragraphs)
    chain = prompt | ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE, max_tokens=max_tokens) | StrOutputParser()
    return chain.invoke({"content": full_text})

def render_summary_ui():
    st.markdown("""
    <style>
    .summary-selectbox label {
        color: #ffffff !important;
        font-size: 18px;
        font-weight: bold;
    }
    div[data-baseweb="select"] > div {
        background-color: #1f2937;
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='summary-selectbox'><label>🧠 Choose Summary Style</label></div>", unsafe_allow_html=True)
    summary_mode = st.selectbox(
        label="Choose Summary Style",
        options=["🧠 Beginner-friendly Summary", "📊 Professional Summary"],
        label_visibility="collapsed",
        key="summary_style_select"
    )

    paragraphs = st.session_state.get("paragraphs", [])
    if not paragraphs:
        st.warning("⚠️ No paragraphs found. Please upload a 10-K report first.")
        return

    target_paras = filter_relevant_paragraphs(paragraphs)

    if st.button("📝 Generate Summary"):
        with st.spinner("Generating summary..."):
            try:
                summary_text = generate_summary(target_paras, summary_mode)
                st.session_state["report_summary"] = summary_text
            except Exception as e:
                st.error(f"Failed to generate summary: {str(e)}")

    if "report_summary" in st.session_state:
        safe_markdown("<h4 class='summary-title'>📌 Summary Card</h4>")
        safe_markdown(f"<div class='summary-text'>{st.session_state['report_summary']}</div>")

        if "suggest a chart" in st.session_state["report_summary"].lower():
            chart_data = {
                "type": "line",
                "data": {
                    "labels": ["2022", "2023", "2024"],
                    "datasets": [{
                        "label": "Revenue ($B)",
                        "data": [100, 110, 120],
                        "borderColor": "#4CAF50",
                        "backgroundColor": "rgba(76, 175, 80, 0.2)"
                    }]
                },
                "options": {
                    "title": {"display": True, "text": "Revenue Trend"},
                    "scales": {"y": {"beginAtZero": False}}
                }
            }
            st.markdown("### Suggested Chart")
            st.write(f"```chartjs\n{json.dumps(chart_data)}\n```")

        summary = st.session_state["report_summary"]
        st.download_button("⬇️ Download Summary (Markdown)", summary, file_name="summary.md")
        st.download_button("⬇️ Download Summary (TXT)", summary, file_name="summary.txt")

