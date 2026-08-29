"""
SOP Agent — LangChain-powered conversational agent for CTRUH SOWs.
"""
import json
import re
import os

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config import PRIMARY_GROQ_MODEL, FALLBACK_GROQ_MODELS, REQUIRED_FIELDS
from agents.prompts import build_system_prompt, FIELD_EXTRACT_PROMPT
from rag.retriever import retrieve_context


def get_api_key() -> str:
    """Retrieve Groq API key from environment, session state, or Streamlit secrets."""
    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_API_KEY")
    if hasattr(st, "session_state") and "user_groq_key" in st.session_state and st.session_state.user_groq_key:
        return st.session_state.user_groq_key
    if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    return ""


def get_llm():
    """Instantiate the Groq LLM with active production model."""
    key = get_api_key()
    if not key:
        return None

    try:
        from langchain_groq import ChatGroq
    except Exception as e:
        print(f"[Agent] langchain_groq import failed: {e}")
        return None

    models_to_try = [PRIMARY_GROQ_MODEL] + [m for m in FALLBACK_GROQ_MODELS if m != PRIMARY_GROQ_MODEL]

    for model_name in models_to_try:
        try:
            llm = ChatGroq(
                model_name=model_name,
                groq_api_key=key,
                temperature=0.2,
                max_retries=1,
            )
            return llm
        except Exception:
            continue

    return None


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

        ai_text = ""
        try:
            response = llm.invoke(messages)
            ai_text = response.content
        except Exception as err_primary:
            key = get_api_key()
            from langchain_groq import ChatGroq
            success = False
            for fb_model in FALLBACK_GROQ_MODELS:
                try:
                    fallback_llm = ChatGroq(model_name=fb_model, groq_api_key=key, temperature=0.2)
                    response = fallback_llm.invoke(messages)
                    ai_text = response.content
                    self.llm = fallback_llm
                    success = True
                    break
                except Exception:
                    continue

            if not success:
                return f"⚠️ AI Engine error: {str(err_primary)}", None

        sow_data = self._parse_sow_data(ai_text)
        display_text = re.sub(r'<SOP_DATA>.*?</SOP_DATA>', '', ai_text, flags=re.DOTALL).strip()

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
                SystemMessage(content=f"Reference from CTRUH knowledge base:\n\n{context}")
            )

        for msg in chat_history[1:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                content = msg["content"].replace(
                    "\n\n✅ **Your CTRUH Scope & Commercials (SOW) is ready! Click the Download button above.**", ""
                )
                messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=user_message))
        return messages

    def _extract_fields_from_message(self, user_message: str, llm):
        try:
            prompt = FIELD_EXTRACT_PROMPT.format(user_message=user_message)
            result = llm.invoke([HumanMessage(content=prompt)])
            json_match = re.search(r'\{.*\}', result.content, re.DOTALL)
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
                preview = str(value)[:60] + ("..." if len(str(value)) > 60 else "")
                lines.append(f"✅ {field}: {preview}")
            else:
                lines.append(f"❌ {field}: NOT YET COLLECTED")
        return "\n".join(lines)
