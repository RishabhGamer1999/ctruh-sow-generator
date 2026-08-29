"""
Knowledge Base Ingestor — Reloads reference documents into memory.
"""
from rag.retriever import load_knowledge_base, KB_PATH


def ingest_documents(kb_path: str = KB_PATH) -> int:
    docs = load_knowledge_base(kb_path)
    return len(docs)


if __name__ == "__main__":
    count = ingest_documents()
    print(f"Loaded {count} documents into knowledge base cache.")
