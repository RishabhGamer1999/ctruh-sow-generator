"""
Client Requirement / Account Proposal Document Parser.
Safely extracts structured SOW fields from uploaded PDF/DOCX files.
"""
import json
import re
from pathlib import Path
from pypdf import PdfReader
import docx2txt

from langchain_core.messages import HumanMessage
from agents.prompts import EXTRACTION_PROMPT


def extract_raw_text(file_path: str) -> str:
    """Extract raw text from PDF, DOCX, or text files safely."""
    path = Path(file_path)
    full_text = ""

    try:
        if path.suffix.lower() == ".pdf":
            reader = PdfReader(file_path)
            pages_text = []
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text() or ""
                    if text.strip():
                        pages_text.append(text.strip())
                except Exception as pe:
                    print(f"[Parser] Warning: Could not extract text from page {i}: {pe}")
            full_text = "\n\n".join(pages_text)
        elif path.suffix.lower() in [".docx", ".doc"]:
            full_text = docx2txt.process(file_path).strip()
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                full_text = f.read().strip()
    except Exception as e:
        print(f"[Parser] File reading exception: {e}")
        return ""

    return full_text.strip()


def parse_requirement_doc(file_path: str, llm) -> dict:
    """
    Extract project parameters from an uploaded Account Proposal / Requirement document.
    """
    full_text = extract_raw_text(file_path)
    if not full_text:
        return {}

    if llm is None:
        return {}

    # Limit to 4500 characters to stay within fast prompt context
    truncated = full_text[:4500]
    prompt = EXTRACTION_PROMPT.format(document_text=truncated)

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()

        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not json_match:
            return {}

        extracted = json.loads(json_match.group())
        cleaned = {
            k: v for k, v in extracted.items()
            if v is not None and str(v).strip().lower() not in ("null", "none", "")
        }
        return cleaned

    except Exception as e:
        print(f"[Parser] LLM extraction error: {e}")
        return {}
