"""
Unit tests for new civil, geotechnical, CAD DXF, and Vastu engines:
- build_matrix/cad_dxf.py (AutoCAD DXF vector generator)
- build_matrix/geotech_engine.py (Soil mechanics & foundation design)
- build_matrix/vastu_engine.py (Vastu Shastra 9-zone directional audit)
- build_matrix/engineering.py (Structural load distribution & dynamic rates)
"""
import os
import tempfile

import pytest

from build_matrix.cad_dxf import DXFGenerator
from build_matrix.engineering import EngineeringEngine
from build_matrix.exporter import ExporterEngine
from build_matrix.geotech_engine import SOIL_PROFILES, GeotechEngine
from build_matrix.models import (
    ArchitecturalStyle,
    BeamSpec,
    BuildingModel,
    PillarSpec,
    PlotDimensions,
    RoomSpec,
)
from build_matrix.vastu_engine import VastuEngine


@pytest.fixture
def sample_building() -> BuildingModel:
    plot = PlotDimensions(length=20.0, width=15.0, num_floors=2, floor_height=3.0)
    model = BuildingModel(plot=plot, style=ArchitecturalStyle.MODERN)
    
    # Add rooms
    model.rooms.extend([
        RoomSpec(id="r1", name="Master Bedroom", room_type="bedroom", x=1.0, y=1.0, width=5.0, height=4.0, floor=1),
        RoomSpec(id="r2", name="Living Room", room_type="living", x=7.0, y=8.0, width=6.0, height=5.0, floor=1),
        RoomSpec(id="r3", name="Kitchen", room_type="kitchen", x=14.0, y=1.0, width=4.0, height=4.0, floor=1),
        RoomSpec(id="r4", name="Pooja / Study", room_type="study", x=14.0, y=10.0, width=4.0, height=3.5, floor=1),
    ])
    
    # Add pillars
    for i, x in enumerate([0.0, 10.0, 20.0]):
        for j, y in enumerate([0.0, 7.5, 15.0]):
            model.pillars.append(PillarSpec(id=f"c_{i}_{j}", x=x, y=y, width=0.30, height=0.30, floor=1))
            model.pillars.append(PillarSpec(id=f"c2_{i}_{j}", x=x, y=y, width=0.30, height=0.30, floor=2))

    # Add beams
    model.beams.append(BeamSpec(id="b1", x1=0.0, y1=0.0, x2=10.0, y2=0.0, width=0.23, depth=0.45, floor=1))
    model.beams.append(BeamSpec(id="b2", x1=10.0, y1=0.0, x2=20.0, y2=0.0, width=0.23, depth=0.45, floor=1))
    
    return model


class TestCADAutoCADDXF:
    def test_dxf_generation_text_structure(self, sample_building):
        dxf_str = DXFGenerator.generate_dxf(sample_building, floor=1)
        assert isinstance(dxf_str, str)
        assert "SECTION" in dxf_str
        assert "HEADER" in dxf_str
        assert "$ACADVER" in dxf_str
        assert "AC1009" in dxf_str
        assert "TABLES" in dxf_str
        assert "A-WALL-EXT" in dxf_str
        assert "A-WALL-INT" in dxf_str
        assert "A-COLS" in dxf_str
        assert "A-BEAM" in dxf_str
        assert "A-ROMS" in dxf_str
        assert "ENTITIES" in dxf_str
        assert "EOF" in dxf_str

    def test_exporter_engine_dxf(self, sample_building):
        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            out = ExporterEngine.export_2d_dxf(sample_building, tmp_path, floor=1)
            assert os.path.exists(out)
            assert os.path.getsize(out) > 500
            with open(out, encoding="utf-8") as f:
                content = f.read()
                assert "SECTION" in content
                assert "EOF" in content
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestGeotechFoundationEngine:
    def test_soil_profiles_exist(self):
        assert "hard_rock" in SOIL_PROFILES
        assert "medium_sand" in SOIL_PROFILES
        assert "stiff_clay" in SOIL_PROFILES
        assert "black_cotton" in SOIL_PROFILES
        assert "soft_marine" in SOIL_PROFILES

    def test_analyze_site_returns_valid_metrics(self, sample_building):
        report = GeotechEngine.analyze_site(sample_building, soil_type="medium_sand", seismic_zone="Zone III (Moderate)")
        assert report.soil_profile.sbc_kpa == 250.0
        assert report.total_building_load_kn > 0
        assert report.total_footing_area_m2 > 0
        assert report.excavation_volume_m3 > 0
        assert report.foundation_concrete_m3 > 0
        assert report.foundation_steel_tons > 0
        assert report.foundation_cost_usd > 0
        assert len(report.geotechnical_advisories) > 0

    def test_black_cotton_soil_recommends_special_measures(self, sample_building):
        report = GeotechEngine.analyze_site(sample_building, soil_type="black_cotton", seismic_zone="Zone IV (Severe)")
        assert report.soil_profile.swelling_potential == "High (Extreme)"
        advisory_text = " ".join(report.geotechnical_advisories)
        assert "Black Cotton" in advisory_text or "sand cushion" in advisory_text


class TestVastuShastraEngine:
    def test_audit_building_evaluates_rooms_and_elements(self, sample_building):
        report = VastuEngine.audit_building(sample_building)
        assert 0 <= report.overall_score <= 100
        assert report.grade in ("A+ Auspicious", "A Harmonious", "B Balanced", "C Needs Remedial Cures")
        assert len(report.room_audits) == len(sample_building.rooms)
        assert "Water (Jal)" in report.element_scores
        assert "Fire (Agni)" in report.element_scores
        assert "Space (Akash)" in report.element_scores
        assert len(report.key_recommendations) > 0

    def test_room_audits_have_remedies_and_zones(self, sample_building):
        report = VastuEngine.audit_building(sample_building)
        for ra in report.room_audits:
            assert ra.zone != ""
            assert ra.compliance in ("Ideal", "Favorable", "Neutral", "Non-Compliant")
            assert ra.remedy != ""


class TestStructuralLoadDistribution:
    def test_load_distribution_metrics(self, sample_building):
        struct = EngineeringEngine.calculate_structural_load_distribution(sample_building)
        assert struct["average_safety_factor"] > 0
        assert struct["min_safety_factor"] > 0
        assert struct["max_bending_moment_knm"] > 0
        assert struct["critical_span_m"] > 0
        assert isinstance(struct["deflection_pass"], bool)
        assert len(struct["columns"]) > 0

    def test_dynamic_cost_calibration(self, sample_building):
        custom_rates = {
            "concrete_rate_usd": 150.0,
            "steel_rate_usd": 1200.0,
            "labor_multiplier": 1.25,
        }
        boq = EngineeringEngine.calculate_boq(sample_building, rates=custom_rates)
        assert boq.cost_usd > 0
        assert boq.concrete_volume_m3 > 0
        assert boq.steel_weight_tons > 0
