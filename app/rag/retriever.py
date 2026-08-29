"""
Knowledge Base Loader & In-Memory Retriever.
Optimized for fast, token-efficient Groq API calls.
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
            for p in reader.pages[:3]:  # First 3 pages only for reference
                txt = p.extract_text() or ""
                if txt.strip():
                    pages.append(txt.strip())
            return "\n".join(pages).strip()
        elif ext in [".docx", ".doc"]:
            return docx2txt.process(str(file_path)).strip()
        elif ext in [".txt", ".md", ".csv"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
    except Exception as e:
        print(f"[KB] Read error for {file_path.name}: {e}")
    return ""


def load_knowledge_base(kb_path: str = KB_PATH) -> list[dict]:
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
                    "content": text[:1200]  # Compact reference snippet
                })
        except Exception as e:
            print(f"[KB] Skipped {file_path.name}: {e}")

    _KB_CACHE = docs
    return docs


def retrieve_context(query: str = "", max_chars: int = 1500) -> str:
    """Returns concise CTRUH reference context within strict token limits."""
    global _KB_CACHE
    if not _KB_CACHE:
        try:
            load_knowledge_base()
        except Exception:
            return ""

    if not _KB_CACHE:
        return ""

    # Filter for most relevant snippet or standard format
    for item in _KB_CACHE:
        if "standard" in item["source"].lower() or "format" in item["source"].lower():
            return f"--- [CTRUH Standard SOW Template] ---\n{item['content'][:max_chars]}"

    # Fallback to first available reference
    return f"--- [CTRUH Reference] ---\n{_KB_CACHE[0]['content'][:max_chars]}"
