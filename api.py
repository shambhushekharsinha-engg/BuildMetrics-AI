"""
BuildMetrics AI — FastAPI Backend Service
Exposes REST endpoints for blueprint generation, 2D/3D rendering, and multi-format export.
"""
import json
import logging
import os
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone

import sentry_sdk
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pythonjsonlogger import jsonlogger
from sentry_sdk.integrations.fastapi import FastApiIntegration
from starlette.background import BackgroundTask

from build_matrix.exporter import ExporterEngine
from build_matrix.input_handler import InputHandler
from build_matrix.layout_engine import LayoutEngine
from build_matrix.models import ArchitecturalStyle, Blueprint2DConfig, PlotDimensions
from build_matrix.rendering_3d import Blueprint3DRenderer
from build_matrix.schemas import (
    ExportRequest,
    GenerateRequest,
    Render2DRequest,
    Render3DRequest,
)

# ---------------------------------------------------------------------------
# Optional dependency guards
# ---------------------------------------------------------------------------

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
    _RATE_LIMIT_AVAILABLE = True
except ImportError:
    _RATE_LIMIT_AVAILABLE = False

try:
    import redis as redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Observability: Sentry
# ---------------------------------------------------------------------------

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        integrations=[FastApiIntegration()],
        environment=os.environ.get("ENVIRONMENT", "development")
    )

# ---------------------------------------------------------------------------
# Structured JSON Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger("buildmetrics_api")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
_handler.setFormatter(_formatter)
if not logger.handlers:
    logger.addHandler(_handler)

# ---------------------------------------------------------------------------
# Redis-backed Model Store (falls back to in-memory dict)
# ---------------------------------------------------------------------------

_MODEL_TTL_SECONDS = 30 * 60  # 30 minutes


class ModelStore:
    """
    Persistent model store backed by Redis when available, with automatic
    fallback to an in-process dict.  Models are stored as JSON with a 30-min TTL.
    """

    _KEY_PREFIX = "buildmetrics:model:"
    _META_PREFIX = "buildmetrics:meta:"

    def __init__(self) -> None:
        self._redis = None
        self._memory: dict = {}

        if _REDIS_AVAILABLE:
            try:
                client = redis_lib.Redis.from_url(
                    os.environ.get("REDIS_URL", "redis://localhost:6379"),
                    socket_connect_timeout=2,
                    decode_responses=True,
                )
                client.ping()
                self._redis = client
                logger.info("ModelStore: Redis connection established.")
            except Exception as exc:  # noqa: BLE001
                logger.warning("ModelStore: Redis unavailable, using in-memory store. %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set(self, building_id: str, model) -> None:
        """Persist a building model under *building_id* with 30-min TTL."""
        from pydantic import TypeAdapter

        now_iso = datetime.now(timezone.utc).isoformat()
        serialized = json.dumps(
            {
                "model": TypeAdapter(type(model)).dump_python(model, mode="json"),
                "model_type": f"{type(model).__module__}.{type(model).__qualname__}",
                "created_at": now_iso,
            }
        )

        if self._redis:
            self._redis.setex(self._KEY_PREFIX + building_id, _MODEL_TTL_SECONDS, serialized)
        else:
            self._memory[building_id] = {
                "raw": serialized,
                "created_at": datetime.now(timezone.utc),
            }

    def get(self, building_id: str):
        """Return the deserialized building model or *None* if not found / expired."""
        from build_matrix.models import BuildingModel
        from pydantic import TypeAdapter

        if self._redis:
            raw = self._redis.get(self._KEY_PREFIX + building_id)
            if raw is None:
                return None
            payload = json.loads(raw)
        else:
            entry = self._memory.get(building_id)
            if entry is None:
                return None
            payload = json.loads(entry["raw"])

        return TypeAdapter(BuildingModel).validate_python(payload["model"])

    def list_all(self) -> list[dict]:
        """Return a list of dicts with building_id and created_at for all stored models."""
        results: list[dict] = []

        if self._redis:
            pattern = self._KEY_PREFIX + "*"
            prefix_len = len(self._KEY_PREFIX)
            for key in self._redis.scan_iter(match=pattern):
                building_id = key[prefix_len:]
                ttl = self._redis.ttl(key)
                raw = self._redis.get(key)
                created_at = None
                if raw:
                    try:
                        payload = json.loads(raw)
                        created_at = payload.get("created_at")
                    except Exception:  # noqa: BLE001
                        pass
                results.append(
                    {
                        "building_id": building_id,
                        "created_at": created_at,
                        "ttl_seconds": ttl,
                    }
                )
        else:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=_MODEL_TTL_SECONDS)
            for building_id, entry in list(self._memory.items()):
                if entry["created_at"] < cutoff:
                    continue  # expired — cleanup() will purge these
                payload = json.loads(entry["raw"])
                results.append(
                    {
                        "building_id": building_id,
                        "created_at": payload.get("created_at"),
                        "ttl_seconds": int(
                            (_MODEL_TTL_SECONDS - (datetime.now(timezone.utc) - entry["created_at"]).total_seconds())
                        ),
                    }
                )

        return results

    def cleanup(self) -> None:
        """Evict expired entries from the in-memory fallback store.
        Redis handles TTL natively, so this is a no-op when Redis is active."""
        if self._redis:
            return
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=_MODEL_TTL_SECONDS)
        expired = [uid for uid, data in list(self._memory.items()) if data["created_at"] < cutoff]
        for uid in expired:
            del self._memory[uid]
        if expired:
            logger.info("ModelStore: evicted %d expired in-memory entries.", len(expired))


model_store = ModelStore()

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BuildMetrics AI — API",
    version="1.1.0",
    description="AI-Powered Architectural Blueprint Generator API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Rate Limiting (optional) ---
if _RATE_LIMIT_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Prometheus Metrics (optional) ---
if _PROMETHEUS_AVAILABLE:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["ops"])

# --- CORS — reads from env var for production security ---
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Lifecycle Events
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup_event():
    logger.info("BuildMetrics API starting up", extra={"version": "1.1.0"})


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("BuildMetrics API shutting down")


# ---------------------------------------------------------------------------
# Request ID + Access Log Middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def add_request_id_and_log(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    logger.info(
        "Request started",
        extra={"request_id": request_id, "path": request.url.path, "method": request.method}
    )
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_sec": round(process_time, 4),
        },
    )
    return response


# ---------------------------------------------------------------------------
# Helper: make a temp file that deletes itself after the response is sent
# ---------------------------------------------------------------------------


def _tmp_file(suffix: str) -> str:
    """Create a named temp file, close it, and return its path.

    The caller is responsible for scheduling ``os.unlink(path)`` via
    ``BackgroundTask`` so the file is removed after the HTTP response is sent.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    path = tmp.name
    tmp.close()
    return path


# ---------------------------------------------------------------------------
# Ops Endpoints
# ---------------------------------------------------------------------------


@app.get("/healthz", tags=["ops"])
def health_check():
    """Lightweight liveness probe for Docker/Kubernetes health checks."""
    return {"status": "ok", "service": "buildmetrics-api"}


@app.get("/api/v1/version", tags=["ops"])
def get_version():
    """Return the running API version and git SHA."""
    git_sha = os.environ.get("GIT_SHA", "dev")
    return {"version": "1.1.0", "git_sha": git_sha, "service": "buildmetrics-api"}


# ---------------------------------------------------------------------------
# Model Listing
# ---------------------------------------------------------------------------


@app.get("/api/v1/models", tags=["blueprint"])
def list_models():
    """List all stored building model IDs and their creation times."""
    return model_store.list_all()


# ---------------------------------------------------------------------------
# Blueprint Generation
# ---------------------------------------------------------------------------


if _RATE_LIMIT_AVAILABLE:
    @app.post("/api/v1/generate", tags=["blueprint"])
    @limiter.limit("10/minute")
    def generate_building(request: Request, req: GenerateRequest):
        """Generate a complete building model from a natural-language prompt."""
        return _generate_building_impl(req)
else:
    @app.post("/api/v1/generate", tags=["blueprint"])
    def generate_building(req: GenerateRequest):
        """Generate a complete building model from a natural-language prompt."""
        return _generate_building_impl(req)


def _generate_building_impl(req: GenerateRequest):
    try:
        plot_dims = PlotDimensions(
            length=req.plot_length,
            width=req.plot_width,
            max_height=req.max_height,
            num_floors=req.num_floors,
        )
        style_enum = ArchitecturalStyle(req.style)
        prompt_parsed = InputHandler.parse_prompt(req.prompt) if req.prompt else {}

        layout_engine = LayoutEngine(plot=plot_dims, style=style_enum)
        model = layout_engine.generate_building(prompt_parsed=prompt_parsed)

        model_store.cleanup()
        building_id = str(uuid.uuid4())
        model_store.set(building_id, model)

        from pydantic import TypeAdapter
        serialized_model = TypeAdapter(type(model)).dump_python(model, mode="json")

        return {"building_id": building_id, "model": serialized_model}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Generation error:")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# 2D Rendering
# ---------------------------------------------------------------------------


@app.post("/api/v1/render/2d", tags=["render"])
def render_2d(req: Render2DRequest):
    """Render a 2D CAD blueprint PNG for the specified floor."""
    model = model_store.get(req.building_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Building model not found. Please regenerate.")

    config = Blueprint2DConfig(
        grid_spacing=req.grid_spacing,
        show_grid=req.show_grid,
        show_dimensions=req.show_dimensions,
        show_pillars=req.show_pillars,
        show_beams=req.show_beams,
        show_stairs=req.show_stairs,
        show_fixtures=req.show_fixtures,
        show_axis_grid=req.show_axis_grid,
        show_hatches=req.show_hatches,
        show_room_labels=req.show_room_labels,
        show_title_block=req.show_title_block,
        show_compass=req.show_compass,
        show_main_gate=req.show_main_gate,
        show_garden=req.show_garden,
        show_boundary_wall=req.show_boundary_wall,
        show_pathway=req.show_pathway,
        dpi=req.dpi,
        theme=req.theme,
    )

    png_path = _tmp_file(".png")
    try:
        ExporterEngine.export_2d_png(model, png_path, floor=req.floor, config=config)
        return FileResponse(
            png_path,
            media_type="image/png",
            filename="blueprint.png",
            background=BackgroundTask(os.unlink, png_path),
        )
    except Exception as e:
        os.unlink(png_path)
        logger.exception("2D render error:")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# 3D Rendering
# ---------------------------------------------------------------------------


@app.post("/api/v1/render/3d", tags=["render"])
def render_3d(req: Render3DRequest):
    """Render an interactive Three.js HTML 3D viewer for the building."""
    model = model_store.get(req.building_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Building model not found. Please regenerate.")
    renderer_3d = Blueprint3DRenderer(model)
    html_code = renderer_3d.generate_threejs_html()
    return HTMLResponse(content=html_code)


# ---------------------------------------------------------------------------
# Synchronous Export
# ---------------------------------------------------------------------------


if _RATE_LIMIT_AVAILABLE:
    @app.post("/api/v1/export", tags=["export"])
    @limiter.limit("5/minute")
    def export_file(request: Request, req: ExportRequest):
        """Export the building in the requested format (synchronous)."""
        return _export_file_impl(req)
else:
    @app.post("/api/v1/export", tags=["export"])
    def export_file(req: ExportRequest):
        """Export the building in the requested format (synchronous)."""
        return _export_file_impl(req)


def _export_file_impl(req: ExportRequest):
    model = model_store.get(req.building_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Building model not found. Please regenerate.")

    fmt_map = {
        "png":  (".png",  "image/png",             "BUILD-MATRIX_2D.png",              ExporterEngine.export_2d_png),
        "svg":  (".svg",  "image/svg+xml",          "BUILD-MATRIX_2D.svg",              ExporterEngine.export_2d_svg),
        "pdf":  (".pdf",  "application/pdf",        "BUILD-MATRIX_2D.pdf",              ExporterEngine.export_2d_pdf),
        "obj":  (".obj",  "model/obj",              "BUILD-MATRIX_3D.obj",              ExporterEngine.export_3d_obj),
        "gltf": (".gltf", "model/gltf+json",        "BUILD-MATRIX_3D.gltf",             ExporterEngine.export_3d_gltf),
        "html": (".html", "text/html",              "BUILD-MATRIX_Interactive.html",    ExporterEngine.export_3d_html),
        "bundle": (".zip","application/zip",        "BUILD-MATRIX_Bundle.zip",          ExporterEngine.export_bundle_zip),
    }

    if req.format not in fmt_map:
        raise HTTPException(status_code=400, detail=f"Invalid format: {req.format}")

    suffix, media_type, filename, exporter_fn = fmt_map[req.format]
    path = _tmp_file(suffix)

    try:
        # 2D exporters accept a `floor` kwarg; 3D / bundle ones do not
        if req.format in ("png", "svg", "pdf"):
            exporter_fn(model, path, floor=req.floor)
        else:
            exporter_fn(model, path)
        return FileResponse(
            path,
            media_type=media_type,
            filename=filename,
            background=BackgroundTask(os.unlink, path),
        )
    except HTTPException:
        os.unlink(path)
        raise
    except Exception as e:
        os.unlink(path)
        logger.exception("Export error (sync):")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# Asynchronous Export (Celery)
# ---------------------------------------------------------------------------


@app.post("/api/v1/export/async", tags=["export"])
def export_file_async(req: ExportRequest):
    """Queue an export task via Celery (returns task_id for polling)."""
    model = model_store.get(req.building_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Building model not found. Please regenerate.")

    # Lazy import: prevents crash when Redis/Celery not available in local dev
    try:
        from worker import export_model_task
    except (ImportError, ModuleNotFoundError) as e:
        logger.warning("Celery worker not available, falling back to sync export: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Background worker unavailable. Use /api/v1/export for synchronous export."
        ) from e

    from pydantic import TypeAdapter

    from build_matrix.models import BuildingModel
    model_dict = TypeAdapter(BuildingModel).dump_python(model, mode="json")
    task = export_model_task.delay(model_dict, req.format, req.floor)
    return {"task_id": task.id}


@app.get("/api/v1/export/status/{task_id}", tags=["export"])
def get_export_status(task_id: str):
    """Poll the status of an async export task."""
    try:
        from celery.result import AsyncResult

        from worker import celery_app
    except (ImportError, ModuleNotFoundError) as e:
        raise HTTPException(status_code=503, detail="Background worker unavailable.") from e

    res = AsyncResult(task_id, app=celery_app)
    if res.state == "SUCCESS":
        return {"status": "SUCCESS", "result": res.result}
    elif res.state == "FAILURE":
        return {"status": "FAILURE", "error": str(res.info)}
    else:
        return {"status": res.state}


@app.get("/api/v1/download", tags=["export"])
def download_file(path: str, filename: str, media_type: str):
    """Serve a previously-generated export file by path."""
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found or expired.")
    return FileResponse(path, media_type=media_type, filename=filename)


# ---------------------------------------------------------------------------
# Sentry Debug (intentional error for integration test)
# ---------------------------------------------------------------------------


@app.get("/sentry-debug", include_in_schema=False)
async def trigger_error():
    """Intentional error for Sentry integration smoke test."""
    division_by_zero = 1 / 0  # noqa: F841
