"""
SOP Agent — LangChain-powered conversational agent for CTRUH SOWs.
Features robust JSON parsing, fault tolerance, and rich summary responses.
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
            temperature=0.1,
            max_tokens=3000,
        )
    except Exception as e:
        print(f"[Agent] LLM creation error: {e}")
        return None


def clean_ai_response(raw_text: str) -> str:
    """Strip thinking tags and JSON markup from visible chat response."""
    cleaned = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    if "<think>" in cleaned and "</think>" not in cleaned:
        cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    
    cleaned = re.sub(r'<SOP_DATA>.*?</SOP_DATA>', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'```json.*?```', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()


def safe_extract_json(text: str) -> dict | None:
    """Robust JSON extraction from LLM response with multiple fallback strategies."""
    # Strategy 1: <SOP_DATA> tags
    match = re.search(r'<SOP_DATA>(.*?)</SOP_DATA>', text, re.DOTALL)
    candidate_str = match.group(1).strip() if match else ""

    # Strategy 2: ```json ... ``` code block
    if not candidate_str:
        json_block_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_block_match:
            candidate_str = json_block_match.group(1).strip()

    # Strategy 3: Outermost { ... }
    if not candidate_str:
        curly_match = re.search(r'(\{[\s\S]*\})', text)
        if curly_match:
            candidate_str = curly_match.group(1).strip()

    if not candidate_str:
        return None

    # Clean common LLM JSON syntax errors
    # Remove trailing commas: , } -> } and , ] -> ]
    candidate_str = re.sub(r',\s*\}', '}', candidate_str)
    candidate_str = re.sub(r',\s*\]', ']', candidate_str)

    try:
        return json.loads(candidate_str)
    except Exception:
        # Fallback: try parsing with relaxed regex if strict parsing fails
        try:
            # Replace single quotes with double quotes
            relaxed = re.sub(r"'", '"', candidate_str)
            return json.loads(relaxed)
        except Exception:
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
                "⚠️ **Groq API Key missing!** Please enter your free key in the sidebar to start.",
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

        # Extract structured SOW data
        sow_data = safe_extract_json(ai_text)
        
        # Merge with collected fields
        if sow_data:
            for f in REQUIRED_FIELDS:
                if f not in sow_data and f in self.collected_fields:
                    sow_data[f] = self.collected_fields[f]

        display_text = clean_ai_response(ai_text)

        # Ensure user ALWAYS gets a meaningful message
        if sow_data:
            client_display = sow_data.get('client_name', 'your client')
            summary_msg = (
                f"🎉 **I have generated the official Scope of Work for {client_display}!**\n\n"
                f"• **Project**: {sow_data.get('project_name', 'Digital Deliverables')}\n"
                f"• **Timeline**: {sow_data.get('timeline_estimate', 'As agreed in scope')}\n"
                f"• **Commercials**: {sow_data.get('pricing', 'Included in document')}\n\n"
                f"📥 **Click the blue download button at the top of the page to save the Word document (.docx).**"
            )
            display_text = summary_msg
        elif not display_text:
            display_text = "I've noted the details. Could you please confirm if there are any specific deliverables or timelines to include?"

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
                SystemMessage(content=f"CTRUH Reference Guidelines:\n{context}")
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
            prompt = FIELD_EXTRACT_PROMPT.format(user_message=user_message[:500])
            result = llm.invoke([HumanMessage(content=prompt)])
            cleaned_result = clean_ai_response(result.content)
            extracted = safe_extract_json(cleaned_result)
            if extracted and isinstance(extracted, dict):
                for key, value in extracted.items():
                    if value and str(value).lower() not in ("null", "none", ""):
                        self.collected_fields[key] = value
        except Exception:
            pass

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
