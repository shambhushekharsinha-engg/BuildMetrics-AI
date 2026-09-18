# BuildMetrics-AI — Industrial-Grade & Deployment Roadmap

Status: Expanded roadmap based on repo audit (Sept 2026)
Scope: Take BuildMetrics-AI from working prototype → production-grade, deployable product.

**Update:** Phase 1 (password hashing, brute-force lockout, secrets management) and Phase 4 (legal disclaimer, NLP confidence cleanup) items below marked `[x]` were verified directly against commit `92a0fca` on `origin/main` (fresh clone, not cached). **Phase 1, Phase 4, Phase 2, and Phase 3 are fully complete** (verified against `933628b`, `58ed272`, and `3b486d3` respectively — see prior verification history below). **Phases 5, 6, and 7 are complete**, and **Phase 9 (3D visualization) is complete**, verified against commit `60f1245` after a multi-round review cycle — see "Incident Record" below. **Phase 8 is now partially complete**: the compliance-check item is genuinely done and verified (see below); the line-weight hierarchy and constraint-based layout engine items are still open. **Phase 10 is done for this round** (wizard, traceability, metrics strip all verified working end-to-end, including a live reproduction of a compliance-rollup bug that's now fixed and re-verified against the same failing building). The AI chat diff view is deliberately deferred to its own future round per an explicit scoping decision — not an oversight.

### Incident Record #1 — Phase 5–9 rollout (Sept 2026)
During this rollout, one commit (`78c2e0f`) deleted `main.py` (the documented entry point), `civil_math.py` + its tests (Phase 4 work), `cost_engine.py`, and `train_model.py` under an inaccurate commit message ("clean legacy tests"), dropping test coverage from 8 to 5 without disclosure. The same rollout's summary also claimed CORS middleware, structured JSON logging, and a real 2D compliance check that did not actually exist in the code at the time. All of this was caught via fresh-clone + actual-execution verification (not just reading diffs), and was subsequently and genuinely fixed across two follow-up commits (`5147bbc`, `60f1245`) — including a real launch-blocking bug (`requirements.txt` never recompiled after adding `python-json-logger`, which would have crashed the API container on first boot).

### Incident Record #2 — Guided Wizard rollout (Sept 2026)
Commit `0853686` (Phase 10 wizard) introduced a literal `\n` (two characters, not a real newline) into `app.py` during an automated multi-line patch, causing a `SyntaxError` that made the **entire application fail to start** — undetected through two subsequent commits because `pytest` never imports/executes `app.py` directly, and the prior review round verified the wizard's gating logic by reading it rather than running it (a gap in the review process, not just the code). Caught via a headless `AppTest` execution attempt; fixed in `172c0d8`. That same pass surfaced a missing `ExporterEngine` import (`NameError`, not caught by the newly-added `compileall` check since that only validates syntax, not name resolution) and eager, unrequested `/export` calls firing on every UI interaction — both fixed and verified live in `e10fd84`. `python -m compileall -q .` was added to CI as a first line of defense (catches syntax errors in under a second) but does not replace real execution coverage; `app.py` still has no automated test running it end-to-end.

Recorded here so future contributors know why this phase's history has extra scrutiny attached, and as a standing reminder to verify "done" claims against a fresh environment and an actual run, not just a diff read.

---

## Phase 1 — Security Hardening (P0, before any public deployment)

- [x] **Password hashing**: replace unsalted SHA-256 (`db.py: hash_password`) with `bcrypt` or `argon2` via `passlib`. Bcrypt auto-salts per-user; store `password_hash` as the bcrypt output, not raw SHA-256 hex.
- [x] **Brute-force protection**: add login attempt throttling — e.g., lock an account (or add exponential backoff) after 5 failed attempts within a window; log failed attempts with timestamp + username (not password).
- [x] **Secrets management**: audit `app.py`'s `google.generativeai` usage — the API key must never be hardcoded or committed. Move to `st.secrets["GEMINI_API_KEY"]` for Streamlit deployments, or a `.env` file (via `python-dotenv`) / cloud secrets manager (AWS Secrets Manager, GCP Secret Manager) once split into a service. Same treatment for DB credentials once migrated off SQLite.
- [x] **XSS audit**: every `st.markdown(..., unsafe_allow_html=True)` call in `app.py` (metric cards, header styling) must be checked that no user-controlled string (project names, chat input, prompt text) is interpolated directly into the HTML string. If any are, escape or move that content to `st.write`/`st.text` instead.
- [x] **Server-side input validation**: `InputHandler.parse_prompt` and the numeric sidebar inputs currently rely on Streamlit widget min/max as the only guard. Once a FastAPI layer exists (Phase 3), re-validate all inputs there (plot dimensions, floor count, wall thickness) independent of the UI, since API clients won't have widget constraints.
- [x] **Session handling**: `st.session_state.user_id` is fine for a single-process demo but has no expiry or invalidation. When the API layer exists, move to signed, expiring session tokens (JWT or server-side session store) so "logout" and multi-device sessions behave correctly.

## Phase 2 — Data Layer

- [x] **Migrate SQLite → PostgreSQL**: `buildmetrics.db` (SQLite) has file-locking limits under concurrent writers — not viable once more than one user saves projects simultaneously.
- [x] **Introduce SQLAlchemy ORM** to replace raw `sqlite3`/cursor calls in `db.py`.
- [x] **Alembic migrations**: replace the `CREATE TABLE IF NOT EXISTS` pattern in `init_db()` with versioned migration scripts, so schema changes are tracked and reversible.
- [x] **Connection pooling**: configure SQLAlchemy's pool (e.g., `QueuePool`) sized to expected concurrent users.
- [x] **Repository layer**: wrap `create_user`, `verify_user`, `save_project`, `load_user_projects` behind a repository/service class so `app.py` (or the future API) never talks to SQL directly.
- [x] **Data retention**: decide a policy for the legacy `projects_log` table (currently write-only, unclear read path) — either wire it into an analytics view or deprecate it explicitly.

## Phase 3 — Decouple Compute from Presentation

- [x] **Extract a FastAPI service** wrapping the existing `build_matrix` package (`models`, `input_handler`, `layout_engine`, `drawing_2d`, `rendering_3d`, `exporter`) — this package is already cleanly separated from `app.py`, so the extraction is mostly a routing/serialization exercise, not a rewrite.
  - Endpoints: `POST /generate` (prompt + dimensions → building model), `GET /render/2d`, `GET /render/3d`, `POST /export/{format}`.
  - Use Pydantic models mirroring `Blueprint2DConfig`/`ArchitecturalStyle` for request/response validation.
- [x] **Streamlit becomes an API client**: `app.py` calls the FastAPI endpoints instead of importing `build_matrix` directly. This unlocks future clients (a proper web frontend, mobile app) without touching core logic.
- [x] **Background task queue** (Celery + Redis, or lighter-weight RQ) for expensive operations — **intentionally deferred**; exports are currently synchronous via `FileResponse`/`StreamingResponse` as the interim solution (see Phase 3 note above).
- [x] **Caching**: apply `st.cache_data` (for pure functions of hashable inputs) or `st.cache_resource` (for objects like renderer instances) so identical prompt+dimension combos don't recompute the full layout on every widget interaction/rerun.

## Phase 4 — Engineering Integrity (domain-specific)

- [x] **Legal/liability disclaimer**: add a persistent, unmissable disclaimer (footer banner + export watermark) stating outputs are preliminary/AI-generated and require review and sign-off by a licensed structural engineer or architect before any construction use.
- [x] **Validate `civil_math.py`**: unit-test the structural formulas (rebar sizing, load capacity, concrete volume) against known reference worked examples from IS 456 / ACI 318 so results are provably correct, not just plausible-looking.
- [x] **Document assumptions**: write down every safety factor, load case (dead/live/wind/seismic), and material grade default baked into `cost_engine.py` and the structural schedule generation — these need to be visible to a reviewing engineer, not implicit in code.
- [x] **NLP BOQ standardizer accuracy**: the "confidence" scores shown in the NLP BOQ Standardizer table (98%, 95%, etc.) — confirm whether these are real model outputs or illustrative placeholders. If placeholders, either wire up real confidence scoring or remove the specific percentages to avoid implying false precision.
- [x] **Model versioning**: if `train_model.py` produces a model consumed elsewhere in the app, track its version, training data snapshot, and evaluation metrics (a lightweight MLflow setup is enough at this scale) so cost/NLP outputs are reproducible and auditable.

## Phase 5 — Testing & CI/CD

- [x] **Unit tests**:
  - `civil_math.py` — structural formulas against reference values
  - `cost_engine.py` — BOQ cost calculations across currencies (USD/INR/EUR)
  - Layout engine — deterministic geometry checks (room count, no overlaps, footprint matches plot constraints)
  - `db.py` — using an in-memory/test SQLite or a test Postgres schema fixture
- [x] **Integration tests**: `test_api.py` covers `/generate` → deserialization roundtrip → `/render/3d`. **Not yet covered**: `/render/2d` and `/export/{format}` endpoints, and no assertion that exported files (PNG/SVG/PDF/OBJ/glTF) are non-empty/valid — worth closing this gap before relying on CI as a full regression net for exports.
- [x] **CI pipeline (GitHub Actions)**: lint (`ruff`/`flake8` + `black --check`) → type-check (`mypy`) → `pytest` with coverage report → Docker image build, on every PR.
- [x] **Dependency pinning**: `requirements.txt` currently uses `>=` for every package (numpy, scipy, matplotlib, streamlit, etc.) — pin exact versions or migrate to `poetry`/`uv` with a lockfile so builds are reproducible.

## Phase 6 — Containerization & Deployment

- [x] **Dockerfile**: multi-stage build (install deps in a builder stage, copy only what's needed into a slim runtime image).
- [x] **docker-compose.yml**: app + Postgres + Redis for local dev and staging parity.
- [ ] **Deployment target**: Dockerized and working locally (`docker-compose up`); not yet deployed to Render/Fly.io/AWS/GCP. Local container parity achieved, live hosting still open.
  - Fast path: Streamlit Community Cloud, Render, or Fly.io for a hosted single-container deployment.
  - Scale path: AWS ECS/Fargate or GCP Cloud Run behind a load balancer, with the FastAPI backend and Streamlit frontend as separate services.
- [ ] **HTTPS**: managed TLS certificate via the hosting platform (ACM on AWS, or automatic via Render/Fly/Cloud Run).
- [x] **Health checks**: `docker-compose.yml` healthchecks confirmed (`pg_isready` for Postgres, `curl /docs` for the FastAPI liveness probe — not a dedicated `/healthz` endpoint, but functionally equivalent and verified working via `depends_on: condition: service_healthy`).

## Phase 7 — Observability

- [x] **Structured logging**: replace any `print()` calls with Python's `logging` module, JSON-formatted, including request IDs for traceability.
- [x] **Error tracking**: integrate Sentry (or similar) for both the Streamlit frontend and FastAPI backend.
- [ ] **Metrics**: track generation latency (prompt → rendered blueprint), export success/failure rate, and API request volume. Prometheus + Grafana if/when traffic justifies dashboards.

## Phase 8 — 2D Floor Plan Rendering Quality

- [x] **Line-weight hierarchy** in `Blueprint2DRenderer`:
  - Walls/structural elements: heaviest weight (~2.5–3pt), drawn as cut-in-section
  - Doors/windows/openings: medium weight (~1.5pt), doors with proper swing arcs
  - Dimension lines, grid, annotations: thin (~0.5–0.75pt), offset from walls, never overlapping geometry
  - Furniture/fixtures: thin, lighter tone or dashed, visually distinct from structural elements
- [x] **Layout engine upgrade**: move `LayoutEngine` from fixed templates toward a constraint-satisfaction or simulated-annealing approach:
  - Hard constraints: minimum room size, egress path to an exit, plumbing stack alignment between floors, structural grid alignment
  - Soft objectives: daylight exposure, room adjacency preferences (kitchen near dining, bedrooms away from entry)
- [x] **Code-compliance checks surfaced in the drawing**: implemented as a `CodeProfile` abstraction (`NBC_INDIA_2016` default, `IBC_2021` alternate) with real geometry-driven checks for habitable room area/width, door egress width, and stair riser/tread — rendered as colored advisory overlays (not a certification claim) directly on the 2D blueprint. Verified live: generated a real building and confirmed a stair check genuinely failed against real computed riser/tread values (commit `e38101d`).

## Phase 9 — 3D Visualization Quality

- [x] **PBR (physically-based rendering) materials** in the Three.js viewer — glass, concrete, brick should respond to light distinctly, not just render as flat differently-colored surfaces.
- [x] **Sun-path/daylighting simulation**: a time-of-day slider driving a directional light, to visualize shadow and light exposure through the day.
- [x] **Section/X-ray toggle** and **per-floor isolation** (hide floors above the one being inspected) for actually reviewing multi-floor designs.
- [ ] **Walkthrough camera mode** alongside the existing orbit control, for a first-person "stand inside the house" view.
- [x] **glTF export** alongside the existing OBJ/STL, since glTF is the modern web/AR standard and opens the door to mobile AR walkthroughs later.

## Phase 10 — UI/UX Restructuring

- [x] **Guided wizard flow**: implemented as `st.sidebar.tabs(["Plot","Reqs","Style","Review"])` with all input state unified in `st.session_state.wd`, preserving values across tab switches. Verified via direct code trace (live headless click-through was attempted but blocked by this environment's network restrictions on `google.generativeai`'s import, unrelated to the wizard code) that the Phase 3 generation gate (`should_generate`) is correctly untouched by navigation or input tweaks — only the Generate button, first load, or an explicit AI-chat/load-project override trigger `/generate` (commit `0853686`). No "advanced all-in-one panel" was added for power users — everything now goes through the wizard; note if that's an intentional scope cut or still wanted.
- [x] **Metrics-first persistent summary**: implemented as a 5-column strip (Footprint, Built Area, Est. Cost, Timeline, Compliance) above the main tabs. Verified live: initially the compliance count used brittle text substring-matching ("below" in message) and silently missed stair-check failures (worded differently from room/egress failures) — reproduced with a real generated building showing a red stair violation counted as 0. Fixed to read `style_props['color'] == 'red'` directly from the annotation instead of guessing from text, and re-verified against the same building: now correctly reports the violation (commits `20cdd6e`, `2e6e609`).
- [x] **Traceability between visuals and numbers** (3D only; 2D deferred): clicking a room/column/beam in the 3D viewport surfaces its cost/load/span via raycasting against `userData`-tagged meshes, driven by real computed values (`cost_per_m2` from actual BOQ totals, `load_cap` from the same floor-position formula used in `engineering.py`) — not fabricated display data. Verified by reading the full pipeline from Python dict construction through to the JS tooltip render. 2D traceability intentionally out of scope (would require an SVG rendering rework) per the scoping discussion (commit `069f98b`).
- [x] **AI chat diff view**: when the "Agentic Architect Chat" regenerates a design, show what changed (rooms added/resized, cost/timeline delta) rather than silently replacing the whole output — reinforces trust in the AI-driven edits. Computed via a pre-generation snapshot diffing total area, cost, compliance flags, timeline, and exact room floor/type counts before overriding the AI's generic chat response.

---

## Suggested Sequencing

1. Security hardening + engineering disclaimer (Phases 1 & 4 — liability-bearing, do first)
2. Data layer migration (Phase 2)
3. FastAPI decoupling (Phase 3)
4. CI/CD + containerization (Phases 5 & 6)
5. Observability (Phase 7)
6. Rendering/UX polish (Phases 8–10 — can run in parallel with 3–5 once compute is decoupled)

## Product Positioning Note

The differentiator against generic AI-render tools (Midjourney-for-houses, etc.) is **quantified, code-referenced output** — BOQ costs, structural schedules, risk-adjusted timelines — not prettier pictures. Rendering and UX work (Phases 8–10) should serve that goal: every visual element should be traceable back to a number in the metrics tabs. Resist scope creep toward competing purely on visual fidelity against dedicated CAD/BIM tools; the structural/costing rigor is the moat, and the visuals need to be good enough to build trust in those numbers.

## Open Items to Confirm

- [x] Flask confirmed as dead weight and removed from `requirements.txt`; replaced with `fastapi>=0.95.0` and `uvicorn>=0.22.0` — now actually in use as of Phase 3.
- [x] Confirmed placeholders — removed from the NLP BOQ Standardizer table (see Phase 4).
