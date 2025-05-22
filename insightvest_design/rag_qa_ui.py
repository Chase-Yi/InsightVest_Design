import streamlit as st
from rag_vectorstore import load_vectorstore
from rag_chain import build_rag_chain

import streamlit as st
from rag_vectorstore import load_vectorstore
from rag_chain import build_rag_chain

def render_rag_ui(default_vectorstore="mycompany.faiss"):
    st.markdown("""
    <div style="padding:1.5rem;background:linear-gradient(135deg,#0D1117,#1F2937);border-radius:12px;margin-bottom:1.5rem;">
        <h2 style="color:#fbbf24;font-weight:bold;">📊 Ask Document-Specific Risk Questions</h2>
        <p style="color:#f3f4f6;">Example: What are the main financial risks? What did the company disclose about liquidity?</p>
    </div>
    """, unsafe_allow_html=True)

    # === 🔍 输入 Vectorstore 路径 ===
    vectorstore_name = st.text_input(
        "📂 Enter Vectorstore Name",
        value=default_vectorstore,
        help="This should match your uploaded document's vectorstore path."
    )

    # === ✨ 金色按钮样式（仅设置一次） ===
    st.markdown("""
    <style>
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #FFD700, #FFA500);
        color: black;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # === 📦 加载向量库按钮 ===
    if st.button("📦 Load Knowledge Base", key="load_rag_vectorstore"):
        try:
            vectorstore = load_vectorstore(vectorstore_name)
            rag_chain = build_rag_chain(vectorstore)
            st.session_state["rag_vectorstore"] = vectorstore
            st.session_state["rag_chain"] = rag_chain
            st.success("✅ Vectorstore loaded and RAG chain initialized.")
        except Exception as e:
            st.error(f"❌ Failed to load vectorstore: {e}")

    # === 💬 提问区域 ===
    if "rag_chain" in st.session_state:
        st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

        risk_question = st.text_area(
            "💬 Enter your risk-related question",
            placeholder="e.g. What operational risks are mentioned in the filing?",
            height=120,
            key="rag_risk_qa"
        )

        if st.button("💡 Submit Risk Question", key="submit_rag_risk_qa"):
            if not risk_question.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("🔍 Searching vector database..."):
                    try:
                        answer = st.session_state["rag_chain"].run(risk_question)
                        st.markdown("### 📌 GPT Response")
                        st.markdown(f"<div style='line-height:1.6'>{answer}</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"❌ Failed to generate response: {e}")
    else:
        st.info("ℹ️ Please load a vectorstore before asking a question.")


