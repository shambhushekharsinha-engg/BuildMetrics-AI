# BuildMetrics-AI: Journey to Production

This walkthrough documents the full transformation of BuildMetrics-AI from a raw working prototype into an industrial-grade, deployable product, culminating in the execution of the Phase 5-10 roadmap. 

## 1. Security & Data Integrity (Phases 1, 2 & 4)
- **Hardened Authentication**: Replaced unsalted hashes with industry-standard `bcrypt`.
- **Database Migration**: Fully migrated away from raw SQLite concurrency bottlenecks into `SQLAlchemy` ORM, enabling connection pooling and robust Postgres deployments.
- **Alembic Migrations**: The database is now strictly version-controlled, fixing day-1 fresh-deploy bugs.
- **Engineering Liability**: Added persistent legal disclaimers and verified implicit load parameters in `ASSUMPTIONS.md`.

## 2. Decoupled Compute via FastAPI (Phase 3)
The monolithic Streamlit app was successfully split, paving the way for scale.
- **`api.py`**: A dedicated FastAPI service now owns the heavy mathematical extrusion and generation load.
- **Server-side Caching**: Implemented a `MODEL_STORE` with UUID tracking and TTL eviction to prevent OOM memory leaks and unbounded network serialization. 
- **Pydantic Validation**: All schemas strictly validated, preserving Enums across the JSON serialization boundary.

## 3. DevOps, CI/CD & Testing (Phases 5 & 6)
We made the codebase robustly testable and containerized.
- **Dependency Pinning**: Swapped GUI-heavy `opencv-python` for `opencv-python-headless` to prevent headless Docker failures. Used `pip-tools` to compile a strictly version-locked, hash-locked `requirements.txt`.
- **Multi-Stage Dockerfile**: Engineered a builder-runner pattern to keep the final `python:3.12-slim` image lightweight without retaining build toolchains.
- **Docker Compose Orchestration**: Bound `Streamlit`, `FastAPI`, and `Postgres` together, resolving Docker networking gaps (`API_BASE_URL=http://api:8000`) and ensuring proper startup order via health checks.
- **Automated CI/CD**: Established `.github/workflows/ci.yml` triggering on PRs to run:
  - `ruff` (linting)
  - `mypy` (advisory type checking for Pydantic integration)
  - `pytest` (Test suite executing structural layout invariants and multi-currency BOQ calculations)
  - Docker smoke-build.

## 4. Observability & 2D Blueprint Code Compliance (Phases 7 & 8)
- **JSON Logging**: Upgraded the FastAPI backend with `python-json-logger` for structured telemetry. Injected `X-Request-ID` headers to trace latency down to the millisecond across generation routes.
- **Code Compliance Overlays**: Enforced line-weight hierarchy (3.0 for exterior, 2.0 for interior) and integrated automated layout compliance checks (e.g., Egress paths, Plot Area Constraints) directly onto the exported `Blueprint2DRenderer` Title Block.

## Next Steps (Phases 9 & 10 UX Restructuring)
The foundations are rock solid. Future iterations will focus purely on the presentation layer:
- Upgrading Three.js to physically-based materials (PBR) and adding interactive Sun-path simulators.
- Restructuring the monolithic Streamlit sidebar into a guided, sequential wizard (`Plot -> Prompt -> Style`).
- Integrating Celery/Redis for asynchronous export processing when the scale justifies it.
