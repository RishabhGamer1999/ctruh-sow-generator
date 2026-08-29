"""
Client Requirement / Account Proposal Document Parser.
Extracts structured SOW fields from uploaded PDF/DOCX files with smart fallback.
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
                except Exception:
                    pass
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


def parse_with_regex_fallback(text: str) -> dict:
    """Fallback parser for CTRUH Account Proposal table formats."""
    result = {}
    
    # Extract Company / Client Name
    m_comp = re.search(r'(?:Company\s*Name|The Account)[\s\:\-\|]+([^\n\r\|]+)', text, re.IGNORECASE)
    if m_comp and m_comp.group(1).strip() and len(m_comp.group(1).strip()) < 80:
        result["client_name"] = m_comp.group(1).strip()

    # Extract POC
    m_poc = re.search(r'(?:POC\s*Name|Who we[\'’]re talking to)[\s\:\-\|]+([^\n\r\|]+)', text, re.IGNORECASE)
    if m_poc and m_poc.group(1).strip() and len(m_poc.group(1).strip()) < 80:
        result["poc_name"] = m_poc.group(1).strip()

    # Extract Use Case / Project Name
    m_uc = re.search(r'(?:Use[\-\s]*case|What they need)[\s\:\-\|]+([^\n\r\|]+)', text, re.IGNORECASE)
    if m_uc and m_uc.group(1).strip() and len(m_uc.group(1).strip()) < 120:
        result["project_name"] = m_uc.group(1).strip()

    # Extract Deliverables
    m_what = re.search(r'(?:What & how many|What we[\'’]re proposing)[\s\:\-\|]+([^\n\r]+)', text, re.IGNORECASE)
    if m_what and m_what.group(1).strip():
        result["in_scope"] = [m_what.group(1).strip()]

    return result


def parse_requirement_doc(file_path: str, llm) -> dict:
    """
    Extract project parameters from an uploaded Account Proposal / Requirement document.
    """
    full_text = extract_raw_text(file_path)
    if not full_text:
        return {}

    # Extract regex fallback fields first
    fallback_data = parse_with_regex_fallback(full_text)

    if llm is None:
        return fallback_data

    truncated = full_text[:4000]
    prompt = EXTRACTION_PROMPT.format(document_text=truncated)

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()

        # Clean thinking tags
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL)
        if "<think>" in raw and "</think>" not in raw:
            raw = re.sub(r'<think>.*', '', raw, flags=re.DOTALL)

        # Extract JSON candidate
        candidate = ""
        m_json = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', raw)
        if m_json:
            candidate = m_json.group(1)
        else:
            m_curly = re.search(r'(\{[\s\S]*\})', raw)
            if m_curly:
                candidate = m_curly.group(1)

        if candidate:
            candidate = re.sub(r',\s*\}', '}', candidate)
            candidate = re.sub(r',\s*\]', ']', candidate)
            extracted = json.loads(candidate)
            
            cleaned = {
                k: v for k, v in extracted.items()
                if v is not None and str(v).strip().lower() not in ("null", "none", "")
            }
            
            # Combine with fallback
            for k, v in fallback_data.items():
                if k not in cleaned or not cleaned[k]:
                    cleaned[k] = v
            return cleaned

    except Exception as e:
        print(f"[Parser] LLM extraction error: {e}")

    return fallback_data
