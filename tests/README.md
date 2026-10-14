# 🧪 BuildMetrics AI — Quality Assurance & Test Suite Manual

The `tests/` directory provides comprehensive coverage across the FastAPI REST endpoints, Streamlit frontend controller, database ORM repository, core computational civil engines, OpenBIM generator, AutoCAD vector CAD exporter, and ML cost models.

---

## 📊 Test Suite Overview

| Test Module | Test Count | Scope & Coverage |
| :--- | :---: | :--- |
| `test_api.py` | 11 tests | FastAPI endpoints (`/healthz`, `/api/v1/version`, `/api/v1/models`, `/api/v1/generate`, `/api/v1/render/2d`, `/api/v1/render/3d`, `/api/v1/export`, synchronous & async Celery tasks, rate limits). |
| `test_app.py` | 11 tests | Streamlit smoke tests, python compile check, module imports, UI initialization, session state initialization, and component rendering without exceptions. |
| `test_civil_math.py` | 3 tests | Foundation volumetric formulas, structural rebar sizing, and material takeoff math. |
| `test_cost_engine.py` | 17 tests | Scikit-learn Random Forest regression model loading, cost prediction positive boundary checks, area scaling, and floor multipliers. |
| `test_db.py` | 6 tests | SQLAlchemy ORM, user registration, bcrypt password hashing verification, 5-strike brute-force lockout, and project save/load. |
| `test_dxf_geotech_vastu.py` | 9 tests | Layered AutoCAD DXF vector structure (`AC1009`), Geotechnical SBC and soil profiles, seismic detailing, Vastu Shastra 9-zone mandala audit, and structural load distribution ($FS$, $M_u$). |
| `test_engineering.py` | 1 test | NBC India 2016 vs IBC 2021 compliance rules, minimum room area, egress door widths, and stair geometry limits. |
| `test_ifc.py` | 4 tests | OpenBIM IFC4 ISO-10303-21 STEP physical format, `IfcProject` hierarchy, semantic building elements (`IfcWallStandardCase`, `IfcColumn`, `IfcBeam`, `IfcSlab`, `IfcSpace`), and file export. |
| `test_layout.py` | 1 test | Recursive Binary Space Partitioning (BSP) floor plan generation, room adjacency, and non-overlapping boundary geometry. |
| **Total** | **63 tests** | **100% Passing Suite** |

---

## 🛠️ Test Environment Fixtures (`conftest.py`)

All tests share environment fixtures defined in [`tests/conftest.py`](conftest.py):
- `set_test_env`: Automatically sets test environment variables:
  - `DATABASE_URL = sqlite:///test_buildmetrics.db`
  - `GEMINI_API_KEY = dummy_test_key`
  - `ENVIRONMENT = test`
  - `REDIS_URL = redis://localhost:6379`
- `api_client`: Provides a shared FastAPI `TestClient(app)` session.
- `sample_building_id`: Fixture that generates a sample building and caches its UUID for multi-format export tests.

---

## 🚀 Running the Tests

### 1. Run Complete Test Suite
```bash
pytest tests/ -v
```

### 2. Run with Coverage Report
The CI pipeline enforces a minimum 50% coverage floor across core modules:
```bash
pytest --cov=build_matrix --cov=api --cov=cost_engine --cov=db --cov-report=term-missing
```

### 3. Run Specific Subsystems
```bash
# CAD & BIM tests
pytest tests/test_dxf_geotech_vastu.py tests/test_ifc.py -v

# FastAPI REST integration tests
pytest tests/test_api.py -v

# Database and security lockout tests
pytest tests/test_db.py -v
```

---

## 🛡️ CI/CD Quality Gates

Every pull request and commit to `main` must pass the GitHub Actions CI pipeline:
1. **Ruff Strict Linter:** `ruff check .` (zero warnings or errors allowed).
2. **Syntax Compilation:** `python -m py_compile app.py` and `compileall`.
3. **Pytest Coverage:** All 63 tests must pass with coverage above 50%.
4. **Security Scan:** `pip-audit` scanning for known CVE vulnerabilities.
5. **Docker Container Build:** Containerization smoke test hitting `/healthz`.
