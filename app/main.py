"""
CTRUH SOW Generator — Main Application Logic
"""
import os
import time
import tempfile
import streamlit as st

from agents.sop_agent import SOPAgent
from document.parser import parse_requirement_doc
from document.generator import generate_sop_docx
from rag.ingestor import ingest_documents


def _next_question(field: str) -> str:
    questions = {
        "project_name":        "What should we name this project?",
        "client_name":         "What is the client's company or brand name?",
        "project_objective":   "What is the core objective of this project for the client?",
        "in_scope":            "What specific deliverables are in-scope (e.g. 3D models, AI videos, configurator)?",
        "timeline":            "What is the delivery timeline or deadline for this project?",
        "pricing":             "What is the agreed pricing / commercial package for this project?",
    }
    return questions.get(field, f"Could you provide details on **{field.replace('_', ' ')}**?")


def run_app():
    """Main Streamlit execution loop."""
    # ── Page Configuration ──
    st.set_page_config(
        page_title="CTRUH SOW Generator",
        page_icon="📋",
        layout="centered",
        initial_sidebar_state="expanded",
    )

    # ── Session State Initialization ──
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = SOPAgent()
    if "sop_ready" not in st.session_state:
        st.session_state.sop_ready = False
    if "sop_bytes" not in st.session_state:
        st.session_state.sop_bytes = None
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()

    # ── Sidebar ──
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/document--v1.png", width=50)
        st.title("CTRUH SOW Generator")
        st.caption("AI-Powered Scope of Work & Commercials")

        # API Key Configuration
        groq_key = os.getenv("GROQ_API_KEY", "")
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            groq_key = st.secrets["GROQ_API_KEY"]

        if not groq_key:
            user_key = st.text_input(
                "🔑 Groq API Key (Free)",
                type="password",
                help="Enter your free key from https://console.groq.com",
                key="user_groq_key"
            )
            if user_key:
                os.environ["GROQ_API_KEY"] = user_key
                st.session_state.agent = SOPAgent()
                st.success("✅ API Key connected!")
        else:
            st.caption("🟢 AI Cloud Engine: Connected")

        st.divider()

        # ── Upload Requirement Doc ──
        st.subheader("📎 Upload Requirement Doc")
        uploaded = st.file_uploader(
            "Upload an Account Proposal (.docx, .pdf, .txt)",
            type=["docx", "pdf", "txt"],
            help="Upload sales proposal to auto-extract project parameters.",
            key="file_uploader",
        )

        if uploaded and uploaded.name not in st.session_state.processed_files:
            progress_placeholder = st.empty()
            start_time = time.time()

            try:
                progress_placeholder.info(f"⏱️ **Step 1/3:** Reading `{uploaded.name}`... ({time.time() - start_time:.1f}s)")
                suffix = f".{uploaded.name.split('.')[-1]}"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.getvalue())
                    tmp_path = tmp.name

                llm = st.session_state.agent.ensure_llm()
                
                progress_placeholder.info(f"🧠 **Step 2/3:** Analyzing project scope with AI... ({time.time() - start_time:.1f}s)")
                extracted = parse_requirement_doc(tmp_path, llm)
                
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

                elapsed = time.time() - start_time
                progress_placeholder.success(f"✅ **Step 3/3:** Analysis complete in {elapsed:.1f}s!")

                if extracted:
                    st.session_state.agent.set_extracted_info(extracted)
                st.session_state.processed_files.add(uploaded.name)

                found = [k for k, v in extracted.items() if v]
                missing = st.session_state.agent.get_missing_fields()

                if extracted:
                    lines = [f"📄 **I've analyzed `{uploaded.name}` ({elapsed:.1f}s)**. Here is what I found:\n"]
                    if extracted.get("client_name"):
                        lines.append(f"- **Client Name**: {extracted['client_name']}")
                    if extracted.get("project_name"):
                        lines.append(f"- **Project**: {extracted['project_name']}")
                    if extracted.get("timeline"):
                        lines.append(f"- **Timeline**: {extracted['timeline']}")
                    if extracted.get("pricing"):
                        lines.append(f"- **Pricing / Commercials**: {extracted['pricing']}")

                    lines.append(f"\n✅ Extracted **{len(found)}** project parameters.")
                    if missing:
                        lines.append(f"\n👉 **Next step:** {_next_question(missing[0])}")
                    else:
                        lines.append("\n👉 **All fields ready!** Just confirm or share any custom pricing to generate.")

                    bot_msg = "\n".join(lines)
                else:
                    bot_msg = (
                        f"📄 I've read `{uploaded.name}` ({elapsed:.1f}s). Let's go through it together!\n\n"
                        "What is the **client name** and **project name**?"
                    )

                st.session_state.messages.append({"role": "assistant", "content": bot_msg})

            except Exception as e:
                progress_placeholder.error(f"❌ Error analyzing document: {str(e)}")

        st.divider()

        # ── Knowledge Base ──
        st.subheader("🗃️ Knowledge Base")
        st.caption("Reference SOWs, templates, and company policies.")

        if st.button("🔄 Reload Knowledge Base", use_container_width=True):
            kb_start = time.time()
            with st.spinner("Indexing reference documents..."):
                count = ingest_documents()
            kb_elapsed = time.time() - kb_start
            if count > 0:
                st.success(f"✅ Loaded {count} reference files ({kb_elapsed:.1f}s)!")
            else:
                st.info("Knowledge base is ready.")

        st.divider()

        # ── Start New SOW ──
        if st.button("🆕 Start New SOW", use_container_width=True):
            for key in ["messages", "agent", "sop_ready", "sop_bytes", "processed_files"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # ── Main Chat Display ──
    st.markdown("## 📋 CTRUH Scope & Commercials (SOW)")
    st.caption("Generate formal SOW documents following CTRUH's official 9-section format.")

    # Download banner
    if st.session_state.sop_ready and st.session_state.sop_bytes:
        client_safe = st.session_state.agent.collected_fields.get('client_name', 'Client').replace(' ', '_')
        st.success("🎉 **Your CTRUH SOW Document is Ready!**")
        st.download_button(
            label="📥 Download Scope & Commercials (.docx)",
            data=st.session_state.sop_bytes,
            file_name=f"Scope_and_Commercials_{client_safe}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        st.divider()

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # Welcome message if empty
    if not st.session_state.messages:
        welcome = (
            "👋 Hello! I am your **CTRUH SOW Assistant**.\n\n"
            "I will help you create a formal **Project Scope & Commercials** document.\n\n"
            "**How to begin:**\n"
            "1. 📎 **Upload an Account Proposal** doc in the sidebar to auto-fill details, or\n"
            "2. 💬 **Type below** (e.g. *\"Let's create an SOW for Stanley Lifestyles for 3D configurators\"*)."
        )
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(welcome)
        st.session_state.messages.append({"role": "assistant", "content": welcome})

    # ── Chat Input ──
    if user_input := st.chat_input("Type your message or project details here..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            status_box = st.empty()
            t0 = time.time()
            status_box.info("🧠 Thinking & retrieving CTRUH context...")
            
            response_text, sow_data = st.session_state.agent.chat(
                user_input, st.session_state.messages
            )
            
            elapsed_chat = time.time() - t0
            status_box.empty()
            st.markdown(response_text)

        st.session_state.messages.append({"role": "assistant", "content": response_text})

        if sow_data:
            doc_box = st.empty()
            doc_t0 = time.time()
            doc_box.info("📄 Generating CTRUH Word document with letterhead & tables...")
            try:
                docx_bytes = generate_sop_docx(sow_data)
                st.session_state.sop_bytes = docx_bytes
                st.session_state.sop_ready = True
                doc_elapsed = time.time() - doc_t0
                doc_box.success(f"✅ Document generated in {doc_elapsed:.1f}s!")
            except Exception as e:
                doc_box.error(f"❌ Document generation error: {str(e)}")

            st.rerun()


if __name__ == "__main__":
    run_app()
