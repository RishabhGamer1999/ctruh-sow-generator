# 📋 SOP / SOW Generator

An internal, AI-powered tool for automatically generating **Scope of Project (SOP)** and **Scope of Work (SOW)** documents from client requirements. Runs 100% locally — no data leaves your server.

---

## ✨ Features

- **Chat-based interface** — just describe the project and the AI asks the right questions
- **Upload client requirement docs** — automatically extracts project details from `.docx` files
- **RAG Knowledge Base** — learns from your past SOPs, pricing tables, and company policies
- **Export to DOCX** — professional, formatted document ready to send
- **100% private** — powered by a local LLM (Mistral/Llama), no external API calls

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed

### First-Time Setup

```bash
# 1. Start all services
docker-compose up -d

# 2. Pull AI models (one-time, ~4-5 GB download)
docker exec sop-ollama ollama pull mistral:7b
docker exec sop-ollama ollama pull nomic-embed-text

# 3. Open the app
# → http://localhost:8501
```

**On Windows**: double-click the scripts in the `scripts/` folder instead.

---

## 🗃️ Adding Your Knowledge Base

Drop your company documents into the relevant folders, then click **"Re-index Knowledge Base"** in the app sidebar:

```
knowledge_base/
├── past_sops/     ← Previous SOW/SOP documents (.docx, .pdf) — used for structure & terms reference
├── pricing/       ← (Optional) Rate cards for reference only — pricing is always confirmed with the user in chat
└── policies/      ← Company policies, standard terms (.docx, .pdf, .txt)
```

> ⚠️ These folders are excluded from Git (see `.gitignore`) to protect sensitive data.

---

## 🖥️ Daily Usage

```bash
# Start
docker-compose up -d

# Stop
docker-compose down
```

Or use the `.bat` scripts in `scripts/` on Windows.

---

## ⚙️ Configuration

Edit `.env` to change settings:

```env
LLM_MODEL=mistral:7b          # or llama3.2:3b for lower RAM usage
EMBEDDING_MODEL=nomic-embed-text
```

---

## 📁 Project Structure

```
sop-generator/
├── docker-compose.yml         # Orchestrates all services
├── .env                       # Configuration
├── app/
│   ├── main.py                # Streamlit chat UI
│   ├── config.py              # Central config
│   ├── agents/
│   │   ├── sop_agent.py       # LangChain conversational agent
│   │   └── prompts.py         # System prompts (edit to customize tone)
│   ├── rag/
│   │   ├── ingestor.py        # Indexes knowledge base into ChromaDB
│   │   └── retriever.py       # Queries the knowledge base
│   └── document/
│       ├── parser.py          # Parses client requirement .docx files
│       └── generator.py       # Generates the final SOP .docx
├── knowledge_base/            # Your company documents (not committed to Git)
├── outputs/                   # Generated SOPs (not committed to Git)
└── scripts/                   # Windows helper scripts
```

---

## 🌐 Deploying to Oracle Cloud (Always Free)

See [ORACLE_DEPLOY.md](./ORACLE_DEPLOY.md) for a step-by-step guide to hosting this on Oracle Cloud's free tier, accessible from any device anywhere.

---

## 🔒 Privacy & Security

- The LLM runs **locally** via [Ollama](https://ollama.ai) — no API calls to OpenAI or any external service
- ChromaDB stores embeddings **locally** on your server
- Your documents **never leave** your server infrastructure
- The `.gitignore` prevents accidental commits of sensitive documents
