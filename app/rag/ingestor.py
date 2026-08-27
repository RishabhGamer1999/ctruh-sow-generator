"""
Knowledge Base Ingestor — loads all documents from knowledge_base/ into ChromaDB.

Run this once on setup, and again whenever you add new documents to the knowledge base.
The app UI also has a "Re-index Knowledge Base" button that triggers this.
"""
import os
import sys
from pathlib import Path

import chromadb
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    CSVLoader,
    TextLoader,
    UnstructuredExcelLoader,
)

from config import (
    OLLAMA_BASE_URL, EMBEDDING_MODEL,
    CHROMA_HOST, CHROMA_PORT, CHROMA_COLLECTION,
    KB_PATH, CHUNK_SIZE, CHUNK_OVERLAP,
)

# ─── File type → loader mapping ───────────────────────────────────────────────
LOADERS = {
    ".docx": Docx2txtLoader,
    ".pdf":  PyPDFLoader,
    ".csv":  CSVLoader,
    ".txt":  TextLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls":  UnstructuredExcelLoader,
}


def load_all_documents(kb_path: str) -> list:
    """Walk the knowledge_base directory and load all supported files."""
    documents = []
    base = Path(kb_path)

    if not base.exists():
        print(f"[Ingestor] Knowledge base directory not found: {kb_path}")
        return documents

    for file_path in sorted(base.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.name.startswith("."):
            continue  # skip .gitkeep etc.

        ext = file_path.suffix.lower()
        if ext not in LOADERS:
            continue

        try:
            loader_cls = LOADERS[ext]
            loader = loader_cls(str(file_path))
            docs = loader.load()

            # Tag each chunk with its source file (relative path)
            relative = str(file_path.relative_to(base))
            for doc in docs:
                doc.metadata["source"] = relative

            documents.extend(docs)
            print(f"  ✅ Loaded: {relative}  ({len(docs)} pages/sections)")

        except Exception as e:
            print(f"  ❌ Failed to load {file_path.name}: {e}")

    return documents


def ingest_documents(kb_path: str = KB_PATH) -> int:
    """
    Main ingestion function.
    Returns the number of chunks indexed.
    """
    print("\n🔄 Starting knowledge base ingestion...")
    print(f"   Directory: {kb_path}")

    # 1. Load documents
    documents = load_all_documents(kb_path)

    if not documents:
        print("\n⚠️  No documents found. Add files to knowledge_base/ and re-index.")
        return 0

    print(f"\n📄 Loaded {len(documents)} document sections total")

    # 2. Chunk documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    print(f"✂️  Split into {len(chunks)} chunks")

    # 3. Initialize embeddings (local Ollama)
    print("🧠 Initialising embeddings model (this may take a moment)...")
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

    # 4. Connect to ChromaDB and reset collection
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    try:
        client.delete_collection(CHROMA_COLLECTION)
        print("🗑️  Cleared existing knowledge base index")
    except Exception:
        pass  # Collection didn't exist yet — that's fine

    # 5. Index all chunks
    print("📥 Indexing chunks into ChromaDB...")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        client=client,
        collection_name=CHROMA_COLLECTION,
    )

    print(f"\n🎉 Done! Indexed {len(chunks)} chunks from {len(documents)} document sections.")
    return len(chunks)


if __name__ == "__main__":
    count = ingest_documents()
    sys.exit(0 if count >= 0 else 1)
