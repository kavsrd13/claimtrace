# ClaimTrace

> Side-by-side document comparison with AI-powered Q&A and keyboard-navigable ClaimTrace citations.

[![CI](https://github.com/YOUR_ORG/claimtrace/actions/workflows/azure-deploy.yml/badge.svg)](https://github.com/YOUR_ORG/claimtrace/actions/workflows/azure-deploy.yml)

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Running the App](#running-the-app)
- [Keyboard Navigation](#keyboard-navigation)
- [Running Tests](#running-tests)
- [Repository Hygiene](#repository-hygiene)
- [Azure Deployment](#azure-deployment)
- [Known Limitations](#known-limitations)

---

## Features

| Feature | Description |
|---|---|
| **Two-document comparison** | Upload two TXT/PDF/DOCX files; view a structured diff side-by-side |
| **ClaimTrace citations** | Every AI answer includes inline citations linking back to source paragraphs |
| **Keyboard navigation** | Navigate citations with `Tab`, open with `Enter`, close with `Escape` |
| **Q&A** | Ask questions grounded in your documents; unsupported questions are politely declined |
| **Session management** | Each session is isolated and expires after 24 h |
| **Security** | Prompt-injection detection, forbidden file types, upload size limits |
| **Azure-ready** | Single App Service (B1+), no separate infrastructure required |

---

## Architecture

```
Browser (React 18 + Vite)
        │
        ▼
FastAPI + Uvicorn  (port 8000)
        ├── /api/sessions
        ├── /api/sessions/{id}/documents
        ├── /api/sessions/{id}/compare
        ├── /api/sessions/{id}/ask
        └── /*  →  serves React static build
                │
                ├── SQLite (dev) / Azure SQL or Postgres (prod)
                └── Azure OpenAI  (chat + embeddings)
```

---

## Prerequisites

- Python ≥ 3.11
- Node.js ≥ 20 (LTS)
- An **Azure OpenAI** resource with:
  - A chat deployment (e.g. `gpt-4o`)
  - An embedding deployment (e.g. `text-embedding-3-small`)

---

## Local Setup

```bash
# 1. Clone
git clone https://github.com/YOUR_ORG/claimtrace.git
cd claimtrace

# 2. Copy and fill in environment variables
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# 3. Backend – create virtual environment and install dependencies
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cd ..

# 4. Frontend – install dependencies
cd frontend
npm ci
cd ..
```

---

## Running the App

### Option A – Two terminals (development)

**Terminal 1 – Backend:**
```bash
cd backend
.venv\Scripts\activate   # or: source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 – Frontend (hot-reload):**
```bash
cd frontend
npm run dev
# Opens http://localhost:5173
```

### Option B – Production mode (single server)

```bash
# Build frontend into backend/static/
cd frontend && npm run build && cd ..

# Serve everything from FastAPI
cd backend
.venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000
# Open http://localhost:8000
```

---

## Keyboard Navigation

ClaimTrace citation overlays are fully keyboard-accessible:

| Key | Action |
|---|---|
| `Tab` | Move focus to the next citation marker |
| `Shift+Tab` | Move focus to the previous citation marker |
| `Enter` or `Space` | Open the citation detail panel |
| `Escape` | Close the open citation panel |
| `Tab` (inside panel) | Navigate links within the panel |

---

## Running Tests

```bash
# Backend – lint + tests
cd backend
.venv\Scripts\activate
ruff check .
ruff format --check .
pytest -v --cov=. --cov-report=term-missing

# Frontend – lint + tests + build
cd frontend
npm run lint
npm run test
npm run build
```

---

## Repository Hygiene

```bash
# Check repo size, detect secrets, verify forbidden paths
python scripts/check_repo_size.py
```

The script:
- Fails if tracked files exceed **9 MB**
- Lists the 20 largest tracked files
- Scans text files for common secret patterns (API keys, tokens, etc.)
- Verifies no forbidden paths (uploads/, *.db, coverage/, node_modules/, .venv/) are tracked

---

## Azure Deployment

### Manual

```bash
# 1. Build frontend
cd frontend && npm run build && cd ..

# 2. Zip the app
# Include: backend/, scripts/, .env.example, azure/startup.sh
# Exclude: .venv/, node_modules/, *.db, uploads/

# 3. Deploy
az webapp deploy --resource-group YOUR_RG --name YOUR_APP_NAME \
  --src-path claimtrace.zip --type zip

# 4. Set App Settings (replaces .env)
az webapp config appsettings set \
  --resource-group YOUR_RG --name YOUR_APP_NAME \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://..." \
    AZURE_OPENAI_API_KEY="..." \
    AZURE_OPENAI_API_VERSION="2024-02-01" \
    AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4o" \
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-small" \
    DATABASE_URL="sqlite:///./claimtrace.db" \
    SECRET_KEY="$(openssl rand -hex 32)"
```

### CI/CD (GitHub Actions)

Push to `main` branch triggers the workflow in `.github/workflows/azure-deploy.yml`.

Set these **GitHub Secrets**:
- `AZURE_CREDENTIALS`
- `AZURE_WEBAPP_NAME`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_CHAT_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `SECRET_KEY`
- `DATABASE_URL`

---

## Known Limitations

| Limitation | Detail |
|---|---|
| SQLite in production | Fine for single-instance App Service; swap `DATABASE_URL` for Postgres for multi-instance |
| File size | 10 MB per upload; very large PDFs may time out on text extraction |
| Embedding search | Uses cosine similarity over in-memory numpy arrays; not persisted across restarts |
| Session storage | Sessions are stored in SQLite; deleted on App Service restart unless using persistent storage |
| Rate limits | Depends on Azure OpenAI quota; add retry logic for production |

---

## Branch

The canonical branch is **`main`**.
