# 📋 CTRUH SOW / Scope & Commercials Generator

An AI-powered web tool for automatically generating **CTRUH Scope of Work (SOW)** and **Project Scope & Commercials** documents from sales requirements and proposals. 

Hosted 24/7 in the cloud on **Streamlit Community Cloud** with **Groq AI** — 100% free, requiring zero credit cards and accessible from any device.

---

## ✨ Features

- **Conversational Chat Interface** — guides users through requirement gathering and project-specific pricing.
- **Requirement Document Reader** — uploads and extracts details from sales **Account Proposals** (`.pdf` or `.docx`).
- **Official CTRUH Format** — automatically builds and styles the 9-section CTRUH document:
  1. Project Objective
  2. Scope of Work
  3. Timeline Table & Turnaround Notes
  4. Iterations Included (2 Revision Rounds)
  5. Out of Scope Exclusions
  6. Acceptance Criteria (5-Day Approval Clause)
  7. Commercials & Infrastructure Add-on Table
  8. Client Inputs Required
  9. Approval Sign-off Blocks
- **Company Branding** — formatted with CTRUH letterhead, brand blue banners, and footer CIN/registered address.
- **RAG Knowledge Base** — references past SOWs, standard clauses, and company policies.
- **Instant DOCX Download** — generates ready-to-sign `.docx` Word documents on the fly.

---

## 🛠️ Tech Stack & Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Streamlit Community Cloud (Hosted 24/7)                    │
│  • Web Chat UI                                              │
│  • Account Proposal PDF / DOCX Parser                       │
│  • CTRUH Document Styler (python-docx)                      │
│  • In-Memory RAG Knowledge Base (ChromaDB + FastEmbed)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Groq Cloud AI Engine (Fast Inference)                      │
│  • Meta Llama 3.3 70B / Mistral                             │
│  • Privacy-preserving API (no training on your documents)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
ctruh-sow-generator/
├── streamlit_app.py           # Streamlit Cloud entrypoint
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── app/
│   ├── main.py                # Main Streamlit chat application & UI
│   ├── config.py              # Central configuration & secrets reader
│   ├── agents/
│   │   ├── sop_agent.py       # LangChain conversational SOW agent
│   │   └── prompts.py         # CTRUH system prompts & 9-section schema
│   ├── rag/
│   │   ├── ingestor.py        # Knowledge base document indexer
│   │   └── retriever.py       # FastEmbed + ChromaDB retriever
│   └── document/
│       ├── parser.py          # Account Proposal (PDF/DOCX) extractor
│       └── generator.py       # CTRUH DOCX letterhead & template builder
└── knowledge_base/
    ├── past_sops/             # Past CTRUH SOWs for reference
    ├── pricing/               # Commercial structures & rate cards
    └── policies/              # Company terms & standard policies
```

---

## 🚀 Deployment & Setup

### 1. Get a Free Groq API Key
1. Go to [console.groq.com](https://console.groq.com) and log in with Google (Free, no card required).
2. Go to **API Keys** → **Create API Key** and copy the key (`gsk_...`).

### 2. Deploy on Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and connect your GitHub account.
2. Select this repository (`ctruh-sow-generator`), set the main file to `streamlit_app.py`.
3. In **Advanced settings** → **Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_groq_key_here"
   ```
4. Click **Deploy!**

---

## 🔒 Privacy & Security

- **No Public Leaks**: Runs through private API endpoints.
- **Zero Training on Data**: Groq's enterprise API terms ensure your internal proposals and client details are not retained or used for model training.
