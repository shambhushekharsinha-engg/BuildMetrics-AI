import os
import tempfile

from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "buildmetrics_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        integrations=[CeleryIntegration()],
        environment=os.environ.get("ENVIRONMENT", "development")
    )

@celery_app.task(name="tasks.export_model")
def export_model_task(model_dict: dict, format: str, floor: int = 1) -> dict:
    from pydantic import TypeAdapter

    from build_matrix.exporter import ExporterEngine
    from build_matrix.models import BuildingModel
    model = TypeAdapter(BuildingModel).validate_python(model_dict)
    
    shared_dir = os.environ.get("SHARED_EXPORT_DIR", tempfile.gettempdir())
    os.makedirs(shared_dir, exist_ok=True)
    temp_dir = tempfile.mkdtemp(dir=shared_dir)
    
    path = ""
    filename = ""
    media_type = ""
    
    if format == "png":
        path = os.path.join(temp_dir, "blueprint.png")
        ExporterEngine.export_2d_png(model, path, floor=floor)
        filename = "BUILD-MATRIX_2D.png"
        media_type = "image/png"
    elif format == "svg":
        path = os.path.join(temp_dir, "blueprint.svg")
        ExporterEngine.export_2d_svg(model, path, floor=floor)
        filename = "BUILD-MATRIX_2D.svg"
        media_type = "image/svg+xml"
    elif format == "pdf":
        path = os.path.join(temp_dir, "blueprint.pdf")
        ExporterEngine.export_2d_pdf(model, path, floor=floor)
        filename = "BUILD-MATRIX_2D.pdf"
        media_type = "application/pdf"
    elif format == "obj":
        path = os.path.join(temp_dir, "model.obj")
        ExporterEngine.export_3d_obj(model, path)
        filename = "BUILD-MATRIX_3D.obj"
        media_type = "model/obj"
    elif format == "gltf":
        path = os.path.join(temp_dir, "model.gltf")
        ExporterEngine.export_3d_gltf(model, path)
        filename = "BUILD-MATRIX_3D.gltf"
        media_type = "model/gltf+json"
    elif format == "html":
        path = os.path.join(temp_dir, "viewer.html")
        ExporterEngine.export_3d_html(model, path)
        filename = "BUILD-MATRIX_Interactive.html"
        media_type = "text/html"
    elif format == "bundle":
        path = os.path.join(temp_dir, "bundle.zip")
        ExporterEngine.export_bundle_zip(model, path)
        filename = "BUILD-MATRIX_Bundle.zip"
        media_type = "application/zip"
    else:
        raise ValueError(f"Invalid format {format}")

    return {
        "status": "success",
        "path": path,
        "filename": filename,
        "media_type": media_type
    }
