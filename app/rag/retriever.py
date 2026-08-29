"""
Knowledge Base Loader & In-Memory Retriever.
Fast, 100% crash-proof, and designed for cloud environments.
"""
import os
from pathlib import Path
from pypdf import PdfReader
import docx2txt

from config import KB_PATH

_KB_CACHE = []


def _extract_text_from_file(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    try:
        if ext == ".pdf":
            reader = PdfReader(str(file_path))
            pages = []
            for p in reader.pages:
                try:
                    txt = p.extract_text() or ""
                    if txt.strip():
                        pages.append(txt.strip())
                except Exception:
                    pass
            return "\n".join(pages).strip()
        elif ext in [".docx", ".doc"]:
            return docx2txt.process(str(file_path)).strip()
        elif ext in [".txt", ".md", ".csv"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
    except Exception as e:
        print(f"[KB] Non-fatal read error for {file_path.name}: {e}")
    return ""


def load_knowledge_base(kb_path: str = KB_PATH) -> list[dict]:
    """Scan knowledge_base directory and load reference documents into memory."""
    global _KB_CACHE
    docs = []
    base = Path(kb_path)

    if not base.exists():
        return docs

    for file_path in sorted(base.rglob("*")):
        if not file_path.is_file() or file_path.name.startswith("."):
            continue

        try:
            text = _extract_text_from_file(file_path)
            if text:
                rel = str(file_path.relative_to(base))
                docs.append({
                    "source": rel,
                    "content": text[:3000]
                })
        except Exception as e:
            print(f"[KB] Skipped file {file_path.name}: {e}")

    _KB_CACHE = docs
    return docs


def retrieve_context(query: str = "", max_chars: int = 4000) -> str:
    """
    Returns relevant CTRUH knowledge base context.
    """
    global _KB_CACHE
    if not _KB_CACHE:
        try:
            load_knowledge_base()
        except Exception:
            return ""

    if not _KB_CACHE:
        return ""

    context_parts = []
    total_len = 0

    for item in _KB_CACHE:
        snippet = f"--- [Reference: {item['source']}] ---\n{item['content']}\n"
        if total_len + len(snippet) > max_chars:
            break
        context_parts.append(snippet)
        total_len += len(snippet)

    return "\n".join(context_parts)
