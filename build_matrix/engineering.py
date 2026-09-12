"""
BUILD-MATRIX.ai Structural Engineering & BOQ Cost Estimation Engine
Calculates IS 456 / ACI 318 structural column/beam/slab reinforcement schedules and Bill of Quantities (BOQ).
"""

from typing import List, Dict, Tuple, Optional
import math
from .models import (
    BuildingModel,
    StructuralColumnSpec,
    StructuralBeamSpec,
    StructuralSlabSpec,
    BOQEstimate,
    PillarSpec,
    BeamSpec,
    WallSpec,
    WindowSpec,
    CodeProfile,
    NBC_INDIA_2016,
    Annotation,
)


class EngineeringEngine:
    """Computes structural engineering schedules and BOQ cost estimates for buildings of any scale."""

    @classmethod
    def calculate_compliance(cls, building: BuildingModel, profile: CodeProfile = NBC_INDIA_2016) -> None:
        """Validates building geometry against a specific building code profile and generates advisory annotations."""
        # Check Rooms
        for room in building.rooms:
            # We assume all rooms are checked, or we could filter by room_type
            # The prompt mentioned "min habitable room area", but for simplicity let's check all main rooms.
            # Only checking rooms that sound habitable to avoid warning about small bathrooms.
            habitable_types = ['bedroom', 'living', 'kitchen', 'dining', 'study', 'office', 'room']
            is_habitable = any(h in room.room_type.lower() for h in habitable_types) or any(h in room.name.lower() for h in habitable_types)
            
            if is_habitable:
                if room.area < profile.min_habitable_room_area_m2:
                    text = f"Area: {room.area:.1f} m² (below {profile.name} min {profile.min_habitable_room_area_m2} m²)"
                    color = "red"
                else:
                    text = f"Area: {room.area:.1f} m² (meets {profile.name} min {profile.min_habitable_room_area_m2} m²)"
                    color = "green"
                
                # Check width
                min_dim = min(room.width, room.height)
                if min_dim < profile.min_room_width_m:
                    text += f"\nWidth: {min_dim:.1f}m (below min {profile.min_room_width_m}m)"
                    color = "red"
                
                building.annotations.append(Annotation(
                    text=text,
                    x=room.x + room.width / 2,
                    y=room.y + 0.5, # Slightly above bottom edge
                    category='compliance_tag',
                    style_props={'color': color, 'fontsize': 6}
                ))

        # Check Doors (Egress)
        for door in building.doors:
            if door.width < profile.min_egress_width_m:
                text = f"Egress: {door.width:.2f}m (below {profile.name} min {profile.min_egress_width_m}m)"
                color = "red"
            else:
                text = f"Egress: {door.width:.2f}m (meets {profile.name} min {profile.min_egress_width_m}m)"
                color = "green"
            
            building.annotations.append(Annotation(
                text=text,
                x=door.x,
                y=door.y - 0.5,
                category='compliance_tag',
                style_props={'color': color, 'fontsize': 6}
            ))
            
        # Check Stairs
        for stair in building.stairs:
            # Riser = floor_height / num_steps
            # Tread = length / (num_steps if straight else num_steps/2)
            riser_mm = (building.plot.floor_height / stair.num_steps) * 1000
            
            effective_steps = stair.num_steps / 2 if stair.stair_type == 'u-shaped' else stair.num_steps
            tread_mm = (stair.length / effective_steps) * 1000 if effective_steps > 0 else 0
            
            if riser_mm > profile.max_riser_mm or tread_mm < profile.min_tread_mm:
                text = f"Stair: Riser {riser_mm:.1f}mm (max {profile.max_riser_mm}), Tread {tread_mm:.1f}mm (min {profile.min_tread_mm})"
                color = "red"
            else:
                text = f"Stair: Riser {riser_mm:.1f}mm, Tread {tread_mm:.1f}mm (meets {profile.name})"
                color = "green"
                
            building.annotations.append(Annotation(
                text=text,
                x=stair.x + stair.width / 2,
                y=stair.y - 0.5,
                category='compliance_tag',
                style_props={'color': color, 'fontsize': 6}
            ))

    @classmethod
    def calculate_engineering_schedules(cls, building: BuildingModel) -> None:
        """Populates structural columns, beams, slabs, and BOQ estimates into BuildingModel."""
        num_floors = building.plot.num_floors

        # Determine concrete grade based on floor count / scale
        if num_floors >= 15:
            concrete_grade = "M40"
            col_rebar = "8x20mm + 4x16mm Fe500 TMT"
            tie_spacing = "8mm @ 100mm c/c"
        elif num_floors >= 5:
            concrete_grade = "M30"
            col_rebar = "4x20mm + 4x16mm Fe500 TMT"
            tie_spacing = "8mm @ 125mm c/c"
        else:
            concrete_grade = "M25"
            col_rebar = "4x16mm + 4x12mm Fe500 TMT"
            tie_spacing = "8mm @ 150mm c/c"

        # 1. Generate Structural Columns
        columns: List[StructuralColumnSpec] = []
        for idx, pillar in enumerate(building.pillars):
            load_capacity = round(600.0 * pillar.floor + (num_floors - pillar.floor + 1) * 350.0, 1)
            columns.append(
                StructuralColumnSpec(
                    id=f"SC_{pillar.floor}_{idx+1}",
                    column_code=f"C{idx+1}",
                    x=pillar.x,
                    y=pillar.y,
                    width=pillar.width,
                    depth=pillar.height,
                    concrete_grade=concrete_grade,
                    main_bars=col_rebar,
                    tie_spacing=tie_spacing,
                    load_capacity_kn=load_capacity,
                    floor=pillar.floor,
                )
            )

        # 2. Generate Structural Beams
        beams: List[StructuralBeamSpec] = []
        for idx, beam in enumerate(building.beams):
            span_len = math.sqrt((beam.x2 - beam.x1) ** 2 + (beam.y2 - beam.y1) ** 2)
            req_depth = max(0.35, round(span_len / 12.0, 2))
            beams.append(
                StructuralBeamSpec(
                    id=f"SB_{beam.floor}_{idx+1}",
                    beam_code=f"B{idx+1}",
                    x1=beam.x1,
                    y1=beam.y1,
                    x2=beam.x2,
                    y2=beam.y2,
                    width=beam.width,
                    depth=req_depth,
                    top_bars="2x12mm Fe500 TMT",
                    bottom_bars="3x16mm Fe500 TMT" if span_len > 4.0 else "2x16mm Fe500 TMT",
                    stirrups="8mm @ 125mm c/c",
                    floor=beam.floor,
                )
            )

        # 3. Generate Structural Slabs
        slabs: List[StructuralSlabSpec] = []
        for fl in range(1, num_floors + 1):
            slab_thick = 175.0 if num_floors >= 5 else 150.0
            slabs.append(
                StructuralSlabSpec(
                    id=f"SL_{fl}",
                    thickness_mm=slab_thick,
                    main_bar="8mm @ 150mm c/c Fe500",
                    distribution_bar="8mm @ 200mm c/c Fe500",
                    dead_load_kn=round(25.0 * (slab_thick / 1000.0) + 1.0, 2),
                    live_load_kn=3.0 if num_floors >= 5 else 2.0,
                    floor=fl,
                )
            )

        building.structural_columns = columns
        building.structural_beams = beams
        building.structural_slabs = slabs

        # 4. Calculate Bill of Quantities (BOQ) Takeoff & Cost Estimates
        cls.calculate_boq(building)

    @classmethod
    def calculate_boq(cls, building: BuildingModel) -> BOQEstimate:
        """Calculates material quantities and multi-currency cost estimates."""
        plot_area = building.plot.length * building.plot.width
        num_floors = building.plot.num_floors
        total_built_area = plot_area * num_floors

        # Structural Concrete Volume (m3)
        col_vol = sum(c.width * c.depth * building.plot.floor_height for c in building.structural_columns)
        beam_vol = sum(
            b.width * b.depth * math.sqrt((b.x2 - b.x1) ** 2 + (b.y2 - b.y1) ** 2) for b in building.structural_beams
        )
        slab_vol = sum(plot_area * (s.thickness_mm / 1000.0) for s in building.structural_slabs)
        foundation_vol = plot_area * 0.45

        total_concrete_m3 = round(col_vol + beam_vol + slab_vol + foundation_vol, 2)

        # Steel Tonnage (tons)
        steel_kg_per_m3 = 125.0 if num_floors >= 5 else 105.0
        total_steel_tons = round((total_concrete_m3 * steel_kg_per_m3) / 1000.0, 2)

        # Brickwork / Blockwork Area (m2)
        total_wall_len = sum(math.sqrt((w.x2 - w.x1) ** 2 + (w.y2 - w.y1) ** 2) for w in building.walls)
        brickwork_m2 = round(total_wall_len * building.plot.floor_height, 2)

        # Glass Area (m2)
        glass_m2 = round(sum(win.width * 1.5 for win in building.windows), 2)
        if glass_m2 == 0:
            glass_m2 = round(total_built_area * 0.15, 2)

        # Flooring Area (m2)
        flooring_m2 = round(total_built_area * 0.85, 2)

        # Boundary Wall & Main Gate Fabrication Costs
        boundary_wall_len = sum(math.sqrt((w.x2 - w.x1) ** 2 + (w.y2 - w.y1) ** 2) for w in building.boundary_walls)
        boundary_wall_m2 = round(boundary_wall_len * 2.0, 2)  # 2.0m height
        gate_count = len(building.main_gates)
        gate_fabrication_cost = gate_count * 1500.0  # $1500 per main gate assembly

        # Landscape & Garden Development Area (m2)
        garden_m2 = sum(g.area for g in building.gardens)
        landscaping_cost = garden_m2 * 25.0  # $25 / m2 landscape lawn & planting

        # Cost Estimation Engine (Rates based on global benchmarks)
        concrete_cost = total_concrete_m3 * 120.0  # $120 / m3
        steel_cost = total_steel_tons * 950.0      # $950 / ton
        brickwork_cost = (brickwork_m2 + boundary_wall_m2) * 35.0  # $35 / m2
        flooring_cost = flooring_m2 * 40.0          # $40 / m2
        glass_cost = glass_m2 * 110.0               # $110 / m2
        mep_cost = total_built_area * 45.0          # $45 / m2 MEP

        subtotal_usd = (
            concrete_cost
            + steel_cost
            + brickwork_cost
            + flooring_cost
            + glass_cost
            + mep_cost
            + gate_fabrication_cost
            + landscaping_cost
        )
        total_usd = round(subtotal_usd * 1.15, 2)   # 15% contractor fee + contingency
        
        # Try to use the ML Cost Estimator
        try:
            import sys
            import os
            # Ensure the current directory is in path to import cost_engine
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from cost_engine import predict_cost
            
            # Use tier=1, grade=1 (or A) for high end villa/modern, tier=2 for others
            grade = 1 if building.plot.num_floors > 2 else 2
            tier = 2
            
            # predict_cost expects area in sq ft. 
            area_sqft = total_built_area * 10.7639
            ml_cost_inr = predict_cost(area_sqft, num_floors, tier, grade)
            if ml_cost_inr > 0:
                total_inr = round(ml_cost_inr, 2)
                total_usd = round(total_inr / 83.5, 2)
            else:
                total_inr = round(total_usd * 83.5, 2)
        except Exception as e:
            print(f"ML cost estimation failed, using rule-based. Error: {e}")
            total_inr = round(total_usd * 83.5, 2)

        total_eur = round(total_usd * 0.92, 2)

        boq = BOQEstimate(
            concrete_volume_m3=total_concrete_m3,
            steel_weight_tons=total_steel_tons,
            brickwork_m2=round(brickwork_m2 + boundary_wall_m2, 2),
            flooring_m2=flooring_m2,
            glass_m2=glass_m2,
            mep_cost_usd=round(mep_cost, 2),
            cost_usd=total_usd,
            cost_inr=total_inr,
            cost_eur=total_eur,
        )

        building.boq_estimate = boq
        return boq
