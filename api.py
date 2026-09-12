import os
import uuid
import tempfile
import json
from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from build_matrix.schemas import GenerateRequest, Render2DRequest, Render3DRequest, ExportRequest
from build_matrix.models import PlotDimensions, ArchitecturalStyle, Blueprint2DConfig
from build_matrix.layout_engine import LayoutEngine
from build_matrix.input_handler import InputHandler
from build_matrix.drawing_2d import Blueprint2DRenderer
from build_matrix.exporter import ExporterEngine

app = FastAPI(title="BUILD-MATRIX.ai API", version="1.0.0")
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

import logging
import time
import uuid
from pythonjsonlogger import jsonlogger
from fastapi import Request

logger = logging.getLogger("buildmetrics_api")
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(logHandler)

@app.middleware("http")
async def add_request_id_and_log(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    logger.info("Request started", extra={"request_id": request_id, "path": request.url.path, "method": request.method})
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    logger.info("Request completed", extra={
        "request_id": request_id, 
        "path": request.url.path, 
        "status_code": response.status_code,
        "latency_sec": round(process_time, 4)
    })
    return response


# In-memory store for active building models
# Real-world: Use Redis + proper serialization
from datetime import datetime, timedelta
MODEL_STORE = {}

def _clean_model_store():
    cutoff = datetime.now() - timedelta(minutes=30)
    expired = [uid for uid, data in MODEL_STORE.items() if data['created_at'] < cutoff]
    for uid in expired:
        del MODEL_STORE[uid]

@app.post("/api/v1/generate")
def generate_building(req: GenerateRequest):
    try:
        plot_dims = PlotDimensions(
            length=req.plot_length,
            width=req.plot_width,
            max_height=req.max_height,
            num_floors=req.num_floors
        )
        style_enum = ArchitecturalStyle(req.style)
        
        prompt_parsed = InputHandler.parse_prompt(req.prompt) if req.prompt else {}
        
        layout_engine = LayoutEngine(plot=plot_dims, style=style_enum)
        model = layout_engine.generate_building(prompt_parsed=prompt_parsed)
        
        _clean_model_store()
        building_id = str(uuid.uuid4())
        MODEL_STORE[building_id] = {"model": model, "created_at": datetime.now()}
        
        # We also return the serialized model so the Streamlit UI can render the metrics without querying again
        from pydantic import TypeAdapter
        serialized_model = TypeAdapter(type(model)).dump_python(model, mode='json')
        
        return {
            "building_id": building_id,
            "model": serialized_model
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/render/2d")
def render_2d(req: Render2DRequest):
    if req.building_id not in MODEL_STORE:
        raise HTTPException(status_code=404, detail="Building model not found. Please regenerate.")
    
    model = MODEL_STORE[req.building_id]['model']
    
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
        theme=req.theme
    )
    
    temp_dir = tempfile.mkdtemp()
    png_path = os.path.join(temp_dir, "blueprint.png")
    
    try:
        ExporterEngine.export_2d_png(model, png_path, floor=req.floor, config=config)
        return FileResponse(png_path, media_type="image/png", filename="blueprint.png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/export")
def export_file(req: ExportRequest):
    if req.building_id not in MODEL_STORE:
        raise HTTPException(status_code=404, detail="Building model not found. Please regenerate.")
    
    model = MODEL_STORE[req.building_id]['model']
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
            raise HTTPException(status_code=400, detail="Invalid format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from build_matrix.rendering_3d import Blueprint3DRenderer
from fastapi.responses import HTMLResponse

@app.post("/api/v1/render/3d")
def render_3d(req: Render3DRequest):
    if req.building_id not in MODEL_STORE:
        raise HTTPException(status_code=404, detail="Building model not found. Please regenerate.")
    model = MODEL_STORE[req.building_id]['model']
    renderer_3d = Blueprint3DRenderer(model)
    html_code = renderer_3d.generate_threejs_html()
    return HTMLResponse(content=html_code)
