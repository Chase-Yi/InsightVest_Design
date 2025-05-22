
import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

def render_flashcard_module(json_path: str, title: str = "📘 Flashcard Deck"):
    with open(json_path, "r") as f:
        terms = json.load(f)

    st.session_state.setdefault("current_index", 0)
    st.session_state.setdefault("flipped", False)
    st.session_state.setdefault("favorites", set())
    st.session_state.setdefault("wrongs", set())

    idx = st.session_state.current_index
    term = terms[idx]["term"]
    definition = terms[idx]["definition"]
    total = len(terms)

    bg_base64 = "iVBORw0KGgoAAAANSUhEUgAAAmQAAAGTCAIAAAAJDJnXAAAAAXNSR0IArs4c6QAAAERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAA"

    st.markdown(f"""
    <style>
    .flashcard-container {{
        perspective: 1000px;
        width: 100%;
        max-width: 600px;
        margin: auto;
        margin-bottom: 2rem;
    }}
    .flashcard-inner {{
        position: relative;
        width: 100%;
        height: 240px;
        transition: transform 0.8s;
        transform-style: preserve-3d;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }}
    .flashcard-inner.flipped {{
        transform: rotateY(180deg);
    }}
    .flashcard-front, .flashcard-back {{
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 20px;
        backface-visibility: hidden;
        background: linear-gradient(135deg, rgba(10,20,40,0.6), rgba(10,20,40,0.85)),
                    url("data:image/png;base64,{bg_base64}") center/cover no-repeat;
        backdrop-filter: blur(4px);
        padding: 2rem;
        text-align: center;
        font-size: 1.6rem;
        font-weight: 600;
        color: #F8FAFC;
        box-shadow: inset 0 0 40px rgba(0,0,0,0.2);
    }}
    .flashcard-back {{
        transform: rotateY(180deg);
    }}
    .stats-bar {{
        text-align: center;
        margin-bottom: 1rem;
        color: #CBD5E1;
        font-size: 0.95rem;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"### {title}")
    st.markdown(f"<div class='stats-bar'>Card {idx + 1} / {total} | ⭐ {len(st.session_state.favorites)} | ❌ {len(st.session_state.wrongs)}</div>", unsafe_allow_html=True)

    flip_class = "flipped" if st.session_state.flipped else ""
    status = ""
    if idx in st.session_state.favorites:
        status += " ⭐"
    if idx in st.session_state.wrongs:
        status += " ❌"

    st.markdown(f"""
    <div class="flashcard-container">
      <div class="flashcard-inner {flip_class}">
        <div class="flashcard-front">
          <b>{term}</b>{status}
        </div>
        <div class="flashcard-back">
          {definition}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns([1, 1, 1, 1, 1])
    with cols[0]: st.button("⏪ Prev", on_click=lambda: update_index(-1, total))
    with cols[1]: st.button("🔁 Flip", on_click=flip_card)
    with cols[2]: st.button("⏩ Next", on_click=lambda: update_index(1, total))
    with cols[3]: st.button("⭐ Favorite", on_click=toggle_favorite)
    with cols[4]: st.button("❌ Mark Wrong", on_click=toggle_wrong)

    with st.expander("📌 My Favorites"):
        for i in sorted(st.session_state.favorites):
            st.write(f"• {terms[i]['term']}")
    with st.expander("❌ My Wrong Terms"):
        for i in sorted(st.session_state.wrongs):
            st.write(f"• {terms[i]['term']}")

    # === Dashboard Section ===
    render_progress_dashboard(
        learned=st.session_state.get("learned_count", 0),
        favorites=len(st.session_state.get("favorites", set())),
        wrongs=len(st.session_state.get("wrongs", set())),
        total=len(terms)
    )

def update_index(change, total):
    st.session_state.current_index = (st.session_state.current_index + change) % total
    st.session_state.flipped = False

def flip_card():
    st.session_state.flipped = not st.session_state.flipped

def toggle_favorite():
    idx = st.session_state.current_index
    if idx in st.session_state.favorites:
        st.session_state.favorites.remove(idx)
    else:
        st.session_state.favorites.add(idx)

def toggle_wrong():
    idx = st.session_state.current_index
    if idx in st.session_state.wrongs:
        st.session_state.wrongs.remove(idx)
    else:
        st.session_state.wrongs.add(idx)

def render_progress_dashboard(learned, favorites, wrongs, total):
    # Streamlit 深色背景适配的图表配色
    mpl.rcParams['axes.edgecolor'] = '#94A3B8'
    mpl.rcParams['axes.labelcolor'] = '#E2E8F0'
    mpl.rcParams['xtick.color'] = '#CBD5E1'
    mpl.rcParams['ytick.color'] = '#CBD5E1'
    mpl.rcParams['text.color'] = '#E2E8F0'
    mpl.rcParams['figure.facecolor'] = 'none'

    stats = pd.DataFrame({
        "Category": ["Learned", "Favorites", "Wrongs"],
        "Count": [learned, favorites, wrongs]
    })

    # 更紧凑的尺寸
    fig, ax = plt.subplots(figsize=(5, 2.5), facecolor='none')
    bars = ax.bar(stats["Category"], stats["Count"], width=0.4,
                  color=["#3B82F6", "#FACC15", "#F87171"], edgecolor='none')

    # 更合理的标题与间距
    ax.set_title("📊 Flashcard Progress", fontsize=13, pad=6)
    ax.set_ylim(0, max(total, stats["Count"].max() + 1))
    ax.set_facecolor("none")

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{int(height)}", xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, color="#E2E8F0")

    plt.tight_layout()
    st.pyplot(fig)
