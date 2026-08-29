"""
SOP Agent — LangChain-powered conversational agent for CTRUH SOWs.
Cleanly parses outputs and filters reasoning/thinking tags.
"""
import json
import re
import os

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config import REQUIRED_FIELDS
from agents.prompts import build_system_prompt, FIELD_EXTRACT_PROMPT
from rag.retriever import retrieve_context


def get_api_key() -> str:
    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_API_KEY")
    if hasattr(st, "session_state") and "user_groq_key" in st.session_state and st.session_state.user_groq_key:
        return st.session_state.user_groq_key
    if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    return ""


def get_active_groq_model(api_key: str) -> str:
    # Prefer non-reasoning direct instruct models for clean client communication
    preferred_order = [
        "llama-3.3-70b-versatile",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        model_list = client.models.list()
        available_ids = [m.id for m in model_list.data]
        for pref in preferred_order:
            if pref in available_ids:
                return pref
        if available_ids:
            return available_ids[0]
    except Exception as e:
        print(f"[Agent] Model query error: {e}")
    return "llama3-70b-8192"


def get_llm():
    key = get_api_key()
    if not key:
        return None
    try:
        from langchain_groq import ChatGroq
        model_name = get_active_groq_model(key)
        return ChatGroq(
            model_name=model_name,
            groq_api_key=key,
            temperature=0.2,
            max_tokens=2048,
        )
    except Exception as e:
        print(f"[Agent] LLM creation error: {e}")
        return None


def clean_ai_response(raw_text: str) -> str:
    """Removes thinking tags, JSON payload tags, and cleans display text."""
    # 1. Remove <think>...</think> blocks
    cleaned = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    # 2. Remove unclosed <think> tags
    if "<think>" in cleaned and "</think>" not in cleaned:
        cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    
    # 3. Remove <SOP_DATA>...</SOP_DATA> JSON blocks
    cleaned = re.sub(r'<SOP_DATA>.*?</SOP_DATA>', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()


class SOPAgent:
    def __init__(self):
        self.llm = get_llm()
        self.collected_fields: dict = {}

    def ensure_llm(self):
        if self.llm is None:
            self.llm = get_llm()
        return self.llm

    def set_extracted_info(self, info: dict):
        self.collected_fields.update({k: v for k, v in info.items() if v})

    def get_missing_fields(self) -> list[str]:
        return [
            f for f in REQUIRED_FIELDS
            if f not in self.collected_fields or not self.collected_fields[f]
        ]

    def all_fields_collected(self) -> bool:
        return len(self.get_missing_fields()) == 0

    def chat(self, user_message: str, chat_history: list) -> tuple[str, dict | None]:
        llm = self.ensure_llm()
        if llm is None:
            return (
                "⚠️ **Groq API Key missing!** Please enter your free key in the sidebar on the left to start generating SOWs.",
                None
            )

        self._extract_fields_from_message(user_message, llm)
        context = retrieve_context(user_message)
        messages = self._build_messages(user_message, chat_history, context)

        try:
            response = llm.invoke(messages)
            ai_text = response.content
        except Exception as e:
            return f"⚠️ AI Engine error: {str(e)}", None

        sow_data = self._parse_sow_data(ai_text)
        display_text = clean_ai_response(ai_text)

        if not display_text and sow_data:
            display_text = "I have collected all project details and generated your SOW."

        if sow_data:
            display_text += "\n\n✅ **Your CTRUH Scope & Commercials (SOW) is ready! Click the Download button above.**"

        return display_text, sow_data

    def _build_messages(self, user_message: str, chat_history: list, context: str) -> list:
        fields_status = self._format_fields_status()
        system_prompt = build_system_prompt(
            collected_fields=json.dumps(self.collected_fields, indent=2),
            fields_status=fields_status,
        )

        messages = [SystemMessage(content=system_prompt)]

        if context:
            messages.append(
                SystemMessage(content=f"CTRUH Template Reference:\n{context}")
            )

        recent_history = chat_history[-4:] if len(chat_history) > 4 else chat_history
        for msg in recent_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"][:400]))
            elif msg["role"] == "assistant":
                clean_content = clean_ai_response(msg["content"])
                if clean_content:
                    messages.append(AIMessage(content=clean_content[:400]))

        messages.append(HumanMessage(content=user_message))
        return messages

    def _extract_fields_from_message(self, user_message: str, llm):
        try:
            prompt = FIELD_EXTRACT_PROMPT.format(user_message=user_message[:300])
            result = llm.invoke([HumanMessage(content=prompt)])
            cleaned_result = clean_ai_response(result.content)
            json_match = re.search(r'\{.*\}', cleaned_result, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group())
                for key, value in extracted.items():
                    if value and str(value).lower() not in ("null", "none", ""):
                        self.collected_fields[key] = value
        except Exception:
            pass

    def _parse_sow_data(self, response: str) -> dict | None:
        match = re.search(r'<SOP_DATA>(.*?)</SOP_DATA>', response, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(1).strip())
            for field in REQUIRED_FIELDS:
                if field not in data and field in self.collected_fields:
                    data[field] = self.collected_fields[field]
            return data
        except json.JSONDecodeError:
            return None

    def _format_fields_status(self) -> str:
        lines = []
        for field in REQUIRED_FIELDS:
            value = self.collected_fields.get(field)
            if value:
                preview = str(value)[:50] + ("..." if len(str(value)) > 50 else "")
                lines.append(f"✅ {field}: {preview}")
            else:
                lines.append(f"❌ {field}: Missing")
        return "\n".join(lines)
