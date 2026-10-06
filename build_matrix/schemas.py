"""
BuildMetrics AI — Pydantic API Request/Response Schemas.
Extended with validation constraints, examples, and response models.
"""

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = ""
    plot_length: float = Field(default=20.0, gt=0, le=5000, description="Plot length in meters")
    plot_width: float = Field(default=15.0, gt=0, le=5000, description="Plot width in meters")
    max_height: float = Field(default=9.0, gt=0, le=600, description="Maximum building height in meters")
    num_floors: int = Field(default=2, gt=0, le=200, description="Number of floors")
    style: str = Field(default="Modern", description="Architectural style")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "prompt": "Modern 2-story villa with 3 bedrooms, living room, kitchen, 6 pillars",
                "plot_length": 20.0,
                "plot_width": 15.0,
                "max_height": 9.0,
                "num_floors": 2,
                "style": "Modern"
            }]
        }
    }


class Render2DRequest(BaseModel):
    building_id: str = Field(..., description="Building ID returned from /api/v1/generate")
    grid_spacing: float = Field(default=1.0, gt=0, le=10)
    show_grid: bool = True
    show_dimensions: bool = True
    show_pillars: bool = True
    show_beams: bool = True
    show_stairs: bool = True
    show_fixtures: bool = True
    show_axis_grid: bool = True
    show_hatches: bool = True
    show_room_labels: bool = True
    show_title_block: bool = True
    show_compass: bool = True
    show_main_gate: bool = True
    show_garden: bool = True
    show_boundary_wall: bool = True
    show_pathway: bool = True
    dpi: int = Field(default=200, ge=72, le=600)
    theme: str = Field(default="Classic Blueprint", description="Rendering theme")
    floor: int = Field(default=1, ge=1)


class Render3DRequest(BaseModel):
    building_id: str = Field(..., description="Building ID returned from /api/v1/generate")


class ExportRequest(BaseModel):
    building_id: str = Field(..., description="Building ID returned from /api/v1/generate")
    format: str = Field(
        ...,
        description="Export format: 'png', 'svg', 'pdf', 'obj', 'gltf', 'html', 'bundle'"
    )
    floor: int = Field(default=1, ge=1, description="Floor number (for 2D exports)")


class GenerateResponse(BaseModel):
    building_id: str
    model: dict


class HealthResponse(BaseModel):
    status: str
    service: str


class VersionResponse(BaseModel):
    version: str
    git_sha: str
    service: str


class ModelListItem(BaseModel):
    building_id: str
    created_at: str


class ErrorResponse(BaseModel):
    detail: str
