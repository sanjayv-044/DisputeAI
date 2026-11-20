# 🏦 DisputeAI

### AI-Powered Banking Dispute Resolution & Fraud Investigation Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2019%20+%20Vite%208-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/Agentic%20AI-LangGraph%200.2+-FF6F00)](https://langchain-ai.github.io/langgraph/)
[![ChromaDB](https://img.shields.io/badge/Vector%20Store-ChromaDB-5C6BC0)](https://www.trychroma.com)
[![Redis](https://img.shields.io/badge/Queue-Redis-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Infra-Docker%20Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com)
[![Prometheus](https://img.shields.io/badge/Monitoring-Prometheus%20+%20Grafana-E6522C?logo=prometheus&logoColor=white)](https://prometheus.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **DisputeAI** is an enterprise-grade banking dispute management and fraud investigation platform.  
> It automates complaint triage, runs a **4-Agent LangGraph workflow**, performs **RAG-based regulatory compliance analysis** over official RBI circulars, and delivers role-isolated **Customer** and **Administrator** portals — all backed by a production-ready FastAPI + React stack.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Demo Credentials](#-demo-credentials)
- [API Reference](#-api-reference)
- [AI Agents](#-ai-agents)
- [RAG Pipeline](#-rag-pipeline)
- [Fraud Classification](#-fraud-classification)
- [Evaluation Results](#-evaluation-results)
- [Monitoring](#-monitoring)
- [RBI Regulatory Grounding](#-rbi-regulatory-grounding)
- [Contributing](#-contributing)

---

## ✨ Features

### 👤 Customer Portal
| Feature | Status |
|---|---|
| Registration & JWT Login | ✅ |
| Submit banking disputes with file uploads | ✅ |
| Real-time complaint status tracking | ✅ |
| View AI investigation results & risk score | ✅ |
| View fraud category & escalation status | ✅ |
| View RBI regulatory references | ✅ |
| View final resolution & recommendations | ✅ |

### 🛡️ Admin Portal
| Feature | Status |
|---|---|
| Secure admin login (role-isolated) | ✅ |
| Analytics dashboard (charts, KPIs) | ✅ |
| View all complaints with filters | ✅ |
| View full AI dossier per complaint | ✅ |
| Approve / reject AI recommendations | ✅ |
| Escalate complaints for human review | ✅ |
| Update status & add investigation remarks | ✅ |
| View evaluation metrics | ✅ |
| Prometheus + Grafana monitoring panel | ✅ |

### 🤖 AI & Backend
| Feature | Status |
|---|---|
| 5-category fraud classification (100% benchmark accuracy) | ✅ |
| 4-Agent LangGraph workflow (Investigate → Verify → Assess → Recommend) | ✅ |
| RAG over RBI circulars via ChromaDB | ✅ |
| Asynchronous AI processing (Redis / BackgroundTasks fallback) | ✅ |
| 20-scenario evaluation benchmark | ✅ |
| Prometheus metrics + Grafana dashboards | ✅ |
| Locust load testing | ✅ |
| Docker Compose full-stack deployment | ✅ |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        React + Vite Frontend                      │
│           Customer Portal          │         Admin Portal          │
└───────────────────┬────────────────┴──────────────┬──────────────┘
                    │  REST / JWT                    │
┌───────────────────▼────────────────────────────────▼──────────────┐
│                      FastAPI Backend (Python 3.12)                 │
│   Auth · Disputes · Files · Admin · Evaluation · Metrics APIs      │
└──────┬─────────────────────────────┬──────────────────────────────┘
       │ SQLite (SQLAlchemy ORM)      │ Redis (Celery tasks)
       │                             │
┌──────▼─────────────────────────────▼──────────────────────────────┐
│                      AI Processing Layer                           │
│                                                                    │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────────┐  │
│  │  Fraud       │  │  LangGraph  │  │   RAG Pipeline           │  │
│  │  Classifier  │  │  4-Agent    │  │   ChromaDB + RBI PDFs    │  │
│  │  (5 classes) │  │  Workflow   │  │   Gemini / Local LLM     │  │
│  └──────────────┘  └─────────────┘  └──────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────┐
│  Prometheus + Grafana│  ← Monitoring
│  Locust              │  ← Load Testing
└──────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, Vite 8, Axios, Recharts |
| **Backend** | FastAPI 0.115, Uvicorn, SQLAlchemy, Pydantic v2 |
| **Database** | SQLite (dev) / PostgreSQL-ready |
| **Auth** | JWT (python-jose), bcrypt, RBAC |
| **AI Agents** | LangGraph 0.2, LangChain |
| **LLM** | Google Gemini API (with local fallback) |
| **Vector Store** | ChromaDB, Sentence-Transformers |
| **Queue** | Redis + Celery (BackgroundTasks fallback) |
| **Monitoring** | Prometheus, Grafana |
| **Load Testing** | Locust |
| **Containerization** | Docker, Docker Compose |

---

## 📁 Project Structure

```
DisputeAI/
├── backend/
│   ├── main.py                  # FastAPI app — 25+ routes
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic v2 schemas
│   ├── security.py              # JWT + bcrypt + RBAC
│   ├── database.py              # DB session & engine
│   ├── async_worker.py          # Celery/Redis + fallback
│   ├── evaluation_runner.py     # 20-scenario benchmark
│   ├── requirements.txt
│   └── Dockerfile
│
├── src/
│   ├── multi_agent_workflow.py  # LangGraph 4-Agent StateGraph
│   ├── fraud_classifier.py      # 5-category fraud classifier
│   ├── regulatory_tools.py      # ChromaDB RAG retrieval
│   ├── gemini_rag.py            # Gemini API + local fallback
│   ├── verification_agent.py    # Evidence & citation verifier
│   └── monitoring.py            # Prometheus metrics
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Router — dual portal
│   │   ├── App.css              # Navy-blue fintech design
│   │   ├── services/api.js      # Axios + JWT interceptor
│   │   ├── components/          # Sidebar, Navbar, StatCard, StatusBadge
│   │   └── pages/
│   │       ├── Login.jsx
│   │       ├── Register.jsx
│   │       ├── CustomerDashboard.jsx
│   │       ├── CustomerSubmitDispute.jsx
│   │       ├── CustomerTrackDisputes.jsx
│   │       ├── CustomerProfile.jsx
│   │       ├── AdminDashboard.jsx
│   │       ├── AdminDisputes.jsx
│   │       ├── AdminDisputeDetail.jsx
│   │       ├── AdminEvaluation.jsx
│   │       └── AdminMonitoring.jsx
│   └── package.json
│
├── documents/
│   ├── rbi_chunks.json          # Pre-chunked RBI circular data
│   └── chroma_db/               # ChromaDB vector store (auto-created)
│
├── monitoring/
│   ├── prometheus.yml
│   ├── grafana_dashboard.json
│   ├── grafana_datasources.yml
│   ├── grafana_dashboards.yml
│   └── locustfile.py
│
├── tests/
│   └── test_end_to_end.py       # 17-point integration test suite
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| Git | any |
| Redis (optional) | 7+ |
| Docker (optional) | 24+ |

---

### Option A — Manual (Recommended for Development)

#### 1. Clone the repository

```bash
git clone https://github.com/sanjayv-044/DisputeAI.git
cd DisputeAI
```

#### 2. Backend setup

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

#### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY
```

```env
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_very_secret_jwt_key_here
DATABASE_URL=sqlite:///./disputes.db
REDIS_URL=redis://localhost:6379/0
```

> **Get a free Gemini API key**: https://aistudio.google.com/app/apikey

#### 4. Seed the database

```bash
cd backend
python -c "
from database import engine, Base
from models import User, Dispute, EvidenceFile, InvestigationDossier, ComplaintHistory
import sys; sys.path.insert(0, '..')
Base.metadata.create_all(bind=engine)
print('Database tables created.')
"
```

#### 5. Start the backend

```bash
# From project root
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend is live at: http://localhost:8000  
Interactive API docs: http://localhost:8000/docs

#### 6. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend is live at: http://localhost:5173

---

### Option B — Docker Compose (Full Stack)

```bash
git clone https://github.com/sanjayv-044/DisputeAI.git
cd DisputeAI

# Copy and configure environment
cp .env.example .env
# Edit .env and set GEMINI_API_KEY

# Launch all services
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

---

## 🔑 Demo Credentials

> These credentials are pre-seeded when you create the database.

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@disputeai.bank` | `Admin@DisputeAI2026` |
| **Customer** | `customer@disputeai.bank` | `Customer@DisputeAI2026` |

> ⚠️ Change these credentials immediately in any production deployment.

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new customer |
| `POST` | `/api/auth/login` | Login (returns JWT) |
| `GET` | `/api/auth/me` | Get current user profile |

### Disputes (Customer)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/disputes/` | Submit new dispute |
| `GET` | `/api/disputes/` | List own disputes |
| `GET` | `/api/disputes/{id}` | Get dispute detail |
| `POST` | `/api/disputes/{id}/evidence` | Upload supporting document |

### Admin

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/disputes` | List all disputes |
| `GET` | `/api/admin/disputes/{id}` | Full dispute + AI dossier |
| `PUT` | `/api/admin/disputes/{id}/status` | Update status |
| `POST` | `/api/admin/disputes/{id}/escalate` | Escalate complaint |
| `POST` | `/api/admin/disputes/{id}/remarks` | Add investigation remark |
| `GET` | `/api/admin/analytics` | Dashboard analytics |

### AI & Evaluation

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/disputes/{id}/investigate` | Trigger AI investigation |
| `GET` | `/api/evaluation/run` | Run 20-scenario benchmark |
| `GET` | `/api/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |

Full interactive docs available at `/docs` (Swagger UI) and `/redoc`.

---

## 🤖 AI Agents

DisputeAI runs a **4-Agent LangGraph StateGraph** pipeline on every new complaint:

```
[START]
   │
   ▼
┌─────────────────────────────────┐
│  Agent 1: Investigation Agent   │  Analyzes complaint, identifies fraud type,
│                                 │  retrieves relevant RBI policies via RAG
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Agent 2: Verification Agent    │  Verifies evidence files, checks citations,
│                                 │  flags unsupported claims
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Agent 3: Liability Assessment  │  Assesses bank vs. customer liability,
│                                 │  applies RBI circular rules
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Agent 4: Recommendation &      │  Generates resolution recommendation,
│           Escalation Router     │  auto-escalates critical-risk cases
└────────────────┬────────────────┘
                 │
                [END] → Results stored in DB → Admin notified
```

Each agent outputs structured JSON that is persisted in the `investigation_dossiers` table and displayed in the Admin portal.

---

## 📚 RAG Pipeline

```
RBI Circulars (PDF)
       │
       ▼
  PDF Extraction  →  Text Chunking  →  Sentence-Transformer Embeddings
                                               │
                                               ▼
                                         ChromaDB Vector Store
                                               │
                                    Semantic Similarity Search
                                               │
                                    Retrieved Chunks + Metadata
                                               │
                                               ▼
                                      Gemini LLM Synthesis
                                               │
                                      Regulatory Analysis Output
```

**RBI Documents Indexed:**
- RBI/2017-18/15 — Customer Protection (Unauthorised Electronic Transactions)
- RBI Integrated Ombudsman Scheme 2026
- Master Directions on KYC
- UPI Operating Circular
- Banking Codes and Standards Board Guidelines

> The system **never fabricates** RBI references. All cited circulars are sourced from indexed documents only.

---

## 🔍 Fraud Classification

Five fraud categories with rule-based + semantic classification:

| Category | Description |
|---|---|
| **UPI Fraud** | Unauthorized UPI transfers, QR code scams, collect request fraud |
| **Credit/Debit Card Fraud** | Card skimming, CNP fraud, POS fraud |
| **Phishing Fraud** | Fake websites, SMS phishing, vishing, OTP theft |
| **Internet Banking Fraud** | Unauthorized net-banking access, credential theft |
| **Identity Theft** | Account takeover, synthetic identity fraud |

Each classification returns:
- **Fraud Category**
- **Risk Score** (0–100)
- **Risk Level**: Low / Medium / High / Critical
- **Complaint Priority**
- **Classification Explanation**

---

## 📊 Evaluation Results

| Benchmark | Scenarios | Score |
|---|---|---|
| Fraud Classification Accuracy | 20 | **100%** |
| RAG Retrieval Precision | 5 | **100%** |
| Agent Workflow Completion | 17 | **17/17 passed** |
| Evidence Verification | 20 | Operational |
| Citation Verification | 20 | Operational |

> Evaluation is run against 20 pre-defined scenarios covering all 5 fraud categories, edge cases, and escalation triggers.

---

## 📈 Monitoring

### Prometheus Metrics (`:8000/metrics`)
- `disputeai_requests_total` — API request count by endpoint and method
- `disputeai_request_duration_seconds` — Response time histogram
- `disputeai_active_requests` — Concurrent requests gauge
- `disputeai_disputes_total` — Disputes submitted by status
- `disputeai_ai_processing_seconds` — AI workflow duration

### Grafana Dashboard (`:3000`)
Default user/password: `admin` / `admin`

Pre-built dashboard panels:
- Request rate & error rate
- P95 / P99 response times
- AI processing duration
- Dispute submission trends

### Locust Load Testing

```bash
cd monitoring
locust -f locustfile.py --host=http://localhost:8000
```

Open Locust UI at http://localhost:8089

---

## 🔒 Security

| Feature | Implementation |
|---|---|
| Password hashing | bcrypt with salt rounds |
| Authentication | JWT (HS256), 24h expiry |
| Authorization | Role-based (customer / admin) scopes |
| Data isolation | Customers can only access own complaints |
| Input validation | Pydantic v2 strict models on all endpoints |
| File upload validation | MIME type and size checks |
| Secrets | `.env` file — never committed to git |
| Protected endpoints | All `/api/admin/*` require admin role |

---

## 📜 RBI Regulatory Grounding

DisputeAI implements and enforces:

**RBI/2017-18/15 DBR.No.Leg.BC.78/09.07.005/2017-18**  
*Customer Protection — Limiting Liability of Customers in Unauthorised Electronic Banking Transactions*

| Rule | Detail |
|---|---|
| Zero Liability | Third-party breach reported within 3 working days (Para 6) |
| Limited Liability | Capped liability for reports within 4–7 working days (Para 7, Table 1) |
| Customer Negligence | Full liability where OTP/credentials were disclosed (Para 7(i)) |
| Shadow Reversal | Mandatory credit within 10 working days of notification (Para 9) |
| Burden of Proof | Rests on the bank, not the customer (Para 12) |

**RBI Integrated Ombudsman Scheme 2026** — Escalation grounds and compensation timelines.

---

## 🧪 Running Tests

```bash
# Activate virtual environment first
venv\Scripts\activate   # Windows
source venv/bin/activate # macOS/Linux

# Run integration tests
python tests/test_end_to_end.py

# Run fraud classification benchmark
python src/fraud_classifier.py

# Run evaluation suite
python backend/evaluation_runner.py
```

Expected output: **17/17 tests passed**

---

## 🐳 Docker Services

```yaml
services:
  backend:   # FastAPI on :8000
  frontend:  # React/Nginx on :5173
  redis:     # Redis on :6379
  prometheus: # Prometheus on :9090
  grafana:   # Grafana on :3000
```

---

## 🤝 Contributing

This project was built as a team academic demonstration. If you'd like to contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push to your branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 👥 Team

| Member | Contribution |
|---|---|
| Member 1 | Frontend (React + Vite), Backend (FastAPI), Database, Redis, Docker |
| Member 2 | Fraud Classifier, RAG Pipeline, ChromaDB, LangGraph Investigation Agent |
| Member 3 | Verification Agent, Liability Assessment, Evaluation, Monitoring |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <strong>Built with ❤️ for AI-powered banking compliance and fraud investigation</strong><br/>
  <sub>DisputeAI · 2026 · FastAPI · React · LangGraph · ChromaDB · RBI Compliant</sub>
</div>
