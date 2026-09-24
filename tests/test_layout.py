from build_matrix.input_handler import InputHandler
from build_matrix.layout_engine import LayoutEngine
from build_matrix.models import ArchitecturalStyle, PlotDimensions


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
    for floor in range(1, plot.num_floors + 1):
        floor_rooms = [r for r in building.rooms if r.floor == floor]
        for i, r1 in enumerate(floor_rooms):
            assert r1.x >= plot.margin
            assert r1.y >= plot.margin
            assert r1.x + r1.width <= plot.length - plot.margin + 0.01
            assert r1.y + r1.height <= plot.width - plot.margin + 0.01
            
            # Pairwise overlap check
            for j, r2 in enumerate(floor_rooms):
                if i >= j: continue
                overlap_x = (r1.x < r2.x + r2.width - 0.01) and (r1.x + r1.width > r2.x + 0.01)
                overlap_y = (r1.y < r2.y + r2.height - 0.01) and (r1.y + r1.height > r2.y + 0.01)
                assert not (overlap_x and overlap_y), f"Room overlap detected: {r1.name} and {r2.name}"

    # 4. Ensure engineering solver extracted valid walls/pillars exist
    assert len(building.pillars) > 0
    assert len(building.beams) > 0
    assert len(building.walls) > 0
