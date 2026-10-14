"""
BuildMetrics AI — Geotechnical & Soil Quality Foundation Engineering Engine
Evaluates soil safe bearing capacity (SBC), foundation design requirements,
excavation volumes, seismic zone detailing, and site-specific foundation civil costs.
Based on IS 1904, IS 2911, and IBC Chapter 18 geotechnical standards.
"""

from dataclasses import dataclass

from build_matrix.models import BuildingModel


@dataclass
class SoilProfile:
    id: str
    name: str
    description: str
    sbc_kpa: float              # Safe Bearing Capacity in kN/m² (kPa)
    foundation_type: str        # Recommended Foundation Type
    min_depth_m: float          # Minimum Depth of Foundation below NGL (m)
    foundation_cost_mult: float # Cost multiplier relative to baseline isolated footing
    swelling_potential: str     # None, Low, Medium, High
    settlement_risk: str        # Low, Moderate, High


SOIL_PROFILES: dict[str, SoilProfile] = {
    "hard_rock": SoilProfile(
        id="hard_rock",
        name="Hard Rock / Granite / Basalt",
        description="Solid bedrock with high compressive strength and near-zero settlement risk.",
        sbc_kpa=600.0,
        foundation_type="Shallow Isolated Rock Pad Footing",
        min_depth_m=0.8,
        foundation_cost_mult=0.75,
        swelling_potential="None",
        settlement_risk="Negligible",
    ),
    "medium_sand": SoilProfile(
        id="medium_sand",
        name="Medium-Dense Sand & Gravel",
        description="Well-graded granular soil with excellent drainage and reliable bearing strength.",
        sbc_kpa=250.0,
        foundation_type="Reinforced Isolated Spread Footings",
        min_depth_m=1.2,
        foundation_cost_mult=1.00,
        swelling_potential="Low",
        settlement_risk="Low",
    ),
    "stiff_clay": SoilProfile(
        id="stiff_clay",
        name="Stiff Clay & Alluvial Silt",
        description="Cohesive fine-grained soil with moderate consolidation and moisture sensitivity.",
        sbc_kpa=175.0,
        foundation_type="Continuous Strip / Combined Footing with Plinth Beams",
        min_depth_m=1.6,
        foundation_cost_mult=1.25,
        swelling_potential="Medium",
        settlement_risk="Moderate",
    ),
    "black_cotton": SoilProfile(
        id="black_cotton",
        name="Black Cotton / Expansive Soil",
        description="High clay content with extreme swell-shrink cycles. Requires specialized stabilization.",
        sbc_kpa=100.0,
        foundation_type="Under-Reamed Bored Piles with Sand Cushion & Grade Beams",
        min_depth_m=2.8,
        foundation_cost_mult=1.65,
        swelling_potential="High (Extreme)",
        settlement_risk="High (Differential Heave)",
    ),
    "soft_marine": SoilProfile(
        id="soft_marine",
        name="Soft Marine Clay / Reclaimed Soil",
        description="High water table, low shear strength, susceptible to long-term consolidation.",
        sbc_kpa=65.0,
        foundation_type="Raft / Mat Foundation or Driven Friction Piles",
        min_depth_m=3.5,
        foundation_cost_mult=1.95,
        swelling_potential="Low",
        settlement_risk="High (Consolidation Settlement)",
    ),
}

SEISMIC_ZONES: dict[str, dict] = {
    "Zone II (Low)": {
        "pga": 0.10,
        "hazard": "Low",
        "detailing": "Standard IS 456 RC detailing. Nominal ductile stirrup spacing.",
        "cost_adder_pct": 0.0,
    },
    "Zone III (Moderate)": {
        "pga": 0.16,
        "hazard": "Moderate",
        "detailing": "IS 13920 mandatory ductile detailing. 135° hook ties and column joint confinement.",
        "cost_adder_pct": 2.5,
    },
    "Zone IV (Severe)": {
        "pga": 0.24,
        "hazard": "Severe",
        "detailing": "Full ductile moment-resisting frame (SMRF). Shear walls recommended along building perimeter.",
        "cost_adder_pct": 5.5,
    },
    "Zone V (Very Severe)": {
        "pga": 0.36,
        "hazard": "Very Severe",
        "detailing": "Special moment frames with shear core. Continuous boundary element reinforcement. Strict rebar splice confinement.",
        "cost_adder_pct": 9.0,
    },
}


@dataclass
class GeotechReport:
    soil_profile: SoilProfile
    seismic_zone: str
    seismic_details: dict
    total_building_load_kn: float
    total_footing_area_m2: float
    footing_coverage_pct: float
    excavation_volume_m3: float
    foundation_concrete_m3: float
    foundation_steel_tons: float
    foundation_cost_usd: float
    foundation_cost_inr: float
    geotechnical_advisories: list[str]


class GeotechEngine:
    """Calculates foundation engineering specifications and soil compatibility."""

    @classmethod
    def analyze_site(
        cls,
        building: BuildingModel,
        soil_type: str = "medium_sand",
        seismic_zone: str = "Zone III (Moderate)"
    ) -> GeotechReport:
        profile = SOIL_PROFILES.get(soil_type, SOIL_PROFILES["medium_sand"])
        seismic = SEISMIC_ZONES.get(seismic_zone, SEISMIC_ZONES["Zone III (Moderate)"])

        plot = building.plot
        total_built_area = sum(r.area for r in building.rooms)

        # 1. Total Service Load on Foundation (Dead Load + Live Load)
        # Baseline dead load = 12 kN/m² per floor, Live load = 3.5 kN/m² per floor
        total_load_kn = total_built_area * 15.5

        # 2. Required Footing Base Contact Area (A = Load / SBC)
        required_area_m2 = total_load_kn / profile.sbc_kpa
        plot_area = plot.length * plot.width
        footing_coverage_pct = min(100.0, (required_area_m2 / max(1.0, plot_area)) * 100.0)

        # 3. Excavation & Foundation Material Volumetrics
        # Excavation footprint considers footing depth and 0.5m working room around perimeter
        excavation_depth = profile.min_depth_m
        excavation_vol_m3 = required_area_m2 * excavation_depth * 1.35  # bulkage factor

        # Foundation concrete: pad/raft thickness typically 0.45m - 0.75m
        slab_thickness = 0.50 if profile.sbc_kpa > 150 else 0.70
        foundation_concrete_m3 = required_area_m2 * slab_thickness

        # Steel reinforcement in foundation: ~80 kg steel per m³ concrete
        foundation_steel_tons = (foundation_concrete_m3 * 85.0) / 1000.0

        # 4. Foundation Costing
        # Baseline foundation cost per m² of footing area adjusted by soil multiplier & seismic
        base_foundation_cost = required_area_m2 * 180.0 * profile.foundation_cost_mult
        seismic_adder = base_foundation_cost * (seismic["cost_adder_pct"] / 100.0)
        foundation_cost_usd = base_foundation_cost + seismic_adder
        foundation_cost_inr = foundation_cost_usd * 83.5

        # 5. Geotechnical Advisories
        advisories: list[str] = []
        if profile.swelling_potential == "High (Extreme)":
            advisories.append("⚠️ Expansive Black Cotton Soil detected: Provide 300mm sand cushion under plinth beams to isolate foundation from vertical swelling pressure.")
            advisories.append("💧 Maintain perimeter surface drainage apron (1.5m wide concrete walkway) to prevent rainwater infiltration into foundation subgrade.")
        elif profile.sbc_kpa < 100:
            advisories.append("⚠️ Low Safe Bearing Capacity (<100 kPa): Continuous raft foundation or bored friction piles required to prevent differential settlement.")
        else:
            advisories.append("✅ Favorable Soil Bearing Capacity: Economical isolated spread footings are structurally viable.")

        if seismic["hazard"] in ("Severe", "Very Severe"):
            advisories.append(f"⚡ High Seismic Hazard ({seismic_zone}): All column ties must have 135° seismic hooks with extension ≥ 10d. Provide continuous plinth tie beams.")
        
        advisories.append("🧪 Recommendation: Conduct on-site Standard Penetration Test (SPT) borehole sampling before pouring foundation footings.")

        return GeotechReport(
            soil_profile=profile,
            seismic_zone=seismic_zone,
            seismic_details=seismic,
            total_building_load_kn=total_load_kn,
            total_footing_area_m2=required_area_m2,
            footing_coverage_pct=footing_coverage_pct,
            excavation_volume_m3=excavation_vol_m3,
            foundation_concrete_m3=foundation_concrete_m3,
            foundation_steel_tons=foundation_steel_tons,
            foundation_cost_usd=foundation_cost_usd,
            foundation_cost_inr=foundation_cost_inr,
            geotechnical_advisories=advisories,
        )
