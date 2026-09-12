from pydantic import BaseModel, Field
from typing import Optional

class GenerateRequest(BaseModel):
    prompt: str = ""
    plot_length: float = Field(default=20.0, gt=0)
    plot_width: float = Field(default=15.0, gt=0)
    max_height: float = Field(default=9.0, gt=0)
    num_floors: int = Field(default=2, gt=0, le=100)
    style: str = "Modern"

class Render2DRequest(BaseModel):
    building_id: str
    grid_spacing: float = 1.0
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
    dpi: int = 200
    theme: str = "Classic Blueprint"
    floor: int = 1

class Render3DRequest(BaseModel):
    building_id: str

class ExportRequest(BaseModel):
    building_id: str
    format: str # 'png', 'svg', 'pdf', 'obj', 'bundle', 'html'
    floor: int = 1
