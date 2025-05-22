# section2_upload_and_extract.py

import os
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

@st.cache_data
def extract_paragraphs_from_pdf(file_content, file_id):
    tmp_path = f"tmp_{file_id}.pdf"
    try:
        with open(tmp_path, "wb") as f:
            f.write(file_content)

        loader = PyPDFLoader(tmp_path)
        all_pages = loader.load()

        keywords = ["risk factors", "item 1a", "item 7", "management’s discussion", "footnotes", "note"]

        def filter_doc(doc):
            return any(kw.lower() in doc.page_content.lower() for kw in keywords)

        with ThreadPoolExecutor() as executor:
            filtered_results = list(executor.map(filter_doc, all_pages))
        filtered_docs = [doc for doc, keep in zip(all_pages, filtered_results) if keep]

        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)

        def split_doc(doc):
            try:
                return splitter.split_text(doc.page_content)
            except Exception as e:
                st.warning(f"Error splitting document: {str(e)}")
                return []

        with ThreadPoolExecutor() as executor:
            chunk_lists = list(executor.map(split_doc, filtered_docs))

        all_chunks = [chunk for chunk_list in chunk_lists for chunk in chunk_list if chunk]

    except Exception as e:
        st.error(f"❌ Error processing PDF: {str(e)}")
        return []
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                st.warning(f"Could not clean up temporary file: {str(e)}")

    return all_chunks


def handle_pdf_upload():
    uploaded_file = st.file_uploader("Upload PDF", type="pdf", key="file_upload_main")

    if "last_uploaded_file_id" not in st.session_state:
        st.session_state["last_uploaded_file_id"] = None

    if uploaded_file:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state["last_uploaded_file_id"] != file_id:
            with st.spinner("📖 Reading PDF..."):
                try:
                    paragraphs = extract_paragraphs_from_pdf(uploaded_file.getvalue(), file_id)
                    if not paragraphs:
                        st.error("❌ No paragraphs extracted.")
                    else:
                        st.session_state["paragraphs"] = paragraphs
                        st.session_state["last_uploaded_file_id"] = file_id
                        st.success(f"✅ Extracted {len(paragraphs)} useful paragraphs.")
                except Exception as e:
                    st.error(f"❌ Failed to extract: {str(e)}")
    else:
        st.session_state.pop("paragraphs", None)
        st.session_state.pop("last_uploaded_file_id", None)
