from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import os
from dotenv import load_dotenv
load_dotenv()

# === Step 1: 文本切分器 ===
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

# === Step 2: Embedding 模型初始化 ===
embedding_model = OpenAIEmbeddings()

# === 构建向量数据库函数 ===
def build_vectorstore_from_pdf(pdf_path: str, save_path: str = None) -> FAISS:
    """读取PDF，分块并存入FAISS向量数据库"""
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    chunks = text_splitter.split_documents(pages)

    vectorstore = FAISS.from_documents(chunks, embedding_model)

    if save_path:
        vectorstore.save_local(save_path)
        print(f"✅ Vectorstore saved to {save_path}")

    return vectorstore

# === 加载向量数据库函数 ===
def load_vectorstore(path: str) -> FAISS:
    """从磁盘加载本地保存的向量数据库"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Vectorstore not found at {path}")
    return FAISS.load_local(path, embeddings=embedding_model)

# === 用于测试的脚本入口 ===
if __name__ == "__main__":
    vs = build_vectorstore_from_pdf("sample.pdf", save_path="data/vector_store")
