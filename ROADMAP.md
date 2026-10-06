# BuildMetrics AI — Product Roadmap

> Live product: AI-powered 2D/3D architectural blueprint generator with structural engineering and BOQ costing.

## ✅ Completed (Phases 1–10)

| Feature | Status |
|---------|--------|
| Security: bcrypt auth, brute-force lockout, secrets via env | ✅ Done |
| Data layer: SQLAlchemy + Alembic migrations, PostgreSQL | ✅ Done |
| FastAPI backend decoupled from Streamlit frontend | ✅ Done |
| 2D CAD blueprint rendering (6 themes, CAD line weights) | ✅ Done |
| 3D WebGL viewer (Three.js, PBR materials, walkthrough cam) | ✅ Done |
| Code compliance checks (NBC India 2016 / IBC 2021) | ✅ Done |
| Structural engineering: IS 456 column/beam reinforcement | ✅ Done |
| BOQ costing: USD/INR/EUR multi-currency estimates | ✅ Done |
| Agentic AI chat (Gemini 2.5 Flash) with diff view | ✅ Done |
| Export: PNG, SVG, PDF, OBJ, glTF, HTML, ZIP bundle | ✅ Done |
| CI/CD: GitHub Actions + Docker + Sentry + Ruff | ✅ Done |
| Guided wizard UI with metrics strip | ✅ Done |

## 🚧 In Progress (October 2026)

| Feature | Priority | ETA |
|---------|----------|-----|
| Redis-backed model store (persistent across restarts) | P0 | Week 1 |
| Real authentication wiring through DB | P0 | Week 1 |
| Computed Eco & Sustainability metrics | P1 | Week 1 |
| Location-aware weather risk model | P1 | Week 1 |
| NLP BOQ mapped to actual quantities | P1 | Week 1 |
| Pinned dependency lockfile | P1 | Week 1 |
| Rate limiting on API endpoints | P2 | Week 2 |
| Prometheus + Grafana observability stack | P2 | Week 2 |
| Design undo/history (last 5 versions) | P2 | Week 2 |
| Dark/Light theme toggle | P2 | Week 2 |
| Live cloud deployment (Render) | P2 | Week 2 |

## 🔮 Planned (Q4 2026)

| Feature | Description |
|---------|-------------|
| Project sharing links | Signed read-only share URLs for client review |
| BIM/IFC export | Industry-standard BIM format for use in Revit/ArchiCAD |
| Site survey import | Upload a site photo or CAD file to auto-detect constraints |
| Cost benchmarking | Compare BOQ against regional market indices |
| Mobile AR walkthrough | glTF export → WebXR AR session on phone |
| Multi-language support | Hindi, Arabic, Spanish UI localization |
| Consultant marketplace | Connect with licensed architects for sign-off |

## Architecture

```
User Browser
    │
    ▼
[Streamlit Frontend — app.py]
    │  REST API calls
    ▼
[FastAPI Backend — api.py]          [Celery Worker — worker.py]
    │                                       │
    ├── build_matrix/layout_engine    [Redis]
    ├── build_matrix/rendering_3d      │
    ├── build_matrix/drawing_2d     [PostgreSQL]
    └── build_matrix/engineering
```

## Contributing
See [README.md](README.md) for setup instructions. All contributions require:
1. Passing CI (`ruff`, `pytest --cov-fail-under=50`)
2. New tests for any new feature
3. Update to this ROADMAP.md if scope changes
