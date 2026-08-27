"""
SOP Agent — LangChain-powered conversational agent that:
  1. Guides the user through collecting CTRUH SOW information
  2. Retrieves relevant context from the RAG knowledge base
  3. Generates the structured SOW data when all details are ready
"""
import json
import re
import os

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config import (
    GROQ_API_KEY, GROQ_MODEL, LLM_PROVIDER,
    OLLAMA_BASE_URL, OLLAMA_MODEL, REQUIRED_FIELDS
)
from agents.prompts import build_system_prompt, FIELD_EXTRACT_PROMPT
from rag.retriever import retrieve_context


def get_llm():
    """Returns Groq or Ollama LLM depending on configuration."""
    if GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model_name=GROQ_MODEL,
                groq_api_key=GROQ_API_KEY,
                temperature=0.2,
            )
        except Exception as e:
            print(f"[Agent] Groq init failed, falling back: {e}")

    # Fallback to local Ollama
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
    )


class SOPAgent:
    def __init__(self):
        self.llm = get_llm()
        self.collected_fields: dict = {}

    def set_extracted_info(self, info: dict):
        """Pre-populate fields extracted from an uploaded Account Proposal."""
        self.collected_fields.update({k: v for k, v in info.items() if v})

    def get_missing_fields(self) -> list[str]:
        return [
            f for f in REQUIRED_FIELDS
            if f not in self.collected_fields or not self.collected_fields[f]
        ]

    def all_fields_collected(self) -> bool:
        return len(self.get_missing_fields()) == 0

    def chat(self, user_message: str, chat_history: list) -> tuple[str, dict | None]:
        """
        Process user message and return (response_text, sow_data_dict or None)
        """
        self._extract_fields_from_message(user_message)
        context = retrieve_context(user_message)
        messages = self._build_messages(user_message, chat_history, context)

        response = self.llm.invoke(messages)
        ai_text = response.content

        sow_data = self._parse_sow_data(ai_text)

        # Clean display text (remove raw JSON markup)
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

    def _extract_fields_from_message(self, user_message: str):
        try:
            prompt = FIELD_EXTRACT_PROMPT.format(user_message=user_message)
            result = self.llm.invoke([HumanMessage(content=prompt)])
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
