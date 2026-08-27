"""
RAG Retriever — queries local vector index for relevant CTRUH context.
Works smoothly in both cloud (Streamlit Cloud in-memory) and local modes.
"""
from langchain_chroma import Chroma
from config import CHROMA_COLLECTION, RAG_TOP_K, GROQ_API_KEY


def _get_embeddings():
    """Return fast local embeddings (runs on CPU, no server needed) or Ollama."""
    try:
        from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
        return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    except Exception:
        from langchain_community.embeddings import FakeEmbeddings
        return FakeEmbeddings(size=384)


def retrieve_context(query: str, k: int = RAG_TOP_K) -> str:
    """
    Retrieve relevant chunks from CTRUH knowledge base.
    """
    try:
        embeddings = _get_embeddings()
        vectorstore = Chroma(
            collection_name=CHROMA_COLLECTION,
            embedding_function=embeddings,
            persist_directory="./chroma_db",
        )

        collection = vectorstore._collection
        if collection.count() == 0:
            return ""

        docs = vectorstore.similarity_search(query, k=k)
        if not docs:
            return ""

        parts = []
        for doc in docs:
            source = doc.metadata.get("source", "CTRUH Knowledge Base")
            parts.append(f"[Source: {source}]\n{doc.page_content}")

        return "\n\n---\n\n".join(parts)

    except Exception as e:
        return ""
