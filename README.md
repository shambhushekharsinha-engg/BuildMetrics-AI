<div align="center">

<h1>🏗️ BuildMetrics-AI</h1>

<p><strong>AI-Powered Architectural Blueprint Generator</strong></p>
<p><em>From a plain-language description to a quantified, code-compliant 2D/3D building blueprint — in seconds.</em></p>

<br/>

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.20+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-316192?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

<br/>

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [What It Does](#-what-it-does)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Deployment](#-deployment)
- [Security](#-security)
- [Testing & CI](#-testing--ci)
- [Research Foundation](#-research-foundation)
- [Engineering Disclaimer](#-engineering-disclaimer)
- [Team](#-team)

---

## 🔍 Overview

**BuildMetrics-AI** is a production-grade AI platform built for architectural and civil engineering use cases. It turns a natural-language building description into a complete, quantified design package:

| Output | Description |
|--------|-------------|
| 📐 **2D Blueprint** | CAD-style floor plan with room dimensions, door/window placement, egress paths, and code-compliance overlays |
| 🏙️ **3D WebGL Model** | Interactive Three.js viewer with PBR materials, sun-path lighting, X-ray toggle, and per-floor isolation |
| 📊 **Bill of Quantities** | NLP-standardized material/labour/equipment line items with multi-currency cost totals |
| 📁 **Exports** | PNG · SVG · PDF · OBJ · STL · glTF (AR-ready) |
| 🤖 **AI Chat** | Google Gemini–powered agentic architect for iterative design refinement |

> **What sets this apart from AI image generators**: every visual element is directly traceable to a computed structural or cost number — BOQ totals, structural schedules, code-compliance checks. The quantified rigor is the product.

---

## 🚀 What It Does

### 🏗️ Design Generation
- Accepts a plain-English building prompt via a **4-step Guided Wizard** (Plot → Requirements → Style → Review)
- Constraint-based layout engine handles room adjacency, structural grid alignment, egress routing, and multi-floor stacking
- Supports: Residential · Commercial · Industrial · Modern · Classical architectural styles

### 📐 2D Blueprint Engine
- Line-weight hierarchy matching professional CAD standards (exterior walls `3.0pt`, interior `2.0pt`, annotations `0.5pt`)
- **NBC India 2016** and **IBC 2021** code-compliance checks rendered as coloured advisory overlays
- Checks include: habitable room area/width, door egress width, stair riser/tread ratios
- Full title block with project metadata

### 🏙️ 3D Visualization Engine
- **PBR materials** (`MeshStandardMaterial`) — glass, concrete, brick respond to light realistically
- **Sun-path daylighting** — time-of-day slider drives a directional light with dynamic shadows
- **X-ray / section mode** — structural opacity drops to 0.3 for interior inspection
- **Raycasting tooltips** — click any room, column, or beam to surface real cost/load/span values
- **glTF export** — opens in mobile AR applications

### 💰 Cost & BOQ Engine
- Scikit-learn regression model for cost prediction (trained on construction data)
- NLP BOQ standardizer aligns free-text work descriptions to standard cost indexes (82.96% QS agreement rate)
- Multi-currency support: INR · USD · EUR
- Persistent metrics bar: Footprint · Built Area · Est. Cost · Timeline · Compliance

### 🔐 Security
- `bcrypt` password hashing with per-user auto-salting
- Brute-force lockout after 5 failed login attempts
- Signed session tokens with TTL expiry
- CORS origin allowlist via FastAPI middleware
- Zero hardcoded credentials — all secrets via `.env` or `st.secrets`

---

## 🏛️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         User (Browser)                           │
└──────────────────────────────┬───────────────────────────────────┘
                               │ HTTPS
┌──────────────────────────────▼───────────────────────────────────┐
│              Streamlit Frontend  (app.py)                         │
│                                                                  │
│   Guided Wizard  ──►  2D Blueprint View  ──►  3D WebGL Viewer    │
│                            │                       │             │
└────────────────────────────┼───────────────────────┼────────────┘
                             │    REST (JSON/Pydantic) │
┌────────────────────────────▼───────────────────────▼────────────┐
│              FastAPI Backend  (api.py)                            │
│                                                                  │
│   POST /generate  ·  GET /render/2d  ·  GET /render/3d           │
│   POST /export/{format}                                          │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                  build_matrix  package                    │  │
│   │  input_handler → layout_engine → engineering             │  │
│   │                    ↓                    ↓                │  │
│   │              drawing_2d          rendering_3d → exporter  │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   In-memory MODEL_STORE (UUID-keyed, TTL-evicted)               │
│   Structured JSON logging  ·  X-Request-ID tracing              │
└───────────────────────────────┬──────────────────────────────────┘
                                │ SQLAlchemy ORM + QueuePool
┌───────────────────────────────▼──────────────────────────────────┐
│             PostgreSQL  +  Alembic versioned migrations           │
│         Tables: users  ·  projects  ·  projects_log              │
└──────────────────────────────────────────────────────────────────┘
```

**Docker Compose** orchestrates all three services with health-check–gated startup:
`pg_isready` (Postgres) → `/docs` liveness (FastAPI) → Streamlit

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit 1.20+, Three.js (WebGL), custom CSS |
| **Backend API** | FastAPI 0.95+, Uvicorn, Pydantic v2 |
| **AI / NLP** | Google Gemini AI, Scikit-learn |
| **2D Rendering** | Matplotlib, OpenCV (headless), SVGWrite, Pillow |
| **3D Rendering** | Three.js, Trimesh (OBJ / STL / glTF) |
| **Cost Model** | Scikit-learn, Pandas, Joblib |
| **Data Layer** | PostgreSQL 14+, SQLAlchemy 2.0+, Alembic, psycopg2 |
| **Security** | bcrypt 4.0+, signed JWT sessions |
| **Observability** | python-json-logger, X-Request-ID headers |
| **Containers** | Docker (multi-stage), Docker Compose |
| **CI/CD** | GitHub Actions (lint → typecheck → test → build) |
| **Dependencies** | pip-tools (`requirements.in` → pinned `requirements.txt`) |

---

## 🗂️ Project Structure

```
BuildMetrics-AI/
│
├── build_matrix/               # Core compute — pure logic, no UI dependency
│   ├── models.py               # Data models: ArchitecturalStyle, Blueprint2DConfig, BuildingModel
│   ├── input_handler.py        # NLP prompt parser + server-side input validation
│   ├── layout_engine.py        # Constraint-based room layout engine
│   ├── drawing_2d.py           # 2D renderer: line weights, compliance overlays, title block
│   ├── rendering_3d.py         # Three.js PBR engine: sun-path, X-ray, glTF, raycasting
│   ├── engineering.py          # Structural formulas (IS 456 / ACI 318 validated)
│   ├── exporter.py             # Multi-format export (PNG / SVG / PDF / OBJ / STL / glTF)
│   ├── labeling.py             # Room label and annotation engine
│   └── schemas.py              # Pydantic request/response schemas for FastAPI
│
├── app.py                      # Streamlit frontend: wizard, 3D viewer, AI chat
├── api.py                      # FastAPI service: endpoints, MODEL_STORE, CORS, logging
├── db.py                       # SQLAlchemy ORM: users, projects, repository layer
├── train_model.py              # ML cost model training
├── civil_math.py               # Structural formulas (unit-tested)
├── cost_engine.py              # BOQ cost calculation
├── export.py                   # Export helper utilities
├── blueprint_generator.py      # Blueprint generation helpers
│
├── Dockerfile                  # Multi-stage: builder → python:3.12-slim runtime
├── docker-compose.yml          # Streamlit + FastAPI + PostgreSQL + healthchecks
├── alembic/                    # Versioned database migration scripts
├── alembic.ini                 # Alembic config
├── .env.example                # Environment variable template
│
├── tests/                      # Pytest test suite
├── .github/workflows/ci.yml    # GitHub Actions CI pipeline
├── requirements.in             # Direct dependencies (pip-tools source)
├── requirements.txt            # Pinned, hash-locked manifest
│
├── PLAN.md                     # 10-phase engineering roadmap
└── walkthrough.md              # Production build walkthrough
```

---

## 🛠️ Getting Started

### Prerequisites

- **Python 3.12+**
- **Docker & Docker Compose** (recommended)
- **Google Gemini API Key** → [Get one at Google AI Studio](https://aistudio.google.com/)

---

### Option A — Docker Compose (Recommended)

```bash
# 1. Clone the repo
git clone https://github.com/shambhushekharsinha-engg/BuildMetrics-AI.git
cd BuildMetrics-AI

# 2. Set your secrets
cp .env.example .env
# Open .env and fill in GEMINI_API_KEY

# 3. Start all services
docker compose up --build
```

| Service | URL |
|---------|-----|
| Streamlit UI | http://localhost:8501 |
| FastAPI Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

---

### Option B — Local Dev (Bare-metal)

```bash
# 1. Install pinned dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Set GEMINI_API_KEY and DATABASE_URL

# 3. Apply database migrations
alembic upgrade head

# 4. Start FastAPI backend (Terminal 1)
uvicorn api:app --reload --port 8000

# 5. Start Streamlit frontend (Terminal 2)
streamlit run app.py
```

---

### Environment Variables

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Database — use Postgres URL for Docker, or leave commented for local SQLite
DATABASE_URL=postgresql://buildmetrics:supersecret@db:5432/buildmetrics

# API location (Docker uses service name; bare-metal uses localhost)
API_BASE_URL=http://api:8000
```

---

## 📦 Deployment

| Platform | Path | Notes |
|----------|------|-------|
| **Docker Compose** | `docker compose up --build` | ✅ Fully working locally |
| **Streamlit Cloud** | Connect GitHub repo, set secrets in dashboard | Fastest public path |
| **Render / Fly.io** | Single-container deploy, set env vars | No config changes needed |
| **AWS ECS / Fargate** | Separate `api` + `streamlit` tasks behind ALB | Scale path |
| **GCP Cloud Run** | Per-service containers, auto-TLS | Cloud-native scale path |

> HTTPS is handled by the hosting platform (ACM on AWS · automatic on Render/Fly/Cloud Run).

---

## 🔒 Security

| Control | How It Works |
|---------|-------------|
| Password storage | `bcrypt` — auto-salted per user; no plain-text or SHA-256 |
| Login protection | Account locked after 5 failed attempts (exponential backoff) |
| Credentials | All secrets via `.env` / `st.secrets` — zero hardcoded values |
| XSS | No user-controlled strings interpolated into raw HTML |
| Sessions | Signed tokens with TTL expiry; logout invalidates immediately |
| CORS | Origin allowlist enforced on all FastAPI routes |
| API input | Pydantic v2 validates every request body and query parameter |

---

## 🧪 Testing & CI

### Run Tests Locally

```bash
# Full test suite
pytest tests/ -v

# Syntax check across all modules
python -m compileall -q .
```

**What is tested:**
- Structural formulas in `civil_math.py` — validated against IS 456 / ACI 318 reference values
- Cost engine — multi-currency outputs (INR / USD / EUR)
- Layout engine — room count, no overlapping geometry, footprint constraints
- Database layer — in-memory fixture (no live Postgres needed)
- API — `/generate` → deserialization → `/render/3d` integration roundtrip

### CI Pipeline

Every pull request automatically runs:

```
ruff + black --check   →  code style
mypy                   →  static type checking
python -m compileall   →  syntax validation (catches import-time crashes)
pytest --cov           →  test suite with coverage report
docker build           →  container smoke test
```

---

## 📊 Development Roadmap

| Phase | What Was Built | Status |
|-------|----------------|--------|
| 1 — Security | bcrypt hashing, brute-force lockout, session tokens, XSS audit | ✅ Done |
| 2 — Data Layer | PostgreSQL, SQLAlchemy ORM, Alembic migrations, connection pooling | ✅ Done |
| 3 — API Decoupling | FastAPI service, Pydantic schemas, in-memory MODEL_STORE with TTL | ✅ Done |
| 4 — Engineering Integrity | Legal disclaimer, IS 456 unit tests, assumption docs, ML versioning | ✅ Done |
| 5 — Testing & CI | Unit + integration tests, GitHub Actions, pip-tools dependency pinning | ✅ Done |
| 6 — Containerisation | Multi-stage Dockerfile, Compose orchestration, pg health checks | ✅ Done |
| 7 — Observability | Structured JSON logging, X-Request-ID header tracing | ✅ Done |
| 8 — 2D Quality | Code-compliance overlays (NBC/IBC), line-weight hierarchy | 🔶 Partial |
| 9 — 3D Quality | PBR materials, sun-path lighting, X-ray mode, glTF export | ✅ Done |
| 10 — UI / UX | Guided wizard, persistent metrics bar, 3D raycasting traceability | ✅ Done |

---

## 📚 Research Foundation

Built on 7 peer-reviewed research papers (2024–2026):

| Paper | Year | Contribution to This Project |
|-------|------|------------------------------|
| *AI-Driven House Plan Generator* — Johnson et al. | 2025 | NLP prompt parsing → 2D layout (T5 / LLaMA / GAN) |
| *Integrating CV in Construction Estimations* — Rasheed et al. | 2024 | 2D-to-3D reconstruction pipeline (OpenCV + Blender API) |
| *Smart House Planner* — Dr. K. Jagadeesh | 2025 | End-to-end benchmark · Gemini AI + Three.js architecture |
| *Home Builder AI* — M. Venu | 2025 | Weather-adjusted scheduling · risk management module |
| *Floor Plans to Cost Estimates* — Kanjiya, Sonani, Zala | 2026 | Deep learning BOQ engine (Transformer U-Net segmentation) |
| *BUILDWISE Cost Estimation* — Verma, Sharma, Patel | 2026 | ML regression pricing (Random Forest + Gradient Boosting) |
| *AI-Augmented Cost Estimation NLP* — Jafary, Shojaei et al. | 2025 | BOQ standardizer: 82.96% Quantity Surveyor agreement rate |

Full literature review: `BuildMetrics_AI_7_Paper_Single_Table_Master.docx`

---

## ⚠️ Engineering Disclaimer

All outputs — floor plans, structural schedules, BOQ estimates, and cost projections — are **preliminary and AI-generated**.

They are intended for **informational and planning purposes only**. They do **not** constitute certified engineering documents and must be reviewed and signed off by a **licensed structural engineer or registered architect** before use in any construction, permitting, or procurement activity.

Structural formulas reference IS 456:2000 and ACI 318. Safety factors, load cases, and material grade defaults are documented in `ASSUMPTIONS.md`. These defaults may not apply to your site, soil type, seismic zone, or local regulations.

---

## 👨‍💻 Team

<div align="center">

**Greater Noida Institute of Technology**
Department of Computer Science & Engineering (AI & ML) · 3rd Year · 2024 Batch

</div>

---

<table width="100%">
<tr>

<td align="center" width="33%" valign="top">

### 👑 Shambhu Shekhar Sinha
**Lead Developer & Architect**

[![GitHub](https://img.shields.io/badge/GitHub-%40shambhushekharsinha--engg-181717?style=flat-square&logo=github)](https://github.com/shambhushekharsinha-engg)

```
Enrollment  2401321530048
Institute   GNIOT, Greater Noida
Branch      CSE · AI & ML
```

**Built:**
- Full-stack architecture
- FastAPI + Streamlit + PostgreSQL
- Three.js 3D PBR engine
- 2D code-compliance overlays
- Docker, CI/CD, security hardening
- Google Gemini AI integration
- 10-phase engineering roadmap

</td>

<td align="center" width="33%" valign="top">

### 🤝 Vaibhav Kumar Tiwari
**Backend & AI Developer**

```
Enrollment  2401321530062
Institute   GNIOT, Greater Noida
Branch      CSE · AI & ML
```

**Built:**
- ML cost regression model
- NLP BOQ standardizer
- Gemini AI prompt engineering
- Scikit-learn training pipeline
- AI/ML research integration

</td>

<td align="center" width="33%" valign="top">

### 🤝 Rishu Raj
**Data & Research Developer**

```
Enrollment  2402321530040
Institute   GNIOT, Greater Noida
Branch      CSE · AI & ML
```

**Built:**
- PostgreSQL + SQLAlchemy ORM
- Alembic migration scripts
- Testing framework setup
- 7-paper literature review
- Technical documentation

</td>

</tr>
</table>

---

<div align="center">

| Metric | Value |
|--------|-------|
| API Endpoints | `/generate` · `/render/2d` · `/render/3d` · `/export/{format}` |
| Export Formats | PNG · SVG · PDF · OBJ · STL · glTF |
| Research Papers | 7 (2024 – 2026) |
| Engineering Phases | 10 completed (9 full · 1 partial) |
| Code Standards | IS 456:2000 · ACI 318 · NBC India 2016 · IBC 2021 |

<br/>

*Built at GNIOT · September 2026*

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Gemini AI](https://img.shields.io/badge/Gemini_AI-4285F4?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com)
[![Three.js](https://img.shields.io/badge/Three.js-000000?style=flat-square&logo=three.js&logoColor=white)](https://threejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)

</div>
