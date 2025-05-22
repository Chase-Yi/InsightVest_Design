from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores.base import VectorStoreRetriever

# === 🔧 构造 RAG 问答链 ===
def build_rag_chain(vectorstore: VectorStoreRetriever, temperature: float = 0.2):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=temperature)

    # Prompt 模板（可根据任务自定义）
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are a senior financial risk analyst.
Use the following context (10-K disclosure) to answer the question.

Context:
{context}

Question:
{question}

Answer:
- Be concise but precise
- Highlight key risk terms
- If relevant, reference specific regulatory issues (e.g., SOX, SEC 229, Basel)
- If the answer is not found in the context, say "Not found in context."
        """
    )

    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_type="similarity", k=5),
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt_template}
    )
    return rag_chain
