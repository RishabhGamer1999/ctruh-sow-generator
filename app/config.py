"""
Central configuration for CTRUH SOW Generator.
Supports Cloud Deployment (Groq Cloud API) and Local Deployment (Ollama).
"""
import os
import streamlit as st

# ─── API Keys & Providers ─────────────────────────────────────────────────────
# Check Streamlit secrets first (for Streamlit Cloud), then environment variables
def get_secret(key: str, default: str = "") -> str:
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

GROQ_API_KEY      = get_secret("GROQ_API_KEY", "")
LLM_PROVIDER      = get_secret("LLM_PROVIDER", "groq" if GROQ_API_KEY else "ollama")

# ─── LLM Models ───────────────────────────────────────────────────────────────
# Default Groq model: llama-3.3-70b-versatile or mistral-saba-24b (fast, top tier)
GROQ_MODEL        = get_secret("GROQ_MODEL", "llama-3.3-70b-versatile")
OLLAMA_BASE_URL   = get_secret("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL      = get_secret("LLM_MODEL", "mistral:7b")

# ─── Vector DB & Paths ────────────────────────────────────────────────────────
CHROMA_COLLECTION = "ctruh_sow_kb"
BASE_DIR          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH           = os.getenv("KB_PATH", os.path.join(BASE_DIR, "knowledge_base"))
OUTPUT_PATH       = os.getenv("OUTPUT_PATH", os.path.join(BASE_DIR, "outputs"))

# ─── RAG Settings ─────────────────────────────────────────────────────────────
RAG_TOP_K         = 4
CHUNK_SIZE        = 1000
CHUNK_OVERLAP     = 200

# ─── Required SOW Fields ──────────────────────────────────────────────────────
REQUIRED_FIELDS = [
    "client_name",
    "project_name",
    "project_objective",
    "in_scope",
    "timeline",
    "pricing",
]
