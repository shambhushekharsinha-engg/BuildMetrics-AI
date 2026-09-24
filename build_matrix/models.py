"""
BUILD-MATRIX.ai Data Models
Defines structural, parametric, and visualization data representations for 2D and 3D architectural blueprints.
"""

from dataclasses import dataclass, field
from enum import Enum


@dataclass
class CodeProfile:
    name: str
    min_habitable_room_area_m2: float
    min_room_width_m: float
    min_egress_width_m: float
    max_riser_mm: float
    min_tread_mm: float

NBC_INDIA_2016 = CodeProfile(
    name="NBC India (2016)",
    min_habitable_room_area_m2=9.5,
    min_room_width_m=2.4,
    min_egress_width_m=0.9,
    max_riser_mm=190.0,
    min_tread_mm=250.0
)

IBC_2021 = CodeProfile(
    name="IBC (2021)",
    min_habitable_room_area_m2=6.5,
    min_room_width_m=2.13,
    min_egress_width_m=0.81,
    max_riser_mm=196.0,
    min_tread_mm=254.0
)


class ArchitecturalStyle(Enum):
    MODERN = "Modern"
    MINIMALIST = "Minimalist"
    CLASSIC = "Classic / Traditional"
    INDUSTRIAL = "Industrial"
    BRUTALIST = "Brutalist"
    LUXURY_VILLA = "Luxury Villa"
    CONTEMPORARY = "Contemporary"
    CRAFTSMAN = "Craftsman"
    JAPANDI = "Japandi (Zen Fusion)"
    SCANDINAVIAN = "Scandinavian (Nordic Light)"
    TROPICAL = "Tropical Eco-Villa"
    MEDITERRANEAN = "Mediterranean Coastal"



@dataclass
class PlotDimensions:
    length: float = 20.0  # meters (X dimension) - supports up to 1000m+
    width: float = 15.0   # meters (Y dimension) - supports up to 1000m+
    max_height: float = 9.0  # meters (Z dimension max limit)
    num_floors: int = 2   # supports up to 100+ floors
    floor_height: float = 3.2  # meters per floor
    wall_thickness: float = 0.25  # meters (25cm)
    margin: float = 1.0  # setback margin from plot edge (meters)


@dataclass
class StructuralColumnSpec:
    id: str
    column_code: str  # e.g., 'C1', 'C2'
    x: float
    y: float
    width: float = 0.45
    depth: float = 0.45
    concrete_grade: str = "M30"  # 'M25', 'M30', 'M40', 'M50'
    main_bars: str = "4x16mm + 4x12mm Fe500 TMT"
    tie_spacing: str = "8mm @ 150mm c/c"
    load_capacity_kn: float = 1200.0
    floor: int = 1


@dataclass
class StructuralBeamSpec:
    id: str
    beam_code: str  # e.g., 'B1', 'B2'
    x1: float
    y1: float
    x2: float
    y2: float
    width: float = 0.3
    depth: float = 0.45
    top_bars: str = "2x12mm Fe500 TMT"
    bottom_bars: str = "3x16mm Fe500 TMT"
    stirrups: str = "8mm @ 125mm c/c"
    floor: int = 1


@dataclass
class StructuralSlabSpec:
    id: str
    thickness_mm: float = 150.0
    main_bar: str = "8mm @ 150mm c/c Fe500"
    distribution_bar: str = "8mm @ 200mm c/c Fe500"
    dead_load_kn: float = 3.75  # kN/m2
    live_load_kn: float = 2.0   # kN/m2
    floor: int = 1


@dataclass
class BOQEstimate:
    concrete_volume_m3: float = 0.0
    steel_weight_tons: float = 0.0
    brickwork_m2: float = 0.0
    flooring_m2: float = 0.0
    glass_m2: float = 0.0
    mep_cost_usd: float = 0.0
    cost_usd: float = 0.0
    cost_inr: float = 0.0
    cost_eur: float = 0.0


@dataclass
class RoomSpec:
    id: str
    name: str
    room_type: str
    x: float  # bottom-left X in meters
    y: float  # bottom-left Y in meters
    width: float  # X span in meters
    height: float  # Y span in meters
    floor: int = 1
    color: str = "#E8F0FE"
    target_area: float | None = None

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class PillarSpec:
    id: str
    x: float  # center X in meters
    y: float  # center Y in meters
    width: float = 0.4  # meters
    height: float = 0.4  # meters
    shape: str = "rectangular"  # 'rectangular' or 'cylindrical'
    floor: int = 1


@dataclass
class BeamSpec:
    id: str
    x1: float
    y1: float
    x2: float
    y2: float
    width: float = 0.3  # beam width in meters
    depth: float = 0.4  # beam depth in meters
    floor: int = 1


@dataclass
class DoorSpec:
    id: str
    x: float  # center X
    y: float  # center Y
    width: float = 0.9  # standard door width (90 cm)
    orientation: str = "horizontal"  # 'horizontal' or 'vertical'
    swing: int = 1  # 1 for positive offset, -1 for negative offset
    door_type: str = "single"  # 'single', 'double', 'sliding'
    floor: int = 1


@dataclass
class WindowSpec:
    id: str
    x: float  # center X
    y: float  # center Y
    width: float = 1.2  # window width (1.2m)
    orientation: str = "horizontal"  # 'horizontal' or 'vertical'
    window_type: str = "standard"  # 'standard', 'sliding', 'picture'
    floor: int = 1


@dataclass
class StairSpec:
    id: str
    x: float  # bottom-left X
    y: float  # bottom-left Y
    width: float = 1.2  # width of staircase flight in meters
    length: float = 3.0  # length of staircase flight in meters
    orientation: str = "vertical"  # 'horizontal' or 'vertical'
    stair_type: str = "straight"  # 'straight', 'u-shaped', 'l-shaped'
    direction: str = "up"  # 'up' or 'down'
    num_steps: int = 16
    floor: int = 1


@dataclass
class FixtureSpec:
    id: str
    fixture_type: str  # 'toilet', 'sink', 'bathtub', 'shower', 'kitchen_counter', 'stove', 'refrigerator', 'bed', 'wardrobe', 'sofa', 'dining_table'
    name: str
    x: float  # center X
    y: float  # center Y
    width: float
    height: float
    rotation: float = 0.0  # degrees
    floor: int = 1


@dataclass
class AxisGridSpec:
    label: str  # e.g., '1', '2', 'A', 'B'
    position: float  # coordinate in meters
    axis_type: str  # 'x' (vertical line at X) or 'y' (horizontal line at Y)


@dataclass
class WallSpec:
    x1: float
    y1: float
    x2: float
    y2: float
    thickness: float = 0.25
    is_exterior: bool = False
    floor: int = 1


@dataclass
class MainGateSpec:
    id: str
    x: float  # center X on plot boundary
    y: float  # center Y on plot boundary
    width: float = 3.5  # meters
    gate_type: str = "double_swing"  # 'double_swing', 'sliding', 'modern_slat', 'wrought_iron'
    side: str = "front"  # 'front', 'back', 'left', 'right'
    pillar_width: float = 0.5  # width of gate pillars
    height: float = 2.2  # 3D extrusion height in meters
    floor: int = 1


@dataclass
class GardenAreaSpec:
    id: str
    name: str = "Front Garden & Lawn"
    x: float = 0.0  # bottom-left X
    y: float = 0.0  # bottom-left Y
    width: float = 10.0  # X span
    height: float = 5.0  # Y span
    garden_type: str = "front_lawn"  # 'front_lawn', 'side_garden', 'courtyard'
    has_pathway: bool = True
    tree_count: int = 3
    floor: int = 1

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class Annotation:
    text: str
    x: float
    y: float
    z: float = 0.0
    category: str = "general"  # 'room_label', 'dimension', 'pillar_tag', 'beam_tag', 'title', 'stair_tag', 'axis_tag', 'gate_tag', 'garden_tag'
    style_props: dict = field(default_factory=dict)


@dataclass
class BuildingModel:
    plot: PlotDimensions
    style: ArchitecturalStyle = ArchitecturalStyle.MODERN
    rooms: list[RoomSpec] = field(default_factory=list)
    pillars: list[PillarSpec] = field(default_factory=list)
    beams: list[BeamSpec] = field(default_factory=list)
    walls: list[WallSpec] = field(default_factory=list)
    boundary_walls: list[WallSpec] = field(default_factory=list)
    main_gates: list[MainGateSpec] = field(default_factory=list)
    gardens: list[GardenAreaSpec] = field(default_factory=list)
    doors: list[DoorSpec] = field(default_factory=list)
    windows: list[WindowSpec] = field(default_factory=list)
    stairs: list[StairSpec] = field(default_factory=list)
    fixtures: list[FixtureSpec] = field(default_factory=list)
    axis_grids: list[AxisGridSpec] = field(default_factory=list)
    annotations: list[Annotation] = field(default_factory=list)
    structural_columns: list[StructuralColumnSpec] = field(default_factory=list)
    structural_beams: list[StructuralBeamSpec] = field(default_factory=list)
    structural_slabs: list[StructuralSlabSpec] = field(default_factory=list)
    boq_estimate: BOQEstimate | None = None
    prompt: str = ""
    metadata: dict = field(default_factory=dict)

    def total_building_area(self, floor: int = 1) -> float:
        return sum(r.area for r in self.rooms if r.floor == floor)

    def total_garden_area(self) -> float:
        return sum(g.area for g in self.gardens)



@dataclass
class Blueprint2DConfig:
    grid_spacing: float = 1.0  # grid line spacing in meters
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
    theme: str = "Classic Blueprint"  # 'Classic Blueprint' (blue), 'Architectural Dark', 'Paper White'


