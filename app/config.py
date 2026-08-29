"""
Central configuration for CTRUH SOW Generator.
"""
import os
import streamlit as st

def get_secret(key: str, default: str = "") -> str:
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

GROQ_API_KEY      = get_secret("GROQ_API_KEY", "")
LLM_PROVIDER      = get_secret("LLM_PROVIDER", "groq" if GROQ_API_KEY else "ollama")

# Active Groq production models
PRIMARY_GROQ_MODEL = get_secret("GROQ_MODEL", "llama-3.1-8b-instant")
FALLBACK_GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "llama-3.3-70b-specdec",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]

BASE_DIR          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH           = os.getenv("KB_PATH", os.path.join(BASE_DIR, "knowledge_base"))
OUTPUT_PATH       = os.getenv("OUTPUT_PATH", os.path.join(BASE_DIR, "outputs"))

REQUIRED_FIELDS = [
    "client_name",
    "project_name",
    "project_objective",
    "in_scope",
    "timeline",
    "pricing",
]
