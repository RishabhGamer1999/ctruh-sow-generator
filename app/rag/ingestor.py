"""
Knowledge Base Ingestor — loads documents from knowledge_base/ into local ChromaDB.
"""
import os
import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    CSVLoader,
    TextLoader,
    UnstructuredExcelLoader,
)

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from config import CHROMA_COLLECTION, KB_PATH, CHUNK_SIZE, CHUNK_OVERLAP
from rag.retriever import _get_embeddings

LOADERS = {
    ".docx": Docx2txtLoader,
    ".pdf":  PyPDFLoader,
    ".csv":  CSVLoader,
    ".txt":  TextLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls":  UnstructuredExcelLoader,
}


def load_all_documents(kb_path: str) -> list:
    documents = []
    base = Path(kb_path)

    if not base.exists():
        return documents

    for file_path in sorted(base.rglob("*")):
        if not file_path.is_file() or file_path.name.startswith("."):
            continue

        ext = file_path.suffix.lower()
        if ext not in LOADERS:
            continue

        try:
            loader_cls = LOADERS[ext]
            loader = loader_cls(str(file_path))
            docs = loader.load()

            relative = str(file_path.relative_to(base))
            for doc in docs:
                doc.metadata["source"] = relative

            documents.extend(docs)
        except Exception as e:
            print(f"[Ingestor] Error loading {file_path.name}: {e}")

    return documents


def ingest_documents(kb_path: str = KB_PATH) -> int:
    try:
        documents = load_all_documents(kb_path)
        if not documents:
            return 0

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        chunks = splitter.split_documents(documents)
        embeddings = _get_embeddings()

        vectorstore = Chroma(
            collection_name=CHROMA_COLLECTION,
            embedding_function=embeddings,
            persist_directory="./chroma_db",
        )
        
        # Reset and add
        try:
            vectorstore.delete_collection()
        except Exception:
            pass

        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=CHROMA_COLLECTION,
            persist_directory="./chroma_db",
        )

        return len(chunks)
    except Exception as e:
        print(f"[Ingestor] Ingestion error: {e}")
        return 0


if __name__ == "__main__":
    count = ingest_documents()
    sys.exit(0 if count >= 0 else 1)
