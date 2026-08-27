"""
Client Requirement / Account Proposal Document Parser.
Accepts .pdf or .docx requirement documents gathered by sales/marketing
and uses the local LLM to extract structured SOW fields.
"""
import json
import re
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader

from agents.prompts import EXTRACTION_PROMPT


def parse_requirement_doc(file_path: str, llm) -> dict:
    """
    Load a client requirement / Account Proposal doc (.pdf or .docx)
    and extract structured project fields.
    """
    path = Path(file_path)
    full_text = ""

    try:
        if path.suffix.lower() == ".pdf":
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            full_text = "\n\n".join(doc.page_content for doc in docs).strip()
        elif path.suffix.lower() in [".docx", ".doc"]:
            loader = Docx2txtLoader(file_path)
            docs = loader.load()
            full_text = "\n\n".join(doc.page_content for doc in docs).strip()
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                full_text = f.read()
    except Exception as e:
        print(f"[Parser] Error reading requirement file: {e}")
        return {}

    if not full_text:
        return {}

    # Take up to 5000 characters (captures Account, POC, Needs, Pre-read, Meeting summary)
    truncated = full_text[:5000]

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
        print(f"[Parser] LLM extraction failed: {e}")
        return {}
