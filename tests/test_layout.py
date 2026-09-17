import pytest
from build_matrix.models import PlotDimensions, ArchitecturalStyle
from build_matrix.layout_engine import LayoutEngine
from build_matrix.input_handler import InputHandler

def test_layout_engine_invariants():
    """
    Test invariants rather than exact room layouts because the generation
    might be heuristic/non-deterministic.
    """
    plot = PlotDimensions(length=25.0, width=15.0, max_height=12.0, num_floors=2, margin=1.0)
    layout = LayoutEngine(plot=plot, style=ArchitecturalStyle.MODERN)
    
    prompt = "A spacious modern home with 2 floors"
    prompt_parsed = InputHandler.parse_prompt(prompt)
    
    building = layout.generate_building(prompt_parsed)
    
    # 1. Check constraints on PlotDimensions
    assert building.plot.length == 25.0
    assert building.plot.width == 15.0
    assert building.plot.num_floors == 2
    
    # 2. Check total room area does not exceed available plot area per floor
    usable_length = plot.length - (2 * plot.margin)
    usable_width = plot.width - (2 * plot.margin)
    max_usable_area = usable_length * usable_width
    
    for floor in range(1, plot.num_floors + 1):
        floor_area = sum(r.area for r in building.rooms if r.floor == floor)
        assert floor_area <= max_usable_area + 0.5, f"Floor {floor} area {floor_area} exceeds plot usable area {max_usable_area}"
    
    # 3. Check room boundary overlaps or out-of-bounds
    for room in building.rooms:
        assert room.x >= plot.margin
        assert room.y >= plot.margin
        assert room.x + room.width <= plot.length - plot.margin
        assert room.y + room.height <= plot.width - plot.margin
    
    # 4. Check structural elements exist
    assert len(building.pillars) > 0
    assert len(building.beams) > 0
    assert len(building.walls) > 0
