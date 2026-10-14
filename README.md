<div align="center">

# 🏗️ BuildMetrics AI
### Autonomous AI-Powered Architectural CAD, Structural Engineering & OpenBIM Studio

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35.0-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Three.js](https://img.shields.io/badge/Three.js-r128-000000?logo=three.js&logoColor=white)](https://threejs.org)
[![AutoCAD DXF](https://img.shields.io/badge/AutoCAD-DXF_R12-E51937?logo=autodesk&logoColor=white)](https://www.autodesk.com)
[![OpenBIM IFC4](https://img.shields.io/badge/OpenBIM-IFC4_ISO_10303--21-005A9C?logo=buildingSMART&logoColor=white)](https://www.buildingsmart.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-5.x-37814A?logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI Pipeline](https://img.shields.io/badge/CI-Passing-brightgreen?logo=github-actions&logoColor=white)](https://github.com/shambhushekharsinha-engg/BuildMetrics-AI/actions)

*Transform a single natural-language text prompt into production-ready 2D CAD blueprints, interactive 3D WebGL scenes, OpenBIM IFC models, IS 456 structural schedules, geotechnical foundation designs, Vastu spatial audits, and CSI MasterFormat cost estimates in seconds.*

[Quick Start](#-quick-start) · [Features](#-core-features) · [CAD & BIM](#-cad--openbim-interoperability) · [Architecture](#-system-architecture) · [API Endpoints](#-api-endpoints) · [Testing](#-running-tests)

</div>

---

## 🌟 Core Features

BuildMetrics AI integrates architectural layout synthesis, civil structural mechanics, geotechnical engineering, ancient spatial harmony (Vastu Shastra), environmental sustainability, and financial quantity takeoff into a unified engineering platform.

| Domain | Capabilities |
| :--- | :--- |
| **🤖 Autonomous AI Design** | Natural language prompt synthesis (Gemini 2.5 Flash), conversational architectural redesign, real-time diff tracking, and prompt undo/revision history (last 5 designs). |
| **📐 2D CAD Blueprint Studio** | CAD-grade vector floor plan rendering across 6 themes (*Classic Blueprint*, *Architectural Dark*, *Paper White*, *Japandi Earth*, *Scandinavian Light*, *Tropical Emerald*). Includes dimension strings, beam/column structural grids, door swing arcs, plumbing fixtures, scale rulers, and title blocks. |
| **🏗️ 3D WebGL Visualizer** | High-performance Three.js viewer with a floating Quick-Action Bar (`🔄 Orbit`, `📐 2D Top`, `🏢 Front Elevation`, `🚶 First-Person Walkthrough`, `🏠 Roof Toggle`, `☀️ Day/Night Sun Cycle`, `📸 HD Snapshot`). |
| **🏢 OpenBIM & CAD Interoperability** | **Native AutoCAD DXF (`.dxf`)** ASCII export and **Industry-Standard OpenBIM IFC4 (`.ifc`)** generation compatible with Autodesk Revit, ArchiCAD, Solibri, FreeCAD, and Blender. |
| **🧱 IS 456 / ACI 318 Structural Mechanics** | Column axial tributary service load accumulation ($P_u$), structural safety factors ($FS$), column & beam rebar schedules, design bending moment ($M_u = \frac{w_u L^2}{8}$), and serviceability deflection checks ($L/250$). |
| **🌍 Geotechnical & Soil Engineering** | 5 regional soil profiles (*Hard Rock*, *Medium Sand*, *Stiff Clay*, *Black Cotton Expansive Soil*, *Soft Marine Clay*), Safe Bearing Capacity (SBC in kPa), footing base contact area, foundation depth, excavation bulk volumetrics ($m^3$), and IS 1893 seismic hazard detailing (Zone II to Zone V). |
| **🧭 Vastu Shastra & Spatial Harmony** | 9-sector *Vastu Purusha Mandala* orientation audit ($0\text{–}100$ score, $A+/A/B/C$ auspicious grade), 5-element (*Pancha Bhoota*) balance index (Water, Fire, Earth, Air, Space), *Brahmasthan* core clearance verification, and remedial advice. |
| **💰 Dynamic BOQ & Multi-Currency** | CSI MasterFormat 2016 division mapping with interactive live sliders for material rates (Steel, Concrete, Masonry, Glass, Flooring, MEP, Labor). Live currency switcher supporting **USD (\$)**, **INR (₹)**, **EUR (€)**, **GBP (£)**, **AED (د.إ)**, **CAD (CA\$)**, and **AUD (AU\$)**. |
| **🌱 Eco & LEED Sustainability** | Formula-driven rooftop solar PV generation potential (kWh/mo), rainwater harvesting cistern sizing, embodied carbon emissions ($tCO_2e$), and LEED certification rating (Certified, Silver, Gold, Platinum). |
| **🌦️ Meteorological Risk Management** | Predictive construction timeline modeling calibrated against 6 global climate zones (*Tropical Monsoon*, *Arid Desert*, *Temperate*, *Cold Continental*, *Mediterranean*, *Tropical Humid*). |
| **⚡ Turbo Direct Engine** | Seamless 0ms in-memory fallback engine that ensures 100% platform availability even when remote microservices or cloud workers are cold or unreachable. |

---

## 📐 CAD & OpenBIM Interoperability

BuildMetrics AI exports directly to standard industry vector and BIM formats without requiring proprietary desktop CAD software:

```
                  ┌────────────────────────────────────────┐
                  │          BuildMetrics AI Core          │
                  │        Generative BIM & CAD            │
                  └──────────────────┬─────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌──────────────────┐       ┌──────────────────┐        ┌──────────────────┐
│   AutoCAD DXF    │       │   OpenBIM IFC4   │        │ 3D Mesh & Vector │
│   (.dxf ASCII)   │       │ (.ifc ISO-10303) │        │ (OBJ, SVG, PDF)  │
└────────┬─────────┘       └────────┬─────────┘        └────────┬─────────┘
         │                          │                           │
         ▼                          ▼                           ▼
AutoCAD, LibreCAD,         Autodesk Revit, ArchiCAD,   WebGL Three.js, SketchUp,
Vectorworks, CorelCAD      Solibri, BlenderBIM, FreeCAD  High-Resolution Plotters
```

- **AutoCAD DXF (Drawing Exchange Format):** Layered R12/2000 ASCII CAD standard with designated layers:
  - `A-WALL-EXT`: Exterior boundary walls (0.35mm lineweight)
  - `A-WALL-INT`: Interior partition walls (0.20mm lineweight)
  - `A-COLS`: Structural reinforced concrete columns (0.50mm lineweight)
  - `A-BEAM`: Structural grid beams (dashed lines)
  - `A-DOOR` & `A-WIND`: Door openings with swing arcs and window glazing
  - `A-ROMS` & `A-DIMS`: Room text labels with metric areas and plot boundary dimensions
- **OpenBIM IFC4 (ISO 10303-21 STEP):** True semantic building information modeling containing `IfcProject`, `IfcSite`, `IfcBuilding`, `IfcBuildingStorey`, `IfcWallStandardCase`, `IfcColumn`, `IfcBeam`, `IfcSlab`, and `IfcSpace`.

---

## ⚡ Quick Start

### 1. Docker Compose (Full Stack Recommended)

> **Prerequisites**: [Docker Desktop](https://www.docker.com/) installed.

```bash
# 1. Clone repository
git clone https://github.com/shambhushekharsinha-engg/BuildMetrics-AI.git
cd BuildMetrics-AI

# 2. Configure environment
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# 3. Spin up full microservice cluster
docker compose up --build -d

# 4. Access the platforms
#    Streamlit UI:     http://localhost:8501
#    FastAPI Swagger:  http://localhost:8000/docs
#    Prometheus:       http://localhost:9090
#    Grafana:          http://localhost:3000
```

### 2. Local Bare-Metal Development

```bash
# Install pinned production dependencies
pip install -r requirements.txt

# Configure environment variables
export GEMINI_API_KEY="your-api-key"
export DATABASE_URL="sqlite:///buildmetrics.db"
export API_BASE_URL="http://localhost:8000"

# Terminal 1 — FastAPI Backend
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Streamlit Frontend Studio
streamlit run app.py --server.port 8501

# Terminal 3 — Celery Background Worker (Optional)
celery -A worker.celery_app worker --loglevel=info
```

---

## 🏛️ System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Streamlit Studio :8501<br/>app.py]
        TURBO[⚡ Turbo Direct In-Memory Engine]
    end

    subgraph "Backend API Layer"
        API[FastAPI :8000<br/>api.py]
        AUTH[Bcrypt Auth & Rate Limiting]
        PROM[Prometheus Instrumentator]
    end

    subgraph "Core Engineering Engines"
        LEN[Layout Engine<br/>BSP Floor Plan Synthesis]
        ENG[Engineering Engine<br/>IS 456 Structural & Deflection]
        GEO[Geotech Engine<br/>Soil Mechanics & SBC Analysis]
        VAS[Vastu Engine<br/>9-Zone Mandala Audit]
        ECO[Eco Engine<br/>LEED & Solar Volumetrics]
        DXF[CAD Engine<br/>Layered AutoCAD DXF]
        IFC[OpenBIM Engine<br/>ISO 10303-21 IFC4]
    end

    subgraph "Workers & Storage"
        WORKER[Celery Worker<br/>Async Export Pipeline]
        REDIS[(Redis 7<br/>Model Store & Broker)]
        PG[(PostgreSQL / SQLite<br/>User DB & Projects)]
    end

    UI --> API
    UI -.->|Zero-Lag Fallback| TURBO
    TURBO --> LEN
    API --> AUTH --> LEN
    LEN --> ENG
    LEN --> GEO
    LEN --> VAS
    LEN --> ECO
    LEN --> DXF
    LEN --> IFC
    API --> WORKER --> REDIS
    API --- PG
    API --- REDIS
```

---

## 🔌 API Endpoints

All endpoints are self-documenting and interactive via Swagger UI at `/docs`.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/healthz` | Kubernetes/Docker container liveness probe |
| `GET` | `/api/v1/version` | Active service version, Git SHA, and deployment environment |
| `POST` | `/api/v1/generate` | Generates a complete `BuildingModel` from a natural-language prompt |
| `POST` | `/api/v1/render/2d` | Renders a high-resolution 2D CAD blueprint PNG |
| `POST` | `/api/v1/render/3d` | Generates interactive Three.js WebGL HTML viewport |
| `POST` | `/api/v1/export` | Synchronous export (`png`, `svg`, `pdf`, `dxf`, `ifc`, `obj`, `gltf`, `bundle`) |
| `POST` | `/api/v1/export/async` | Queues async background export task via Celery |
| `GET` | `/api/v1/export/status/{id}`| Polls Celery background export task status |
| `GET` | `/api/v1/download` | Streams generated CAD/BIM archive to client |
| `GET` | `/metrics` | Prometheus metrics scrape endpoint (`ops`) |

---

## 🧪 Running Tests

The test suite includes unit, integration, civil mechanics, CAD, and smoke tests:

```bash
# Run the complete test suite
pytest tests/ -v

# Run with coverage reporting
pytest --cov=build_matrix --cov=api --cov=cost_engine

# Run specific CAD & BIM test suites
pytest tests/test_dxf_geotech_vastu.py tests/test_ifc.py -v

# Strict code quality check
ruff check .
```

---

## 📋 Comprehensive Changelog

### v1.2.0 — Enterprise Civil, Geotechnical & BIM Release (October 2026)
* 🏛️ **OpenBIM IFC4 Generation:** Implemented [`build_matrix/cad_ifc.py`](build_matrix/cad_ifc.py) generating standard ISO-10303-21 STEP files for seamless import into Autodesk Revit and ArchiCAD.
* 📐 **Native AutoCAD DXF Exporter:** Added [`build_matrix/cad_dxf.py`](build_matrix/cad_dxf.py) with 9 standard architectural layers and universal R12 compatibility.
* 🌍 **Geotechnical Soil Mechanics Engine:** Integrated [`build_matrix/geotech_engine.py`](build_matrix/geotech_engine.py) modeling 5 soil types, Safe Bearing Capacity (SBC), excavation volumes, and IS 1893 seismic detailing.
* 🧭 **Vastu Shastra Spatial Harmony Engine:** Added [`build_matrix/vastu_engine.py`](build_matrix/vastu_engine.py) evaluating 9-zone directional orientations, 5 elements balance, and Brahmasthan core clearance.
* ⚡ **Structural Load Distribution:** Implemented tributary load accumulation, safety factors ($FS$), critical beam bending moments ($M_u$), and $L/250$ deflection serviceability limits in [`build_matrix/engineering.py`](build_matrix/engineering.py).
* 💱 **Multi-Currency Pricing & Live Calibration:** Integrated real-time currency conversion (**USD, INR, EUR, GBP, AED, CAD, AUD**) and dynamic material rate calibration sliders.
* 🛡️ **Zero-Defect Quality Gates:** 63 passing unit tests, 100% green GitHub Actions CI pipeline, and Ruff strict lint compliance.

### v1.1.0 — Observability, Rate Limiting & UI Upgrades
* 🛡️ **SlowAPI Rate Limiting:** Added remote-address rate limiting (`60/min` on generation/export).
* 📊 **Prometheus & Grafana Observability:** Integrated endpoint instrumentation at `/metrics`.
* 💾 **Redis-Backed Model Store:** Replaced ephemeral in-memory dictionary with Redis caching and TTL cleanup.
* 🕹️ **Floating 3D Quick-Action Bar:** Streamlined Three.js viewer with intuitive HUD buttons for orbit, top-down, elevation, and daylight cycles.
* 🌿 **Value Engineering ROI:** Added CapEx savings, carbon offset, and annual utility payback calculations.

---

## ⚖️ Legal Disclaimer

All outputs generated by BuildMetrics AI — including blueprints, structural schedules, soil mechanics assessments, and Bill of Quantities — are **AI-assisted preliminary engineering estimates**. They must be reviewed, verified, and stamped by a **licensed professional structural engineer or registered architect** prior to permitting, procurement, or construction activity.

---

<div align="center">

**Built with 🏗️ by the BuildMetrics AI Engineering Team**

*Empowering Architects & Civil Engineers with Autonomous Generative Intelligence*

</div>
