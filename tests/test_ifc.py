"""
Unit tests for build_matrix/cad_ifc.py (OpenBIM IFC4 generator).
Verifies that generated files conform to ISO 10303-21 STEP physical format
and contain semantic architectural building elements.
"""
import os
import tempfile

import pytest

from build_matrix.cad_ifc import IFCGenerator
from build_matrix.engineering import EngineeringEngine
from build_matrix.exporter import ExporterEngine
from build_matrix.models import (
    ArchitecturalStyle,
    BeamSpec,
    BuildingModel,
    PillarSpec,
    PlotDimensions,
    RoomSpec,
    WallSpec,
)


@pytest.fixture
def bim_building() -> BuildingModel:
    plot = PlotDimensions(length=18.0, width=12.0, num_floors=2, floor_height=3.2)
    model = BuildingModel(plot=plot, style=ArchitecturalStyle.MODERN)

    # Rooms
    model.rooms.extend([
        RoomSpec(id="r1", name="Living Room", room_type="living", x=1.0, y=1.0, width=6.0, height=5.0, floor=1),
        RoomSpec(id="r2", name="Kitchen", room_type="kitchen", x=8.0, y=1.0, width=4.0, height=4.0, floor=1),
        RoomSpec(id="r3", name="Master Bedroom", room_type="bedroom", x=1.0, y=1.0, width=5.0, height=4.5, floor=2),
    ])

    # Columns
    model.pillars.extend([
        PillarSpec(id="c1", x=0.0, y=0.0, width=0.30, height=0.30, floor=1),
        PillarSpec(id="c2", x=9.0, y=0.0, width=0.30, height=0.30, floor=1),
        PillarSpec(id="c3", x=18.0, y=0.0, width=0.30, height=0.30, floor=1),
    ])

    # Beams
    model.beams.extend([
        BeamSpec(id="b1", x1=0.0, y1=0.0, x2=9.0, y2=0.0, width=0.23, depth=0.45, floor=1),
        BeamSpec(id="b2", x1=9.0, y1=0.0, x2=18.0, y2=0.0, width=0.23, depth=0.45, floor=1),
    ])

    # Walls
    model.walls.extend([
        WallSpec(x1=0.0, y1=0.0, x2=18.0, y2=0.0, thickness=0.20, floor=1),
        WallSpec(x1=18.0, y1=0.0, x2=18.0, y2=12.0, thickness=0.20, floor=1),
    ])

    # Structural engineering run to generate slabs
    EngineeringEngine.calculate_engineering_schedules(model)
    return model


class TestIFCGenerator:
    def test_ifc_step_header(self, bim_building):
        ifc_str = IFCGenerator.generate_ifc(bim_building)
        assert isinstance(ifc_str, str)
        assert "ISO-10303-21;" in ifc_str
        assert "HEADER;" in ifc_str
        assert "FILE_SCHEMA(('IFC4'));" in ifc_str
        assert "DATA;" in ifc_str
        assert "ENDSEC;" in ifc_str
        assert "END-ISO-10303-21;" in ifc_str

    def test_ifc_spatial_hierarchy(self, bim_building):
        ifc_str = IFCGenerator.generate_ifc(bim_building)
        assert "IFCPROJECT(" in ifc_str
        assert "IFCSITE(" in ifc_str
        assert "IFCBUILDING(" in ifc_str
        assert "IFCBUILDINGSTOREY(" in ifc_str
        assert "IFCRELAGGREGATES(" in ifc_str
        assert "IFCRELCONTAINEDINSPATIALSTRUCTURE(" in ifc_str

    def test_ifc_semantic_elements(self, bim_building):
        ifc_str = IFCGenerator.generate_ifc(bim_building)
        assert "IFCWALLSTANDARDCASE(" in ifc_str
        assert "IFCCOLUMN(" in ifc_str
        assert "IFCBEAM(" in ifc_str
        assert "IFCSLAB(" in ifc_str
        assert "IFCSPACE(" in ifc_str
        assert "IFCEXTRUDEDAREASOLID(" in ifc_str

    def test_exporter_engine_export_ifc(self, bim_building):
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            out = ExporterEngine.export_3d_ifc(bim_building, tmp_path)
            assert os.path.exists(out)
            assert os.path.getsize(out) > 1000
            with open(out, encoding="utf-8") as f:
                content = f.read()
                assert "ISO-10303-21;" in content
                assert "IFC4" in content
                assert "END-ISO-10303-21;" in content
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
