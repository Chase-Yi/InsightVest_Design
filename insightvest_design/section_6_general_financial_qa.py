import streamlit as st
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import uuid
import re

MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.3
MAX_TOKENS = 1024

# ✅ 通用金融问题 Prompt 模板
GENERAL_QA_TEMPLATES = {
    "📘 Plain English": """
You are a financial educator. Explain the following investment or finance-related question in clear, simple terms suitable for a beginner. Use analogies or examples when needed.

Question: {question}
""",
    "📊 Analytical": """
You are a professional financial analyst. Answer the following question using accurate terminology and examples. Structure your response logically and clearly.

Question: {question}
"""
}

@st.cache_data
def answer_general_financial_question(question, style):
    prompt = ChatPromptTemplate.from_template(GENERAL_QA_TEMPLATES[style])
    chain = prompt | ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE, max_tokens=MAX_TOKENS) | StrOutputParser()
    return chain.invoke({"question": question})

def highlight_keywords_general(answer):
    keywords = set(word.strip(".,()") for word in answer.split() if len(word) > 6)
    for kw in sorted(keywords, key=len, reverse=True):
        answer = re.sub(rf"(?i)\b({re.escape(kw)})\b", r'<span style="background-color:#ffcccc"><b>\1</b></span>', answer)
    return answer

def render_general_financial_qa():
    st.markdown("""
    <div style="padding:1.5rem;background:linear-gradient(135deg,#0D1117,#1F2937);border-radius:12px;margin-bottom:1rem;">
        <h2 style="color:#fbbf24;font-weight:bold;margin-bottom:0.8rem;">📚 General Financial Q&A</h2>
        <p style="color:#f3f4f6;">Example: What is a high PEG ratio? What does ROE mean? How is Free Cash Flow calculated?</p>
    </div>
    """, unsafe_allow_html=True)

    question = st.text_area(
        "💬 Your Question",
        placeholder="Ask any question about finance, valuation, accounting, or investment...",
        height=100,
        key="general_qa_input"
    )

    style = st.selectbox("🎯 Choose explanation style:", list(GENERAL_QA_TEMPLATES.keys()), index=0)

    if "general_qa_history" not in st.session_state:
        st.session_state["general_qa_history"] = []

    # 金色按钮样式
    submit_button = st.markdown("""
    <style>
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #FFD700, #FFA500);
        color: black;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("💡 Submit Question", key="ask_general"):
        if not question:
            st.warning("Please enter a question.")
            return

        with st.spinner("Thinking..."):
            try:
                answer = answer_general_financial_question(question, style)
                answer_id = str(uuid.uuid4())[:8]
                st.session_state["last_general_answer"] = {
                    "id": answer_id,
                    "question": question,
                    "style": style,
                    "answer": answer
                }
                st.session_state["general_qa_history"].insert(0, st.session_state["last_general_answer"])
            except Exception as e:
                st.error(f"❌ Failed: {str(e)}")
                return

    if "last_general_answer" in st.session_state:
        result = st.session_state["last_general_answer"]
        st.markdown("### 📘 GPT Answer")

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**📝 Question:** {result['question']}")
            st.markdown(f"**🎯 Style:** {result['style']}")
        with col2:
            if st.button("⭐ Save to Favorites", key="save_" + result["id"]):
                if "general_favorites" not in st.session_state:
                    st.session_state["general_favorites"] = []
                st.session_state["general_favorites"].append(result)
                st.success("Saved!")

        highlighted = highlight_keywords_general(result["answer"])
        st.markdown(f"<div style='line-height:1.7'>{highlighted}</div>", unsafe_allow_html=True)

    if st.toggle("📂 Show Past Questions", value=False):
        for idx, qa in enumerate(st.session_state["general_qa_history"][:3]):
            with st.expander(f"📌 {qa['question']} — {qa['style']}"):
                st.markdown(f"<div style='line-height:1.6'>{highlight_keywords_general(qa['answer'])}</div>", unsafe_allow_html=True)

    if "general_favorites" in st.session_state and st.toggle("⭐ View Favorites", value=False):
        for fav in st.session_state["general_favorites"]:
            with st.expander(f"⭐ {fav['question']} — {fav['style']}"):
                st.markdown(f"<div style='line-height:1.6'>{highlight_keywords_general(fav['answer'])}</div>", unsafe_allow_html=True)

