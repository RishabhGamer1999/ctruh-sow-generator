"""
SOP Generator — Main Streamlit Application
"""
import os
import tempfile
import streamlit as st

from agents.sop_agent import SOPAgent
from document.parser import parse_requirement_doc
from document.generator import generate_sop_docx
from rag.ingestor import ingest_documents

# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SOP Generator",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─── Session State Init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = SOPAgent()
if "sop_ready" not in st.session_state:
    st.session_state.sop_ready = False
if "sop_bytes" not in st.session_state:
    st.session_state.sop_bytes = None
if "file_processed" not in st.session_state:
    st.session_state.file_processed = False


# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/document--v1.png", width=60)
    st.title("CTRUH SOW Generator")
    st.caption("AI-Powered Scope of Work & Commercials")

    # API Key configuration
    import os
    groq_key = os.getenv("GROQ_API_KEY", "")
    if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
        groq_key = st.secrets["GROQ_API_KEY"]

    if not groq_key:
        user_key = st.text_input(
            "🔑 Groq API Key (Free)",
            type="password",
            help="Get your free key from https://console.groq.com (no credit card needed).",
            key="user_groq_key"
        )
        if user_key:
            os.environ["GROQ_API_KEY"] = user_key
            st.session_state.agent = SOPAgent()
            st.success("API Key activated!")
    else:
        st.caption("🟢 Cloud AI Engine: Connected")

    st.divider()

    # ── Upload Client Requirement / Account Proposal Doc ─────────────────────
    st.subheader("📎 Upload Requirement Doc")
    uploaded = st.file_uploader(
        "Upload an Account Proposal or Requirement doc (.docx or .pdf)",
        type=["docx", "pdf", "txt"],
        help="The AI will read your sales proposal and auto-fill project details.",
        key="file_uploader",
    )

    if uploaded and not st.session_state.file_processed:
        with st.spinner("Reading and parsing document..."):
            suffix = f".{uploaded.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = tmp.name

            # Extract fields using LLM
            extracted = parse_requirement_doc(tmp_path, st.session_state.agent.llm)
            os.unlink(tmp_path)

            # Update agent with extracted info
            st.session_state.agent.set_extracted_info(extracted)
            st.session_state.file_processed = True

            # Build a friendly summary message
            found = [k for k, v in extracted.items() if v]
            missing = st.session_state.agent.get_missing_fields()

            if extracted:
                summary_lines = [f"📄 I've read **{uploaded.name}**. Here's what I found:\n"]
                if extracted.get("project_name"):
                    summary_lines.append(f"- **Project**: {extracted['project_name']}")
                if extracted.get("client_name"):
                    summary_lines.append(f"- **Client**: {extracted['client_name']}")
                if extracted.get("timeline"):
                    summary_lines.append(f"- **Timeline**: {extracted['timeline']}")
                if extracted.get("pricing"):
                    summary_lines.append(f"- **Budget**: {extracted['pricing']}")

                summary_lines.append(
                    f"\n✅ Extracted **{len(found)}** fields. "
                    f"Still need: **{', '.join(missing) if missing else 'nothing — ready to generate!'}**"
                )
                bot_msg = "\n".join(summary_lines)

                if missing:
                    bot_msg += f"\n\nLet's fill in the rest. {_next_question(missing[0])}"
            else:
                bot_msg = (
                    f"I read **{uploaded.name}** but couldn't extract structured information from it. "
                    "No problem — let's go through it together. What's the client name and project name?"
                )

            st.session_state.messages.append({"role": "assistant", "content": bot_msg})
            st.rerun()

    st.divider()

    # ── Knowledge Base ────────────────────────────────────────────────────────
    st.subheader("🗃️ Knowledge Base")
    st.caption("Add your docs to `knowledge_base/` folders, then click Re-index.")

    if st.button("🔄 Re-index Knowledge Base", use_container_width=True):
        with st.spinner("Indexing documents... this may take a few minutes."):
            count = ingest_documents()
        if count > 0:
            st.success(f"✅ Indexed {count} chunks!")
        else:
            st.warning("No documents found. Add files to knowledge_base/ first.")

    st.divider()

    # ── New SOP ───────────────────────────────────────────────────────────────
    if st.button("🆕 Start New SOP", use_container_width=True):
        for key in ["messages", "agent", "sop_ready", "sop_bytes", "file_processed"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


# ─── Helper: next question hint ────────────────────────────────────────────────
def _next_question(field: str) -> str:
    questions = {
        "project_name":       "What should we call this project?",
        "client_name":        "What is the client's name or company?",
        "project_description":"Can you briefly describe what this project involves?",
        "in_scope":           "What services or deliverables are included in this project?",
        "out_of_scope":       "Is there anything that should be explicitly excluded (out of scope)?",
        "timeline":           "What's the expected timeline or deadline for this project?",
        "pricing":            "What is the agreed pricing for this project? (Please share the total amount or a breakdown)",
        "payment_terms":      "What are the payment terms? (e.g. 50% upfront, 50% on delivery)",
        "special_terms":      "Are there any special terms or conditions to include?",
    }
    return questions.get(field, f"Can you tell me about the **{field.replace('_', ' ')}**?")


# ─── Main Chat UI ──────────────────────────────────────────────────────────────
st.markdown("## 📋 SOP Assistant")

# Download button (pinned at top when SOP is ready)
if st.session_state.sop_ready and st.session_state.sop_bytes:
    client_safe = st.session_state.agent.collected_fields.get('client_name', 'Client').replace(' ', '_')
    st.success("✅ Your CTRUH Scope & Commercials SOW is ready!")
    st.download_button(
        label="📥 Download Scope & Commercials (.docx)",
        data=st.session_state.sop_bytes,
        file_name=f"Scope_and_Commercials_{client_safe}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )
    st.divider()

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# Initial welcome message
if not st.session_state.messages:
    welcome = (
        "👋 Hello! I'm your **SOP Assistant**.\n\n"
        "I'll guide you through creating a professional SOP document in a few steps.\n\n"
        "You can:\n"
        "- **Upload a client requirement document** from the sidebar to auto-fill information\n"
        "- **Just start typing** and I'll ask you the right questions\n\n"
        "Let's begin — what's the **client name** and **project name**?"
    )
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(welcome)
    st.session_state.messages.append({"role": "assistant", "content": welcome})

# Chat input
if user_input := st.chat_input("Type your message here..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Get agent response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            response_text, sop_data = st.session_state.agent.chat(
                user_input, st.session_state.messages
            )
        st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})

    # If SOP data was returned, generate the document
    if sop_data:
        with st.spinner("Generating your SOP document..."):
            try:
                docx_bytes = generate_sop_docx(sop_data)
                st.session_state.sop_bytes = docx_bytes
                st.session_state.sop_ready = True
            except Exception as e:
                st.error(f"Document generation failed: {e}")

        st.rerun()
