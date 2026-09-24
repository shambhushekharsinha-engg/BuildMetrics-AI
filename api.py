"""
BuildMetrics AI — FastAPI Backend Service
Exposes REST endpoints for blueprint generation, 2D/3D rendering, and multi-format export.
"""
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

# --- Observability: Sentry ---
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        integrations=[FastApiIntegration()],
        environment=os.environ.get("ENVIRONMENT", "development")
    )

# --- Application ---
app = FastAPI(
    title="BuildMetrics AI — API",
    version="1.0.0",
    description="AI-Powered Architectural Blueprint Generator API",
    docs_url="/docs",
    redoc_url="/redoc",
)

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

# --- Structured JSON Logging ---
logger = logging.getLogger("buildmetrics_api")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
_handler.setFormatter(_formatter)
if not logger.handlers:
    logger.addHandler(_handler)


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


# --- In-memory Model Store (TTL-evicted) ---
# Real-world: Use Redis + proper serialization
MODEL_STORE: dict = {}


def _clean_model_store():
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    expired = [uid for uid, data in MODEL_STORE.items() if data["created_at"] < cutoff]
    for uid in expired:
        del MODEL_STORE[uid]


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/healthz", tags=["ops"])
def health_check():
    """Lightweight liveness probe for Docker/Kubernetes health checks."""
    return {"status": "ok", "service": "buildmetrics-api"}


# ---------------------------------------------------------------------------
# Blueprint Generation
# ---------------------------------------------------------------------------

@app.post("/api/v1/generate", tags=["blueprint"])
def generate_building(req: GenerateRequest):
    """Generate a complete building model from a natural-language prompt."""
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

        _clean_model_store()
        building_id = str(uuid.uuid4())
        MODEL_STORE[building_id] = {"model": model, "created_at": datetime.now(timezone.utc)}

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
    if req.building_id not in MODEL_STORE:
        raise HTTPException(status_code=404, detail="Building model not found. Please regenerate.")

    model = MODEL_STORE[req.building_id]["model"]

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

    temp_dir = tempfile.mkdtemp()
    png_path = os.path.join(temp_dir, "blueprint.png")

    try:
        ExporterEngine.export_2d_png(model, png_path, floor=req.floor, config=config)
        return FileResponse(png_path, media_type="image/png", filename="blueprint.png")
    except Exception as e:
        logger.exception("2D render error:")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# 3D Rendering
# ---------------------------------------------------------------------------

@app.post("/api/v1/render/3d", tags=["render"])
def render_3d(req: Render3DRequest):
    """Render an interactive Three.js HTML 3D viewer for the building."""
    if req.building_id not in MODEL_STORE:
        raise HTTPException(status_code=404, detail="Building model not found. Please regenerate.")
    model = MODEL_STORE[req.building_id]["model"]
    renderer_3d = Blueprint3DRenderer(model)
    html_code = renderer_3d.generate_threejs_html()
    return HTMLResponse(content=html_code)


# ---------------------------------------------------------------------------
# Synchronous Export
# ---------------------------------------------------------------------------

@app.post("/api/v1/export", tags=["export"])
def export_file(req: ExportRequest):
    """Export the building in the requested format (synchronous)."""
    if req.building_id not in MODEL_STORE:
        raise HTTPException(status_code=404, detail="Building model not found. Please regenerate.")

    model = MODEL_STORE[req.building_id]["model"]
    temp_dir = tempfile.mkdtemp()

    try:
        if req.format == "png":
            path = os.path.join(temp_dir, "blueprint.png")
            ExporterEngine.export_2d_png(model, path, floor=req.floor)
            return FileResponse(path, media_type="image/png", filename="BUILD-MATRIX_2D.png")
        elif req.format == "svg":
            path = os.path.join(temp_dir, "blueprint.svg")
            ExporterEngine.export_2d_svg(model, path, floor=req.floor)
            return FileResponse(path, media_type="image/svg+xml", filename="BUILD-MATRIX_2D.svg")
        elif req.format == "pdf":
            path = os.path.join(temp_dir, "blueprint.pdf")
            ExporterEngine.export_2d_pdf(model, path, floor=req.floor)
            return FileResponse(path, media_type="application/pdf", filename="BUILD-MATRIX_2D.pdf")
        elif req.format == "obj":
            path = os.path.join(temp_dir, "model.obj")
            ExporterEngine.export_3d_obj(model, path)
            return FileResponse(path, media_type="model/obj", filename="BUILD-MATRIX_3D.obj")
        elif req.format == "gltf":
            path = os.path.join(temp_dir, "model.gltf")
            ExporterEngine.export_3d_gltf(model, path)
            return FileResponse(path, media_type="model/gltf+json", filename="BUILD-MATRIX_3D.gltf")
        elif req.format == "html":
            path = os.path.join(temp_dir, "viewer.html")
            ExporterEngine.export_3d_html(model, path)
            return FileResponse(path, media_type="text/html", filename="BUILD-MATRIX_Interactive.html")
        elif req.format == "bundle":
            path = os.path.join(temp_dir, "bundle.zip")
            ExporterEngine.export_bundle_zip(model, path)
            return FileResponse(path, media_type="application/zip", filename="BUILD-MATRIX_Bundle.zip")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid format: {req.format}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Export error (sync):")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# Asynchronous Export (Celery)
# ---------------------------------------------------------------------------

@app.post("/api/v1/export/async", tags=["export"])
def export_file_async(req: ExportRequest):
    """Queue an export task via Celery (returns task_id for polling)."""
    if req.building_id not in MODEL_STORE:
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

    model = MODEL_STORE[req.building_id]["model"]
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
