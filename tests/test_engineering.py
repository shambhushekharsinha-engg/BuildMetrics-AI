import pytest
from build_matrix.models import BuildingModel, PlotDimensions, StructuralColumnSpec, StructuralBeamSpec, StructuralSlabSpec, WallSpec, WindowSpec
from build_matrix.engineering import EngineeringEngine

def test_calculate_boq():
    plot = PlotDimensions(length=10.0, width=10.0, num_floors=2, floor_height=3.0)
    building = BuildingModel(plot=plot)
    
    # Add dummy elements
    building.structural_columns = [
        StructuralColumnSpec(id="C1", column_code="C1", x=0, y=0, width=0.5, depth=0.5),
        StructuralColumnSpec(id="C2", column_code="C2", x=10, y=10, width=0.5, depth=0.5)
    ]
    building.structural_beams = [
        StructuralBeamSpec(id="B1", beam_code="B1", x1=0, y1=0, x2=10, y2=0, width=0.3, depth=0.5)
    ]
    building.structural_slabs = [
        StructuralSlabSpec(id="S1", thickness_mm=150.0)
    ]
    building.walls = [
        WallSpec(x1=0, y1=0, x2=10, y2=0, thickness=0.25)
    ]
    building.windows = [
        WindowSpec(id="W1", x=5, y=0, width=2.0)
    ]
    
    boq = EngineeringEngine.calculate_boq(building)
    
    # 2 columns * (0.5 * 0.5 * 3.0) = 1.5 m3
    # 1 beam * (0.3 * 0.5 * 10.0) = 1.5 m3
    # 1 slab * (10*10 * 0.15) = 15.0 m3
    # foundation = 100 * 0.45 = 45.0 m3
    # total concrete = 1.5 + 1.5 + 15 + 45 = 63.0 m3
    assert boq.concrete_volume_m3 == 63.0
    
    # Steel = 63.0 * 105.0 / 1000 = 6.615 -> 6.62 tons
    assert boq.steel_weight_tons == 6.62
    
    # Brickwork = 10m * 3.0m = 30.0 m2
    assert boq.brickwork_m2 == 30.0
    
    # Glass = 2.0 * 1.5 = 3.0 m2
    assert boq.glass_m2 == 3.0
    
    # Flooring = 200m2 built area * 0.85 = 170.0 m2
    assert boq.flooring_m2 == 170.0
    
    # Check currency conversions roughly
    assert boq.cost_usd > 0
    assert boq.cost_inr > 0
    assert boq.cost_eur > 0
    assert boq.cost_inr > boq.cost_usd * 80  # very rough assertion for sanity
