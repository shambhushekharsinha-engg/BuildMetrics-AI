"""
BUILD-MATRIX.ai Labeling & Annotation Manager
Computes structural annotations, room area labels, pillar/beam callouts, dimension lines, compass directions, and title block metadata.
"""

from .models import Annotation, BuildingModel


class LabelingManager:
    """Manages dimension annotations, structural tags, room information labels, and metadata for blueprints."""

    @classmethod
    def annotate_building(cls, building: BuildingModel) -> None:
        """Generates annotations directly onto the BuildingModel instance."""
        building.annotations.clear()

        # 1. Overall Plot Outer Dimension Annotations
        plot = building.plot

        # Top length dimension
        building.annotations.append(
            Annotation(
                text=f"PLOT LENGTH: {plot.length:.2f} m",
                x=plot.length / 2,
                y=plot.width + 0.8,
                z=0.0,
                category="dimension",
                style_props={"align": "center", "orientation": "horizontal", "type": "plot_outer"},
            )
        )

        # Right width dimension
        building.annotations.append(
            Annotation(
                text=f"PLOT WIDTH: {plot.width:.2f} m",
                x=plot.length + 0.8,
                y=plot.width / 2,
                z=0.0,
                category="dimension",
                style_props={"align": "center", "orientation": "vertical", "type": "plot_outer"},
            )
        )

        # Height constraint annotation
        building.annotations.append(
            Annotation(
                text=f"MAX HEIGHT: {plot.max_height:.1f} m ({plot.num_floors} Floors)",
                x=0.0,
                y=-0.8,
                z=0.0,
                category="title",
                style_props={"align": "left"},
            )
        )

        # 2. Room Annotations (Name, Dimensions, Area)
        for room in building.rooms:
            text_lines = [
                f"{room.name.upper()}",
                f"{room.width:.2f}m x {room.height:.2f}m",
                f"Area: {room.area:.2f} m²",
            ]
            full_text = "\n".join(text_lines)

            building.annotations.append(
                Annotation(
                    text=full_text,
                    x=room.x + room.width / 2,
                    y=room.y + room.height / 2,
                    z=(room.floor - 1) * plot.floor_height + 0.5,
                    category="room_label",
                    style_props={
                        "room_id": room.id,
                        "floor": room.floor,
                        "color": "#1A237E",
                        "font_size": 9,
                    },
                )
            )

        # 3. Structural Pillar Annotations (P1, P2...)
        for pillar in building.pillars:
            building.annotations.append(
                Annotation(
                    text=f"[{pillar.id}]",
                    x=pillar.x,
                    y=pillar.y + 0.3,
                    z=(pillar.floor - 1) * plot.floor_height + 0.2,
                    category="pillar_tag",
                    style_props={"floor": pillar.floor, "color": "#D32F2F", "font_size": 7},
                )
            )

        # 4. Structural Beam Annotations (BH1, BV1...)
        for beam in building.beams:
            mid_x = (beam.x1 + beam.x2) / 2
            mid_y = (beam.y1 + beam.y2) / 2
            building.annotations.append(
                Annotation(
                    text=f"{beam.id}",
                    x=mid_x,
                    y=mid_y,
                    z=(beam.floor - 1) * plot.floor_height + plot.floor_height - 0.2,
                    category="beam_tag",
                    style_props={"floor": beam.floor, "color": "#E65100", "font_size": 6},
                )
            )

        # 5. Stair Annotations (STAIRWELL 16 RISERS UP ->)
        for stair in building.stairs:
            stair_text = f"STAIR ({stair.direction.upper()} →)\n{stair.num_steps} RISERS @ 0.18m"
            building.annotations.append(
                Annotation(
                    text=stair_text,
                    x=stair.x + stair.width / 2,
                    y=stair.y + stair.length / 2,
                    z=(stair.floor - 1) * plot.floor_height + 0.3,
                    category="stair_tag",
                    style_props={"floor": stair.floor, "color": "#00796B", "font_size": 7},
                )
            )

        # 6. Door Tag Annotations (D1, D2...)
        for door in building.doors:
            building.annotations.append(
                Annotation(
                    text=door.id,
                    x=door.x,
                    y=door.y + (0.25 if door.orientation == "horizontal" else 0.0),
                    z=(door.floor - 1) * plot.floor_height + 0.1,
                    category="door_tag",
                    style_props={"floor": door.floor, "color": "#0288D1", "font_size": 6},
                )
            )

        # 7. Window Tag Annotations (W1, W2...)
        for win in building.windows:
            building.annotations.append(
                Annotation(
                    text=win.id,
                    x=win.x,
                    y=win.y + (0.25 if win.orientation == "horizontal" else 0.0),
                    z=(win.floor - 1) * plot.floor_height + 0.1,
                    category="window_tag",
                    style_props={"floor": win.floor, "color": "#0097A7", "font_size": 6},
                )
            )

        # 8. Main Gate Annotations
        for gate in building.main_gates:
            building.annotations.append(
                Annotation(
                    text=f"[MAIN GATE - {gate.width:.1f}m]",
                    x=gate.x,
                    y=gate.y - 0.4,
                    z=0.0,
                    category="gate_tag",
                    style_props={"color": "#E65100", "font_size": 8},
                )
            )

        # 9. Garden Area Annotations
        for garden in building.gardens:
            building.annotations.append(
                Annotation(
                    text=f"{garden.name.upper()}\n({garden.area:.1f} m²)",
                    x=garden.x + garden.width / 2,
                    y=garden.y + garden.height / 2,
                    z=0.0,
                    category="garden_tag",
                    style_props={"color": "#2E7D32", "font_size": 8},
                )
            )

        # 10. Axis Grid Bubble Annotations
        for grid in building.axis_grids:
            if grid.axis_type == "x":
                building.annotations.append(
                    Annotation(
                        text=f"({grid.label})",
                        x=grid.position,
                        y=plot.width + 0.4,
                        category="axis_tag",
                        style_props={"axis": "x"},
                    )
                )
            else:
                building.annotations.append(
                    Annotation(
                        text=f"({grid.label})",
                        x=-0.4,
                        y=grid.position,
                        category="axis_tag",
                        style_props={"axis": "y"},
                    )
                )

    @classmethod
    def get_title_block_data(cls, building: BuildingModel, floor: int = 1) -> dict[str, str]:
        """Generates standard architectural title block metadata dict."""
        plot = building.plot
        total_area = building.total_building_area(floor=floor)

        return {
            "PROJECT_TITLE": "Buildmetrics-AI ARCHITECTURAL BLUEPRINT",
            "ARCHITECTURAL_STYLE": building.style.value,
            "FLOOR_LEVEL": f"FLOOR {floor} OF {plot.num_floors}",
            "PLOT_DIMENSIONS": f"{plot.length:.2f}m x {plot.width:.2f}m ({plot.length * plot.width:.2f} m²)",
            "TOTAL_BUILT_AREA": f"{total_area:.2f} m²",
            "SCALE": "1 : 100",
            "UNITS": "METRIC (m / m²)",
            "STATUS": "APPROVED ARCHITECTURAL DRAFT",
        }

