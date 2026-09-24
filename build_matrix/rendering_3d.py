"""
Buildmetrics AI 3D Renderer & WebGL Generator
Extrudes 2D blueprints into 3D volumetric building meshes using Trimesh and generates interactive Three.js HTML 3D viewports.
"""

import json

import numpy as np
import trimesh

from .models import (
    ArchitecturalStyle,
    BuildingModel,
)


class Blueprint3DRenderer:
    """3D mesh builder and interactive WebGL scene generator for architectural models."""

    import typing

    STYLE_ROOF_TYPES: typing.ClassVar[dict] = {
        ArchitecturalStyle.MODERN: "flat",
        ArchitecturalStyle.MINIMALIST: "flat",
        ArchitecturalStyle.CLASSIC: "gable",
        ArchitecturalStyle.INDUSTRIAL: "flat",
        ArchitecturalStyle.BRUTALIST: "flat",
        ArchitecturalStyle.LUXURY_VILLA: "hip",
        ArchitecturalStyle.CONTEMPORARY: "flat",
        ArchitecturalStyle.CRAFTSMAN: "gable",
        ArchitecturalStyle.JAPANDI: "hip",
        ArchitecturalStyle.SCANDINAVIAN: "gable",
        ArchitecturalStyle.TROPICAL: "hip",
        ArchitecturalStyle.MEDITERRANEAN: "hip",
    }


    def __init__(self, building: BuildingModel):
        self.building = building

    def build_trimesh_scene(self) -> trimesh.Scene:
        """Constructs a composite 3D Trimesh Scene consisting of walls, pillars, beams, stairs, doors, windows, fixtures, floors, and roof."""
        scene = trimesh.Scene()
        plot = self.building.plot

        # 1. Foundation Slab
        foundation = trimesh.creation.box(
            extents=[plot.length, plot.width, 0.3],
            transform=trimesh.transformations.translation_matrix([plot.length / 2, plot.width / 2, -0.15]),
        )
        foundation.visual.face_colors = [120, 140, 160, 255]
        scene.add_geometry(foundation, node_name="Foundation")

        # 2. Extrude Walls for each floor
        for floor in range(1, plot.num_floors + 1):
            floor_z = (floor - 1) * plot.floor_height
            floor_walls = [w for w in self.building.walls if w.floor == floor]

            for idx, w in enumerate(floor_walls):
                dx = w.x2 - w.x1
                dy = w.y2 - w.y1
                wall_length = np.hypot(dx, dy)
                if wall_length < 0.05:
                    continue

                angle = np.arctan2(dy, dx)
                wall_box = trimesh.creation.box(extents=[wall_length, w.thickness, plot.floor_height])

                mid_x = (w.x1 + w.x2) / 2
                mid_y = (w.y1 + w.y2) / 2
                mid_z = floor_z + plot.floor_height / 2

                matrix = trimesh.transformations.translation_matrix([mid_x, mid_y, mid_z])
                rot_matrix = trimesh.transformations.rotation_matrix(angle, [0, 0, 1])
                transform = trimesh.transformations.concatenate_matrices(matrix, rot_matrix)

                wall_box.apply_transform(transform)

                if w.is_exterior:
                    wall_box.visual.face_colors = [200, 220, 240, 255]
                else:
                    wall_box.visual.face_colors = [230, 230, 230, 255]

                scene.add_geometry(wall_box, node_name=f"Wall_F{floor}_{idx}")

        # 3. Extrude Pillars (Columns)
        for idx, p in enumerate(self.building.pillars):
            floor_z = (p.floor - 1) * plot.floor_height
            pillar_h = plot.floor_height

            if p.shape == "cylindrical":
                pillar_mesh = trimesh.creation.cylinder(radius=p.width / 2, height=pillar_h)
            else:
                pillar_mesh = trimesh.creation.box(extents=[p.width, p.height, pillar_h])

            transform = trimesh.transformations.translation_matrix([p.x, p.y, floor_z + pillar_h / 2])
            pillar_mesh.apply_transform(transform)
            pillar_mesh.visual.face_colors = [220, 50, 50, 255]

            scene.add_geometry(pillar_mesh, node_name=f"Pillar_{p.id}")

        # 4. Extrude Beams
        for idx, b in enumerate(self.building.beams):
            floor_z = (b.floor - 1) * plot.floor_height + plot.floor_height - b.depth / 2
            dx = b.x2 - b.x1
            dy = b.y2 - b.y1
            span = np.hypot(dx, dy)
            if span < 0.05:
                continue

            angle = np.arctan2(dy, dx)
            beam_mesh = trimesh.creation.box(extents=[span, b.width, b.depth])

            mid_x = (b.x1 + b.x2) / 2
            mid_y = (b.y1 + b.y2) / 2

            matrix = trimesh.transformations.translation_matrix([mid_x, mid_y, floor_z])
            rot_matrix = trimesh.transformations.rotation_matrix(angle, [0, 0, 1])
            transform = trimesh.transformations.concatenate_matrices(matrix, rot_matrix)

            beam_mesh.apply_transform(transform)
            beam_mesh.visual.face_colors = [240, 140, 40, 255]

            scene.add_geometry(beam_mesh, node_name=f"Beam_{b.id}")

        # 5. Extrude Staircases
        for idx, s in enumerate(self.building.stairs):
            floor_z = (s.floor - 1) * plot.floor_height
            num_steps = s.num_steps
            step_dz = plot.floor_height / num_steps
            step_dy = s.length / num_steps

            for step_i in range(num_steps):
                step_box = trimesh.creation.box(extents=[s.width, step_dy, (step_i + 1) * step_dz])
                sx = s.x + s.width / 2
                sy = s.y + step_i * step_dy + step_dy / 2
                sz = floor_z + (step_i + 1) * step_dz / 2

                transform = trimesh.transformations.translation_matrix([sx, sy, sz])
                step_box.apply_transform(transform)
                step_box.visual.face_colors = [0, 150, 136, 255]
                scene.add_geometry(step_box, node_name=f"Stair_{s.id}_step{step_i}")

        # 6. Extrude Doors & Windows (Frames and Panes)
        for idx, d in enumerate(self.building.doors):
            floor_z = (d.floor - 1) * plot.floor_height
            frame = trimesh.creation.box(extents=[d.width, 0.15, 2.1])
            transform = trimesh.transformations.translation_matrix([d.x, d.y, floor_z + 1.05])
            frame.apply_transform(transform)
            frame.visual.face_colors = [139, 69, 19, 255]
            scene.add_geometry(frame, node_name=f"DoorFrame_{d.id}")

        for idx, w in enumerate(self.building.windows):
            floor_z = (d.floor - 1) * plot.floor_height + 1.0
            win_box = trimesh.creation.box(extents=[w.width, 0.1, 1.2])
            transform = trimesh.transformations.translation_matrix([w.x, w.y, floor_z + 0.6])
            win_box.apply_transform(transform)
            win_box.visual.face_colors = [79, 195, 247, 180]
            scene.add_geometry(win_box, node_name=f"Window_{w.id}")

        # 8. Boundary Compound Wall (3D)
        for idx, bw in enumerate(getattr(self.building, "boundary_walls", [])):
            dx = bw.x2 - bw.x1
            dy = bw.y2 - bw.y1
            wall_len = np.hypot(dx, dy)
            if wall_len < 0.05:
                continue
            angle = np.arctan2(dy, dx)
            bwall_box = trimesh.creation.box(extents=[wall_len, bw.thickness, 2.0])
            mid_x = (bw.x1 + bw.x2) / 2
            mid_y = (bw.y1 + bw.y2) / 2
            matrix = trimesh.transformations.translation_matrix([mid_x, mid_y, 1.0])
            rot_matrix = trimesh.transformations.rotation_matrix(angle, [0, 0, 1])
            transform = trimesh.transformations.concatenate_matrices(matrix, rot_matrix)
            bwall_box.apply_transform(transform)
            bwall_box.visual.face_colors = [140, 150, 160, 255]
            scene.add_geometry(bwall_box, node_name=f"BoundaryWall_{idx}")

        # 9. Main Gates (3D Pillars + Gate Bars)
        for idx, mg in enumerate(getattr(self.building, "main_gates", [])):
            pw = mg.pillar_width
            gh = mg.height
            # Left Pillar
            lp = trimesh.creation.box(extents=[pw, pw, gh + 0.2])
            lp.apply_transform(trimesh.transformations.translation_matrix([mg.x - mg.width / 2 - pw / 2, mg.y, (gh + 0.2) / 2]))
            lp.visual.face_colors = [180, 70, 70, 255]
            scene.add_geometry(lp, node_name=f"MainGate_LPillar_{idx}")
            # Right Pillar
            rp = trimesh.creation.box(extents=[pw, pw, gh + 0.2])
            rp.apply_transform(trimesh.transformations.translation_matrix([mg.x + mg.width / 2 + pw / 2, mg.y, (gh + 0.2) / 2]))
            rp.visual.face_colors = [180, 70, 70, 255]
            scene.add_geometry(rp, node_name=f"MainGate_RPillar_{idx}")
            # Gate Panel Mesh
            gp = trimesh.creation.box(extents=[mg.width, 0.1, gh])
            gp.apply_transform(trimesh.transformations.translation_matrix([mg.x, mg.y, gh / 2]))
            gp.visual.face_colors = [40, 40, 50, 240]
            scene.add_geometry(gp, node_name=f"MainGate_Panel_{idx}")

        # 10. Garden Area (3D Grass Lawn + Trees)
        for idx, gd in enumerate(getattr(self.building, "gardens", [])):
            lawn_mesh = trimesh.creation.box(
                extents=[gd.width, gd.height, 0.05],
                transform=trimesh.transformations.translation_matrix([gd.x + gd.width / 2, gd.y + gd.height / 2, 0.025]),
            )
            lawn_mesh.visual.face_colors = [46, 125, 50, 255]
            scene.add_geometry(lawn_mesh, node_name=f"Garden_Lawn_{idx}")

            if gd.tree_count > 0:
                spacing = gd.width / (gd.tree_count + 1)
                for t_i in range(1, gd.tree_count + 1):
                    tx = gd.x + t_i * spacing
                    ty = gd.y + gd.height * 0.5
                    trunk = trimesh.creation.cylinder(radius=0.12, height=1.8)
                    trunk.apply_transform(trimesh.transformations.translation_matrix([tx, ty, 0.9]))
                    trunk.visual.face_colors = [101, 67, 33, 255]
                    scene.add_geometry(trunk, node_name=f"Tree_Trunk_{idx}_{t_i}")
                    foliage = trimesh.creation.icosphere(subdivisions=2, radius=0.8)
                    foliage.apply_transform(trimesh.transformations.translation_matrix([tx, ty, 2.2]))
                    foliage.visual.face_colors = [34, 139, 34, 255]
                    scene.add_geometry(foliage, node_name=f"Tree_Foliage_{idx}_{t_i}")

        # 11. Steel Rods Reinforcement Frame (3D Rebar Cages)
        for p in self.building.pillars:
            floor_z = (p.floor - 1) * plot.floor_height
            pillar_h = plot.floor_height
            cover = 0.04
            rw = (p.width / 2) - cover
            rh = (p.height / 2) - cover
            corner_offsets = [(-rw, -rh), (rw, -rh), (rw, rh), (-rw, rh)]
            if p.width > 0.45:
                corner_offsets.extend([(0, -rh), (0, rh), (-rw, 0), (rw, 0)])

            for rod_i, (ox, oy) in enumerate(corner_offsets):
                rod = trimesh.creation.cylinder(radius=0.016, height=pillar_h)
                rod.apply_transform(trimesh.transformations.translation_matrix([p.x + ox, p.y + oy, floor_z + pillar_h / 2]))
                rod.visual.face_colors = [176, 190, 197, 255]
                scene.add_geometry(rod, node_name=f"Rebar_Column_{p.id}_Rod_{rod_i}")

            num_stirrups = int(pillar_h / 0.22)
            for s_i in range(1, num_stirrups + 1):
                tie_z = floor_z + s_i * 0.22
                tie = trimesh.creation.box(extents=[max(0.05, p.width - cover * 2), max(0.05, p.height - cover * 2), 0.01])
                tie.apply_transform(trimesh.transformations.translation_matrix([p.x, p.y, tie_z]))
                tie.visual.face_colors = [255, 183, 77, 255]
                scene.add_geometry(tie, node_name=f"Rebar_Column_{p.id}_Stirrup_{s_i}")

        for b in self.building.beams:
            dx = b.x2 - b.x1
            dy = b.y2 - b.y1
            span = float(np.hypot(dx, dy))
            if span < 0.05:
                continue
            angle = float(np.arctan2(dy, dx))
            floor_z = (b.floor - 1) * plot.floor_height + plot.floor_height - b.depth / 2
            mid_x = (b.x1 + b.x2) / 2
            mid_y = (b.y1 + b.y2) / 2
            cover = 0.035
            rod_offsets = [
                (-(b.width / 2 - cover), (b.depth / 2 - cover)),
                ((b.width / 2 - cover), (b.depth / 2 - cover)),
                (-(b.width / 2 - cover), -(b.depth / 2 - cover)),
                ((b.width / 2 - cover), -(b.depth / 2 - cover))
            ]

            for rod_i, (ox, oz) in enumerate(rod_offsets):
                rod = trimesh.creation.cylinder(radius=0.014, height=span)
                rx = mid_x + ox * np.sin(angle)
                ry = mid_y - ox * np.cos(angle)
                rz = floor_z + oz

                matrix = trimesh.transformations.translation_matrix([rx, ry, rz])
                rot_z = trimesh.transformations.rotation_matrix(angle, [0, 0, 1])
                rot_x = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
                transform = trimesh.transformations.concatenate_matrices(matrix, rot_z, rot_x)
                rod.apply_transform(transform)
                rod.visual.face_colors = [176, 190, 197, 255]
                scene.add_geometry(rod, node_name=f"Rebar_Beam_{b.id}_Rod_{rod_i}")

        # Wall Rebar Mesh (Vertical Steel Rods for all walls)
        for w_idx, w in enumerate(self.building.walls):
            dx = w.x2 - w.x1
            dy = w.y2 - w.y1
            wall_len = float(np.hypot(dx, dy))
            if wall_len < 0.05:
                continue
            angle = float(np.arctan2(dy, dx))
            floor_z = (w.floor - 1) * plot.floor_height
            mid_x = (w.x1 + w.x2) / 2
            mid_y = (w.y1 + w.y2) / 2
            rod_spacing = 0.45

            num_vert = int(wall_len / rod_spacing)
            for i in range(num_vert + 1):
                dist = i * rod_spacing - wall_len / 2
                rx = mid_x + dist * np.cos(angle)
                ry = mid_y + dist * np.sin(angle)
                vrod = trimesh.creation.cylinder(radius=0.008, height=plot.floor_height)
                vrod.apply_transform(trimesh.transformations.translation_matrix([rx, ry, floor_z + plot.floor_height / 2]))
                vrod.visual.face_colors = [176, 190, 197, 255]
                scene.add_geometry(vrod, node_name=f"Rebar_Wall_{w_idx}_VRod_{i}")

        return scene

    def generate_threejs_html(self, render_mode: str = "Blueprint") -> str:
        """Generates a complete standalone interactive Three.js 3D WebGL viewer with Orbit Controls and 3D annotations."""
        plot = self.building.plot

        cost_per_m2 = 0
        if hasattr(self.building, "boq_estimate") and self.building.boq_estimate:
            total_area = sum(r.area for r in self.building.rooms)
            if total_area > 0:
                cost_per_m2 = self.building.boq_estimate.cost_usd / total_area

        scene_data = {
            "plot": {"length": plot.length, "width": plot.width, "height": plot.max_height, "floors": plot.num_floors, "floor_h": plot.floor_height, "cost_per_m2": cost_per_m2},
            "rooms": [{"id": f"room_{i}", "name": r.name, "x": r.x, "y": r.y, "w": r.width, "h": r.height, "floor": r.floor, "color": r.color, "area": r.area, "est_cost": round(r.area * cost_per_m2)} for i, r in enumerate(self.building.rooms)],
            "walls": [{"x1": w.x1, "y1": w.y1, "x2": w.x2, "y2": w.y2, "ext": w.is_exterior, "floor": w.floor} for w in self.building.walls],
            "boundary_walls": [{"x1": w.x1, "y1": w.y1, "x2": w.x2, "y2": w.y2} for w in getattr(self.building, "boundary_walls", [])],
            "main_gates": [{"id": g.id, "x": g.x, "y": g.y, "w": g.width, "type": g.gate_type, "pw": g.pillar_width, "h": g.height} for g in getattr(self.building, "main_gates", [])],
            "gardens": [{"id": g.id, "name": g.name, "x": g.x, "y": g.y, "w": g.width, "h": g.height, "trees": g.tree_count} for g in getattr(self.building, "gardens", [])],
            "pillars": [{"id": p.id, "x": p.x, "y": p.y, "w": p.width, "h": p.height, "shape": p.shape, "floor": p.floor, "load_cap": round(600.0 * p.floor + (plot.num_floors - p.floor + 1) * 350.0, 1)} for p in self.building.pillars],
            "beams": [{"id": b.id, "x1": b.x1, "y1": b.y1, "x2": b.x2, "y2": b.y2, "w": b.width, "d": b.depth, "floor": b.floor} for b in self.building.beams],
            "doors": [{"id": d.id, "x": d.x, "y": d.y, "w": d.width, "orient": d.orientation, "type": getattr(d, "door_type", "single"), "floor": d.floor} for d in self.building.doors],
            "windows": [{"id": w.id, "x": w.x, "y": w.y, "w": w.width, "orient": w.orientation, "floor": w.floor} for w in self.building.windows],
            "stairs": [{"id": s.id, "x": s.x, "y": s.y, "w": s.width, "l": s.length, "steps": s.num_steps, "dir": s.direction, "floor": s.floor} for s in self.building.stairs],
            "fixtures": [{"id": f.id, "type": f.fixture_type, "name": f.name, "x": f.x, "y": f.y, "w": f.width, "h": f.height, "floor": f.floor} for f in self.building.fixtures],
            "style": self.building.style.value,
        }

        json_str = json.dumps(scene_data)

        html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buildmetrics AI 3D Architectural Blueprint Visualizer</title>
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; font-family: 'Segoe UI', Arial, sans-serif; background-color: #0d1117; color: #fff; }}
        #canvas-container {{ width: 100vw; height: 100vh; display: block; }}
        #ui-panel {{ position: absolute; top: 15px; left: 15px; background: rgba(13, 17, 23, 0.88); backdrop-filter: blur(10px); padding: 16px 22px; border-radius: 10px; border: 1px solid #30363d; box-shadow: 0 8px 24px rgba(0,0,0,0.6); font-size: 13px; max-width: 340px; }}
        #ui-panel h2 {{ margin: 0 0 8px 0; font-size: 17px; color: #58a6ff; letter-spacing: 0.5px; }}
        .control-group {{ margin-top: 10px; }}
        .control-group label {{ display: block; font-weight: bold; margin-bottom: 4px; color: #8b949e; }}
        .btn-group {{ display: flex; gap: 6px; }}
        button {{ flex: 1; background: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all 0.2s; }}
        button:hover {{ background: #30363d; color: #58a6ff; border-color: #58a6ff; }}
        button.active {{ background: #1f6feb; color: #fff; border-color: #388bfd; }}
        #legend {{ position: absolute; bottom: 15px; right: 15px; background: rgba(13, 17, 23, 0.88); padding: 14px; border-radius: 8px; border: 1px solid #30363d; font-size: 11px; }}
        .legend-item {{ display: flex; align-items: center; margin-bottom: 4px; }}
        .legend-color {{ width: 12px; height: 12px; border-radius: 2px; margin-right: 8px; }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/PointerLockControls.js"></script>
</head>
<body>
    <div id="ui-panel">
        <h2>📐 Buildmetrics AI 3D Studio</h2>
        <div><strong>Style:</strong> <span id="style-val">{self.building.style.value}</span></div>
        <div><strong>Plot Footprint:</strong> {plot.length:.1f}m x {plot.width:.1f}m ({plot.max_height:.1f}m H)</div>
        
        <div class="control-group">
            <label>Render Mode:</label>
            <div class="btn-group">
                <button id="btn-blueprint" onclick="setRenderMode('blueprint')">Blueprint Cyan</button>
                <button id="btn-shaded" onclick="setRenderMode('shaded')">Realistic Shaded</button>
                <button id="btn-rebar" class="active" onclick="setRenderMode('rebar')">Steel Rods Frame</button>
                <button id="btn-wireframe" onclick="setRenderMode('wireframe')">Wireframe</button>
            </div>
        </div>

        <div class="control-group">
            <label>Toggles:</label>
            <div class="btn-group">
                <button id="btn-toggle-stairs" class="active" onclick="toggleLayer('stairs')">Stairs</button>
                <button id="btn-toggle-fixtures" class="active" onclick="toggleLayer('fixtures')">Furniture</button>
                <button id="btn-toggle-gate" class="active" onclick="toggleLayer('gate')">Main Gate</button>
                <button id="btn-toggle-garden" class="active" onclick="toggleLayer('garden')">Garden</button>
                <button id="btn-toggle-boundary" class="active" onclick="toggleLayer('boundary')">Boundary Wall</button>
                <button id="btn-toggle-roof" class="active" onclick="toggleLayer('roof')">Roof</button>
            </div>
        </div>

        <div class="control-group">
            <label>Floor Visibility:</label>
            <div class="btn-group">
                <button id="btn-f0" onclick="setFloorFilter(0)" class="active">All Floors</button>
                <button id="btn-f1" onclick="setFloorFilter(1)">Floor 1</button>
                <button id="btn-f2" onclick="setFloorFilter(2)">Floor 2</button>
            </div>
        </div>

        <div class="control-group">
            <label>Camera:</label>
            <div class="btn-group">
                <button id="btn-orbit" class="active" onclick="setCameraView('orbit')">Orbit</button>
                <button id="btn-top" onclick="setCameraView('top')">Top View</button>
                <button id="btn-front" onclick="setCameraView('front')">Front</button>
                <button id="btn-walkthrough" onclick="enterWalkthrough()" title="WASD + Mouse to move">🚶 Walkthrough</button>
            </div>
        </div>

        <div class="control-group">
            <label>Lighting Setup:</label>
            <div class="btn-group">
                <button id="btn-light-day" class="active" onclick="setLighting('day')">Daylight</button>
                <button id="btn-light-golden" onclick="setLighting('golden')">Golden Hour</button>
                <button id="btn-light-night" onclick="setLighting('night')">Night Neon</button>
            </div>
        </div>
    </div>

    <div id="legend">
        <div class="legend-item"><div class="legend-color" style="background:#b0bec5; border:1px solid #78909c;"></div> TMT Vertical Rebar Rods</div>
        <div class="legend-item"><div class="legend-color" style="background:#ffb74d;"></div> Stirrup Lateral Ties</div>
        <div class="legend-item"><div class="legend-color" style="background:#81c784;"></div> Floor Slab Mesh Grid</div>
        <div class="legend-item"><div class="legend-color" style="background:#1f6feb;"></div> Outer & Interior Walls</div>
        <div class="legend-item"><div class="legend-color" style="background:#e65100;"></div> Main Gate & Posts</div>
        <div class="legend-item"><div class="legend-color" style="background:#2e7d32;"></div> Garden Lawn & Trees</div>
    </div>

    
    <div id="canvas-container"></div>
    <div id="tooltip" style="display:none; position:absolute; background:rgba(13,17,23,0.95); padding:12px; border:1px solid #58a6ff; border-radius:6px; color:#c9d1d9; font-size:13px; pointer-events:none; z-index:200; box-shadow:0 4px 12px rgba(0,0,0,0.8);"></div>
    <div id="walkthrough-hint" style="display:none; position:absolute; bottom:20px; left:50%; transform:translateX(-50%); background:rgba(0,0,0,0.8); color:#fff; padding:10px 20px; border-radius:8px; font-size:13px; text-align:center; pointer-events:none; z-index:300; border:1px solid #58a6ff;">
        🚶 <b>Walkthrough Mode</b> &mdash; WASD / Arrows to move &middot; Mouse to look &middot; <b>ESC</b> to exit
    </div>
    <script>
        const data = {json_str};
        
        let scene, camera, renderer, controls;
        let ambientLight, dirLight;
        let buildingGroup = new THREE.Group();
        let stairsGroup = new THREE.Group();
        let fixturesGroup = new THREE.Group();
        let roofGroup = new THREE.Group();
        let gateGroup = new THREE.Group();
        let gardenGroup = new THREE.Group();
        let boundaryGroup = new THREE.Group();
        let rebarGroup = new THREE.Group();

        let materials = {{}};
        const isHighRise = data.plot.floors > 5;
        let currentMode = isHighRise ? 'shaded' : 'rebar';
        let layerState = {{ 
            stairs: !isHighRise, 
            fixtures: !isHighRise, 
            roof: true, 
            gate: true, 
            garden: true, 
            boundary: true, 
            rebar: !isHighRise 
        }};

        function init() {{
            const container = document.getElementById('canvas-container');
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0d1117);

            camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(data.plot.length * 1.4, data.plot.height * 2.2, data.plot.width * 1.6);

            renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap; // Advanced Soft Shadows
            renderer.toneMapping = THREE.ACESFilmicToneMapping; // Photorealistic tone mapping
            renderer.toneMappingExposure = 1.0;
            container.appendChild(renderer.domElement);
            
            // Phase 9: PBR & Sun-path Daylighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
            scene.add(ambientLight);
            
            const sunLight = new THREE.DirectionalLight(0xffeeb1, 1.5);
            sunLight.position.set(50, 100, 20);
            sunLight.castShadow = true;
            sunLight.shadow.mapSize.width = 2048;
            sunLight.shadow.mapSize.height = 2048;
            scene.add(sunLight);
            
            // X-Ray / Section Toggle UI Overlay
            const uiDiv = document.createElement('div');
            uiDiv.style.position = 'absolute';
            uiDiv.style.top = '10px';
            uiDiv.style.right = '10px';
            uiDiv.style.zIndex = '100';
            uiDiv.style.background = 'rgba(0,0,0,0.7)';
            uiDiv.style.padding = '10px';
            uiDiv.style.borderRadius = '5px';
            uiDiv.style.color = '#fff';
            uiDiv.style.fontFamily = 'sans-serif';
            uiDiv.innerHTML = `
                <label style="cursor:pointer; display:block; margin-bottom:5px;">
                    <input type="checkbox" id="xrayToggle"> Enable X-Ray Mode
                </label>
                <label style="cursor:pointer; display:block;">
                    <input type="range" id="sunPath" min="0" max="100" value="50"> Sun Path
                </label>
            `;
            container.appendChild(uiDiv);
            
            document.getElementById('xrayToggle').addEventListener('change', (e) => {{
                const isXray = e.target.checked;
                scene.traverse((child) => {{
                    if (child.isMesh && child.material && child.material.name !== 'wireframe') {{
                        child.material.transparent = true;
                        child.material.opacity = isXray ? 0.3 : 1.0;
                        child.material.needsUpdate = true;
                    }}
                }});
            }});
            
            document.getElementById('sunPath').addEventListener('input', (e) => {{
                const val = e.target.value / 100; // 0 to 1
                const angle = val * Math.PI; // Sunrise to sunset
                sunLight.position.set(Math.cos(angle) * 100, Math.sin(angle) * 100, 20);
            }});


            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.target.set(data.plot.length / 2, 0, data.plot.width / 2);
            controls.update();

            // Lighting — assign to outer-scope vars used by setLighting()
            ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
            scene.add(ambientLight);

            dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
            dirLight.position.set(data.plot.length * 2, data.plot.length * 2, data.plot.width * 2);
            dirLight.castShadow = true;
            dirLight.shadow.mapSize.width = 4096; // High-res shadows
            dirLight.shadow.mapSize.height = 4096;
            const d = Math.max(data.plot.length, data.plot.width) * 1.5;
            dirLight.shadow.camera.left = -d;
            dirLight.shadow.camera.right = d;
            dirLight.shadow.camera.top = d;
            dirLight.shadow.camera.bottom = -d;
            dirLight.shadow.camera.far = 1000;
            dirLight.shadow.bias = -0.0005;
            scene.add(dirLight);

            // Procedural PBR Noise/Bump Texture Generator
            function createNoiseTexture() {{
                const canvas = document.createElement('canvas');
                canvas.width = 512; canvas.height = 512;
                const context = canvas.getContext('2d');
                const imgData = context.createImageData(512, 512);
                for (let i = 0; i < imgData.data.length; i += 4) {{
                    const val = Math.random() * 255;
                    imgData.data[i] = val; imgData.data[i+1] = val; imgData.data[i+2] = val; imgData.data[i+3] = 255;
                }}
                context.putImageData(imgData, 0, 0);
                const tex = new THREE.CanvasTexture(canvas);
                tex.wrapS = THREE.RepeatWrapping;
                tex.wrapT = THREE.RepeatWrapping;
                return tex;
            }}
            const noiseTex = createNoiseTexture();

            // Advanced Contextual Topographic Terrain
            const maxDim = Math.max(data.plot.length, data.plot.width);
            const groundGeom = new THREE.PlaneGeometry(maxDim * 6, maxDim * 6, 64, 64);
            const pos = groundGeom.attributes.position;
            for(let i=0; i<pos.count; i++) {{
                const u = pos.getX(i);
                const v = pos.getY(i);
                const distToCenter = Math.sqrt(u*u + v*v);
                // Keep the building plot flat, add rolling hills to the periphery
                if (distToCenter > maxDim * 0.7) {{
                    const height = (Math.sin(u * 0.05) * Math.cos(v * 0.05)) * (distToCenter - maxDim * 0.7) * 0.15;
                    pos.setZ(i, height);
                }}
            }}
            groundGeom.computeVertexNormals();
            const groundMat = new THREE.MeshStandardMaterial({{ color: 0x1b4332, roughness: 0.9, bumpMap: noiseTex, bumpScale: 0.2 }});
            const groundMesh = new THREE.Mesh(groundGeom, groundMat);
            groundMesh.rotation.x = -Math.PI / 2;
            groundMesh.position.set(data.plot.length / 2, -0.05, data.plot.width / 2);
            groundMesh.receiveShadow = true;
            scene.add(groundMesh);

            // Ground Grid Helper
            const gridHelper = new THREE.GridHelper(maxDim * 2.5, 50, 0x81c784, 0x4caf50);
            gridHelper.position.set(data.plot.length / 2, 0.01, data.plot.width / 2);
            scene.add(gridHelper);

            // Photorealistic PBR Materials
            materials = {{
                blueprint_wall: new THREE.MeshStandardMaterial({{ color: 0x1f6feb, roughness: 0.3, metalness: 0.1, transparent: true, opacity: 0.88 }}),
                blueprint_pillar: new THREE.MeshStandardMaterial({{ color: 0xd32f2f, roughness: 0.2, metalness: 0.3, bumpMap: noiseTex, bumpScale: 0.05 }}),
                blueprint_beam: new THREE.MeshStandardMaterial({{ color: 0xf57c00, roughness: 0.3, metalness: 0.2, bumpMap: noiseTex, bumpScale: 0.05 }}),
                blueprint_stair: new THREE.MeshStandardMaterial({{ color: 0x00796b, roughness: 0.4 }}),
                blueprint_door: new THREE.MeshStandardMaterial({{ color: 0x8d6e63, roughness: 0.6, bumpMap: noiseTex, bumpScale: 0.02 }}),
                blueprint_glass: new THREE.MeshPhysicalMaterial({{ color: 0x80deea, transmission: 0.9, opacity: 1, transparent: true, roughness: 0.1, ior: 1.5 }}),
                shaded_ext_wall: new THREE.MeshStandardMaterial({{ color: 0xe0e0e0, roughness: 0.4, bumpMap: noiseTex, bumpScale: 0.08 }}),
                shaded_int_wall: new THREE.MeshStandardMaterial({{ color: 0xf5f5f5, roughness: 0.6, bumpMap: noiseTex, bumpScale: 0.04 }}),
                fixture_mat: new THREE.MeshStandardMaterial({{ color: 0xb0bec5, roughness: 0.5, metalness: 0.3 }}),
                wireframe: new THREE.MeshBasicMaterial({{ color: 0x58a6ff, wireframe: true }}),
                roof: new THREE.MeshStandardMaterial({{ color: 0x37474f, roughness: 0.6, metalness: 0.2, bumpMap: noiseTex, bumpScale: 0.1 }}),
                gate_pillar: new THREE.MeshStandardMaterial({{ color: 0xc62828, roughness: 0.4 }}),
                gate_door: new THREE.MeshStandardMaterial({{ color: 0x263238, roughness: 0.2, metalness: 0.8 }}),
                garden_lawn: new THREE.MeshStandardMaterial({{ color: 0x2e7d32, roughness: 0.9, bumpMap: noiseTex, bumpScale: 0.15 }}),
                tree_foliage: new THREE.MeshStandardMaterial({{ color: 0x1b5e20, roughness: 0.7 }}),
                tree_trunk: new THREE.MeshStandardMaterial({{ color: 0x4e342e, roughness: 0.9, bumpMap: noiseTex, bumpScale: 0.05 }}),
                boundary_wall: new THREE.MeshStandardMaterial({{ color: 0x607d8b, roughness: 0.5, bumpMap: noiseTex, bumpScale: 0.1 }}),
                steel_rod: new THREE.MeshStandardMaterial({{ color: 0xb0bec5, roughness: 0.25, metalness: 0.85 }}),
                steel_stirrup: new THREE.MeshStandardMaterial({{ color: 0xffb74d, roughness: 0.35, metalness: 0.80 }}),
                steel_mesh: new THREE.MeshStandardMaterial({{ color: 0x81c784, roughness: 0.4, metalness: 0.70 }}),
                ghost_concrete: new THREE.MeshPhysicalMaterial({{ color: 0x1f6feb, transparent: true, opacity: 0.14, roughness: 0.1, ior: 1.2 }})
            }};

            buildBuildingScene();
            scene.add(buildingGroup);
            scene.add(stairsGroup);
            scene.add(fixturesGroup);
            scene.add(roofGroup);
            scene.add(gateGroup);
            scene.add(gardenGroup);
            scene.add(boundaryGroup);
            scene.add(rebarGroup);


            window.addEventListener('resize', onWindowResize);
            
            // --- RAYCASTER FOR TRACEABILITY ---
            const raycaster = new THREE.Raycaster();
            const mouse = new THREE.Vector2();
            const tooltip = document.getElementById('tooltip');
            
            window.addEventListener('pointerdown', (e) => {{
                if (e.target.tagName === 'BUTTON' || e.target.tagName === 'INPUT' || e.target.closest('#ui-panel')) return;
                
                mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
                mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
                raycaster.setFromCamera(mouse, camera);
                
                const intersects = raycaster.intersectObjects(buildingGroup.children);
                let found = null;
                for (let i = 0; i < intersects.length; i++) {{
                    if (intersects[i].object.userData && intersects[i].object.userData.type) {{
                        found = intersects[i].object;
                        break;
                    }}
                }}
                
                if (found) {{
                    const ud = found.userData;
                    let html = `<b style="color:#58a6ff;">${{ud.type}}</b><br/>`;
                    if (ud.type === 'Room') {{
                        html += `<b>${{ud.name.toUpperCase()}}</b> (Floor ${{ud.floor}})<br/>`;
                        html += `Area: ${{ud.area.toFixed(1)}} m²<br/>`;
                        html += `Est. Cost: <span style="color:#3fb950;">$${{ud.est_cost.toLocaleString()}}</span>`;
                    }} else if (ud.type === 'Structural Column') {{
                        html += `ID: ${{ud.id}} (Floor ${{ud.floor}})<br/>`;
                        html += `Max Load Capacity: <span style="color:#ff7b72;">${{ud.load_cap}} kN</span>`;
                    }} else if (ud.type === 'Structural Beam') {{
                        html += `ID: ${{ud.id}} (Floor ${{ud.floor}})<br/>`;
                        html += `Span: ${{ud.span}} m`;
                    }}
                    tooltip.innerHTML = html;
                    tooltip.style.display = 'block';
                    tooltip.style.left = (e.clientX + 15) + 'px';
                    tooltip.style.top = (e.clientY + 15) + 'px';
                }} else {{
                    tooltip.style.display = 'none';
                }}
            }});

            animate();
        }}

        // --- WALKTHROUGH CAMERA (Phase 9: First-Person PointerLockControls) ---
        let pointerLockControls = null;
        let walkthroughActive = false;
        const walkthroughKeys = {{ w: false, a: false, s: false, d: false, ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false }};
        let walkthroughVelocity = new THREE.Vector3();
        const walkthroughSpeed = 0.05;
        let walkthroughClock = new THREE.Clock();
        let orbitControlsRef = null;

        function enterWalkthrough() {{
            if (!pointerLockControls) {{
                pointerLockControls = new THREE.PointerLockControls(camera, renderer.domElement);
                scene.add(pointerLockControls.getObject());
                // Store reference to orbit controls to disable it
                orbitControlsRef = controls;

                document.addEventListener('keydown', (e) => {{ if (e.code in walkthroughKeys) walkthroughKeys[e.code] = true; }});
                document.addEventListener('keyup', (e) => {{ if (e.code in walkthroughKeys) walkthroughKeys[e.code] = false; }});

                pointerLockControls.addEventListener('unlock', () => {{
                    walkthroughActive = false;
                    if (orbitControlsRef) orbitControlsRef.enabled = true;
                    document.getElementById('btn-walkthrough').classList.remove('active');
                    document.getElementById('walkthrough-hint').style.display = 'none';
                }});

                pointerLockControls.addEventListener('lock', () => {{
                    walkthroughActive = true;
                    if (orbitControlsRef) orbitControlsRef.enabled = false;
                    document.getElementById('walkthrough-hint').style.display = 'block';
                }});
            }}

            // Position camera at floor level inside the building
            camera.position.set(
                data.plot.length * 0.3,
                1.7,  // Eye height 1.7m
                data.plot.width * 0.3
            );
            document.getElementById('btn-walkthrough').classList.add('active');
            pointerLockControls.lock();
        }}

        function updateWalkthrough(delta) {{
            if (!walkthroughActive || !pointerLockControls || !pointerLockControls.isLocked) return;

            walkthroughVelocity.x = 0;
            walkthroughVelocity.z = 0;

            const speed = walkthroughSpeed * (delta / 0.016);
            if (walkthroughKeys['w'] || walkthroughKeys['ArrowUp']) pointerLockControls.moveForward(speed);
            if (walkthroughKeys['s'] || walkthroughKeys['ArrowDown']) pointerLockControls.moveForward(-speed);
            if (walkthroughKeys['a'] || walkthroughKeys['ArrowLeft']) pointerLockControls.moveRight(-speed);
            if (walkthroughKeys['d'] || walkthroughKeys['ArrowRight']) pointerLockControls.moveRight(speed);

            // Clamp camera to valid floor range
            const camY = pointerLockControls.getObject().position.y;
            if (camY < 0.5) pointerLockControls.getObject().position.y = 1.7;
        }}

        function buildBuildingScene() {{
            buildingGroup.clear();
            stairsGroup.clear();
            fixturesGroup.clear();
            roofGroup.clear();
            gateGroup.clear();
            gardenGroup.clear();
            boundaryGroup.clear();

            const wallThick = 0.25;
            const floorH = data.plot.floor_h;


            // 0. Rooms (Floor Plates for Raycasting)
            data.rooms.forEach((r) => {{
                const geom = new THREE.BoxGeometry(r.w, Math.max(r.h, 0.1), 0.05);
                const mat = new THREE.MeshBasicMaterial({{ color: 0x1f6feb, transparent: true, opacity: 0.1, depthWrite: false }});
                const mesh = new THREE.Mesh(geom, mat);
                const midX = r.x + r.w / 2;
                const midZ = r.y + r.h / 2;
                const midY = (r.floor - 1) * floorH + 0.025;
                mesh.position.set(midX, midY, midZ);
                mesh.rotation.x = -Math.PI / 2;
                mesh.userData = {{ type: 'Room', name: r.name, floor: r.floor, area: r.area, est_cost: r.est_cost }};
                buildingGroup.add(mesh);
            }});
            
            // 1. Walls
            data.walls.forEach((w) => {{
                const dx = w.x2 - w.x1;
                const dy = w.y2 - w.y1;
                const len = Math.hypot(dx, dy);
                if (len < 0.05) return;

                const angle = Math.atan2(dy, dx);
                const geom = new THREE.BoxGeometry(len, floorH, wallThick);
                const mat = currentMode === 'wireframe' ? materials.wireframe : (currentMode === 'blueprint' ? materials.blueprint_wall : (w.ext ? materials.shaded_ext_wall : materials.shaded_int_wall));

                const mesh = new THREE.Mesh(geom, mat);
                const midX = (w.x1 + w.x2) / 2;
                const midZ = (w.y1 + w.y2) / 2;
                const midY = (w.floor - 1) * floorH + floorH / 2;

                mesh.position.set(midX, midY, midZ);
                mesh.rotation.y = -angle;
                mesh.userData = {{ type: "Wall", floor: w.floor, exterior: w.ext }};
                mesh.castShadow = true;
                mesh.receiveShadow = true;
                buildingGroup.add(mesh);
            }});

            // 2. Pillars
            data.pillars.forEach(p => {{
                const pillarH = floorH;
                const geom = p.shape === 'cylindrical' ? new THREE.CylinderGeometry(p.w/2, p.w/2, pillarH, 16) : new THREE.BoxGeometry(p.w, pillarH, p.h);
                const mat = currentMode === 'wireframe' ? materials.wireframe : materials.blueprint_pillar;
                const mesh = new THREE.Mesh(geom, mat);
                const midY = (p.floor - 1) * floorH + pillarH / 2;
                mesh.position.set(p.x, midY, p.y);
                mesh.castShadow = true;
                mesh.userData = {{ type: "Structural Column", id: p.id, floor: p.floor, load_cap: p.load_cap }};
                buildingGroup.add(mesh);
            }});

            // 3. Beams
            data.beams.forEach(b => {{
                const dx = b.x2 - b.x1;
                const dy = b.y2 - b.y1;
                const span = Math.hypot(dx, dy);
                if (span < 0.05) return;

                const angle = Math.atan2(dy, dx);
                const geom = new THREE.BoxGeometry(span, b.d, b.w);
                const mat = currentMode === 'wireframe' ? materials.wireframe : materials.blueprint_beam;
                const mesh = new THREE.Mesh(geom, mat);

                const midX = (b.x1 + b.x2) / 2;
                const midZ = (b.y1 + b.y2) / 2;
                const midY = (b.floor - 1) * floorH + floorH - b.d / 2;

                mesh.position.set(midX, midY, midZ);
                mesh.rotation.y = -angle;
                mesh.userData = {{ type: "Structural Beam", id: b.id, floor: b.floor, span: span.toFixed(2) }};
                buildingGroup.add(mesh);
            }});

            // 4. Doors & Windows
            data.doors.forEach(d => {{
                const geom = new THREE.BoxGeometry(d.w, 2.1, 0.15);
                const mat = currentMode === 'wireframe' ? materials.wireframe : materials.blueprint_door;
                const mesh = new THREE.Mesh(geom, mat);
                const midY = (d.floor - 1) * floorH + 1.05;
                mesh.position.set(d.x, midY, d.y);
                if (d.orient === 'vertical') mesh.rotation.y = Math.PI / 2;
                buildingGroup.add(mesh);
            }});

            data.windows.forEach(w => {{
                const geom = new THREE.BoxGeometry(w.w, 1.2, 0.1);
                const mat = currentMode === 'wireframe' ? materials.wireframe : materials.blueprint_glass;
                const mesh = new THREE.Mesh(geom, mat);
                const midY = (w.floor - 1) * floorH + 1.6;
                mesh.position.set(w.x, midY, w.y);
                if (w.orient === 'vertical') mesh.rotation.y = Math.PI / 2;
                buildingGroup.add(mesh);
            }});

            // 5. Stairs (3D Step Treads)
            data.stairs.forEach(s => {{
                const steps = s.steps || 16;
                const stepDz = floorH / steps;
                const stepDy = s.l / steps;
                const floorY0 = (s.floor - 1) * floorH;

                for (let i = 0; i < steps; i++) {{
                    const stepH = (i + 1) * stepDz;
                    const geom = new THREE.BoxGeometry(s.w, stepH, stepDy);
                    const mat = currentMode === 'wireframe' ? materials.wireframe : materials.blueprint_stair;
                    const mesh = new THREE.Mesh(geom, mat);

                    const stepZ = s.y + i * stepDy + stepDy / 2;
                    const stepY = floorY0 + stepH / 2;
                    mesh.position.set(s.x + s.w / 2, stepY, stepZ);
                    stairsGroup.add(mesh);
                }}
            }});

            // 6. Fixtures & Furniture
            data.fixtures.forEach(f => {{
                const mesh = createFixtureMesh(f, currentMode, materials);
                const midY = (f.floor - 1) * floorH;
                mesh.position.set(f.x, midY, f.y);
                fixturesGroup.add(mesh);
            }});

            // 7. Roof Slab
            const roofZ0 = data.plot.floors * floorH;
            const roofGeom = new THREE.BoxGeometry(data.plot.length + 0.6, 0.4, data.plot.width + 0.6);
            const roofMesh = new THREE.Mesh(roofGeom, materials.roof);
            roofMesh.position.set(data.plot.length / 2, roofZ0 + 0.2, data.plot.width / 2);
            roofGroup.add(roofMesh);

            // 8. Boundary Compound Wall (3D)
            if (data.boundary_walls) {{
                data.boundary_walls.forEach(bw => {{
                    const dx = bw.x2 - bw.x1;
                    const dy = bw.y2 - bw.y1;
                    const len = Math.hypot(dx, dy);
                    if (len < 0.05) return;

                    const angle = Math.atan2(dy, dx);
                    const geom = new THREE.BoxGeometry(len, 2.0, 0.2);
                    const mat = currentMode === 'wireframe' ? materials.wireframe : materials.boundary_wall;
                    const mesh = new THREE.Mesh(geom, mat);

                    const midX = (bw.x1 + bw.x2) / 2;
                    const midZ = (bw.y1 + bw.y2) / 2;
                    mesh.position.set(midX, 1.0, midZ);
                    mesh.rotation.y = -angle;
                    boundaryGroup.add(mesh);
                }});
            }}

            // 9. Main Gates (3D Pillars + Metal Panel)
            if (data.main_gates) {{
                data.main_gates.forEach(g => {{
                    const pw = g.pw || 0.5;
                    const gh = g.h || 2.2;
                    const pillarGeom = new THREE.BoxGeometry(pw, gh + 0.2, pw);
                    const matPillar = currentMode === 'wireframe' ? materials.wireframe : materials.gate_pillar;
                    const matGate = currentMode === 'wireframe' ? materials.wireframe : materials.gate_door;

                    // Left Pillar
                    const lp = new THREE.Mesh(pillarGeom, matPillar);
                    lp.position.set(g.x - g.w / 2 - pw / 2, (gh + 0.2) / 2, g.y);
                    gateGroup.add(lp);

                    // Right Pillar
                    const rp = new THREE.Mesh(pillarGeom, matPillar);
                    rp.position.set(g.x + g.w / 2 + pw / 2, (gh + 0.2) / 2, g.y);
                    gateGroup.add(rp);

                    // Gate Panel Mesh
                    const gpGeom = new THREE.BoxGeometry(g.w, gh, 0.08);
                    const gp = new THREE.Mesh(gpGeom, matGate);
                    gp.position.set(g.x, gh / 2, g.y);
                    gateGroup.add(gp);
                }});
            }}

            // 10. Garden Area (3D Grass Lawn + Trees)
            if (data.gardens) {{
                data.gardens.forEach(gd => {{
                    const lawnGeom = new THREE.BoxGeometry(gd.w, 0.05, gd.h);
                    const lawnMesh = new THREE.Mesh(lawnGeom, materials.garden_lawn);
                    lawnMesh.position.set(gd.x + gd.w / 2, 0.025, gd.y + gd.h / 2);
                    gardenGroup.add(lawnMesh);

                    if (gd.trees > 0) {{
                        const spacing = gd.w / (gd.trees + 1);
                        for (let t_i = 1; t_i <= gd.trees; t_i++) {{
                            const tx = gd.x + t_i * spacing;
                            const ty = gd.y + gd.h * 0.5;
                            const trunkGeom = new THREE.CylinderGeometry(0.12, 0.12, 1.8, 8);
                            const trunk = new THREE.Mesh(trunkGeom, materials.tree_trunk);
                            trunk.position.set(tx, 0.9, ty);
                            gardenGroup.add(trunk);

                            const foliageGeom = new THREE.SphereGeometry(0.8, 8, 8);
                            const foliage = new THREE.Mesh(foliageGeom, materials.tree_foliage);
                            foliage.position.set(tx, 2.2, ty);
                            gardenGroup.add(foliage);
                        }}
                    }}
                }});
            }}

            // 11. Steel Rods Reinforcement Frame (3D Rebar Cages)
            rebarGroup.clear();
            rebarGroup.visible = layerState.rebar;
            
            // Rebar Columns (Pillar Cages)
            data.pillars.forEach(p => {{
                const pillarH = floorH;
                const floorY0 = (p.floor - 1) * floorH;
                const cover = 0.04;
                const rw = (p.w / 2) - cover;
                const rh = (p.h / 2) - cover;

                // Main Vertical TMT Steel Rods (Corner & Side Rods)
                const mainRodGeom = new THREE.CylinderGeometry(0.016, 0.016, pillarH, 8);
                const cornerOffsets = [
                    [-rw, -rh], [rw, -rh], [rw, rh], [-rw, rh]
                ];
                if (p.w > 0.45) {{
                    cornerOffsets.push([0, -rh], [0, rh], [-rw, 0], [rw, 0]);
                }}

                cornerOffsets.forEach(off => {{
                    const rod = new THREE.Mesh(mainRodGeom, materials.steel_rod);
                    rod.position.set(p.x + off[0], floorY0 + pillarH / 2, p.y + off[1]);
                    rebarGroup.add(rod);
                }});

                // Lateral Hoop Stirrup Ties (Spaced every 22cm)
                const numStirrups = Math.floor(pillarH / 0.22);
                for (let s = 1; s <= numStirrups; s++) {{
                    const tieY = floorY0 + s * 0.22;
                    // Stirrup Ring Box Frame
                    const tieGeom = new THREE.BoxGeometry(p.w - cover * 2, 0.01, p.h - cover * 2);
                    const tieMesh = new THREE.Mesh(tieGeom, materials.steel_stirrup);
                    tieMesh.position.set(p.x, tieY, p.y);
                    rebarGroup.add(tieMesh);
                }}
            }});

            // Rebar Beams (Top/Bottom Bars & Shear Stirrups)
            data.beams.forEach(b => {{
                const dx = b.x2 - b.x1;
                const dz = b.y2 - b.y1;
                const span = Math.hypot(dx, dz);
                if (span < 0.05) return;

                const angle = Math.atan2(dz, dx);
                const floorY0 = (b.floor - 1) * floorH + floorH - b.d / 2;
                const midX = (b.x1 + b.x2) / 2;
                const midZ = (b.y1 + b.y2) / 2;
                const cover = 0.035;

                // Longitudinal Steel Rods (2 Top, 2 Bottom)
                const mainBeamRodGeom = new THREE.CylinderGeometry(0.014, 0.014, span, 8);
                const rodOffsets = [
                    [-(b.w / 2 - cover), (b.d / 2 - cover)],
                    [(b.w / 2 - cover), (b.d / 2 - cover)],
                    [-(b.w / 2 - cover), -(b.d / 2 - cover)],
                    [(b.w / 2 - cover), -(b.d / 2 - cover)]
                ];

                rodOffsets.forEach(off => {{
                    const rod = new THREE.Mesh(mainBeamRodGeom, materials.steel_rod);
                    rod.position.set(midX + off[0] * Math.sin(angle), floorY0 + off[1], midZ - off[0] * Math.cos(angle));
                    rod.rotation.y = -angle;
                    rod.rotation.z = Math.PI / 2;
                    rebarGroup.add(rod);
                }});

                // Beam Shear Stirrup Rings (Spaced every 20cm)
                const numBeamStirrups = Math.floor(span / 0.20);
                for (let s = 1; s <= numBeamStirrups; s++) {{
                    const tieDist = s * 0.20 - span / 2;
                    const tieX = midX + tieDist * Math.cos(angle);
                    const tieZ = midZ + tieDist * Math.sin(angle);
                    const stirrupGeom = new THREE.BoxGeometry(b.w - cover * 2, b.d - cover * 2, 0.01);
                    const stirrupMesh = new THREE.Mesh(stirrupGeom, materials.steel_stirrup);
                    stirrupMesh.position.set(tieX, floorY0, tieZ);
                    stirrupMesh.rotation.y = -angle;
                    rebarGroup.add(stirrupMesh);
                }}
            }});

            // Slab Rebar Mesh Grids
            for (let fl = 1; fl <= data.plot.floors; fl++) {{
                const slabY = fl * floorH;
                const meshSpacing = 0.6;
                // Longitudinal X Rods
                for (let sz = 0.5; sz < data.plot.width; sz += meshSpacing) {{
                    const xRodGeom = new THREE.CylinderGeometry(0.008, 0.008, data.plot.length, 6);
                    const xRod = new THREE.Mesh(xRodGeom, materials.steel_mesh);
                    xRod.position.set(data.plot.length / 2, slabY - 0.05, sz);
                    xRod.rotation.z = Math.PI / 2;
                    rebarGroup.add(xRod);
                }}
                // Transverse Z Rods
                for (let sx = 0.5; sx < data.plot.length; sx += meshSpacing) {{
                    const zRodGeom = new THREE.CylinderGeometry(0.008, 0.008, data.plot.width, 6);
                    const zRod = new THREE.Mesh(zRodGeom, materials.steel_mesh);
                    zRod.position.set(sx, slabY - 0.04, data.plot.width / 2);
                    zRod.rotation.x = Math.PI / 2;
                    rebarGroup.add(zRod);
                }}
            }}

            // Wall Rebar Reinforcement Mesh (Vertical & Horizontal Tie Rods for all walls)
            data.walls.forEach(w => {{
                const dx = w.x2 - w.x1;
                const dy = w.y2 - w.y1;
                const len = Math.hypot(dx, dy);
                if (len < 0.05) return;

                const angle = Math.atan2(dy, dx);
                const floorY0 = (w.floor - 1) * floorH;
                const midX = (w.x1 + w.x2) / 2;
                const midZ = (w.y1 + w.y2) / 2;
                const rodSpacing = 0.45;

                // Vertical Wall Steel Rods
                const numVert = Math.floor(len / rodSpacing);
                for (let i = 0; i <= numVert; i++) {{
                    const dist = i * rodSpacing - len / 2;
                    const rx = midX + dist * Math.cos(angle);
                    const rz = midZ + dist * Math.sin(angle);
                    const vRodGeom = new THREE.CylinderGeometry(0.008, 0.008, floorH, 6);
                    const vRod = new THREE.Mesh(vRodGeom, materials.steel_rod);
                    vRod.position.set(rx, floorY0 + floorH / 2, rz);
                    rebarGroup.add(vRod);
                }}

                // Horizontal Wall Tie Rods
                const numHoriz = Math.floor(floorH / rodSpacing);
                for (let j = 1; j <= numHoriz; j++) {{
                    const ry = floorY0 + j * rodSpacing;
                    const hRodGeom = new THREE.CylinderGeometry(0.007, 0.007, len, 6);
                    const hRod = new THREE.Mesh(hRodGeom, materials.steel_stirrup);
                    hRod.position.set(midX, ry, midZ);
                    hRod.rotation.y = -angle;
                    hRod.rotation.z = Math.PI / 2;
                    rebarGroup.add(hRod);
                }}
            }});

            // Rebar Boundary Wall Framework
            if (data.boundary_walls) {{
                data.boundary_walls.forEach(bw => {{
                    const dx = bw.x2 - bw.x1;
                    const dy = bw.y2 - bw.y1;
                    const len = Math.hypot(dx, dy);
                    if (len < 0.05) return;
                    const angle = Math.atan2(dy, dx);
                    const midX = (bw.x1 + bw.x2) / 2;
                    const midZ = (bw.y1 + bw.y2) / 2;

                    const numPosts = Math.floor(len / 0.5);
                    for (let p = 0; p <= numPosts; p++) {{
                        const dist = p * 0.5 - len / 2;
                        const px = midX + dist * Math.cos(angle);
                        const pz = midZ + dist * Math.sin(angle);
                        const postGeom = new THREE.CylinderGeometry(0.01, 0.01, 2.0, 6);
                        const post = new THREE.Mesh(postGeom, materials.steel_rod);
                        post.position.set(px, 1.0, pz);
                        rebarGroup.add(post);
                    }}
                }});
            }}

            // Rebar Main Gate Framework
            if (data.main_gates) {{
                data.main_gates.forEach(g => {{
                    const gh = g.h || 2.2;
                    const numGateBars = Math.floor(g.w / 0.18);
                    for (let gb = 0; gb <= numGateBars; gb++) {{
                        const gbx = (g.x - g.w / 2) + gb * 0.18;
                        const gBarGeom = new THREE.CylinderGeometry(0.012, 0.012, gh, 8);
                        const gBar = new THREE.Mesh(gBarGeom, materials.steel_rod);
                        gBar.position.set(gbx, gh / 2, g.y);
                        rebarGroup.add(gBar);
                    }}
                }});
            }}
        }}

        function setRenderMode(mode) {{
            currentMode = mode;
            document.querySelectorAll('.control-group button').forEach(b => b.classList.remove('active'));
            const activeBtn = document.getElementById('btn-' + mode);
            if (activeBtn) activeBtn.classList.add('active');

            if (mode === 'rebar') {{
                buildingGroup.visible = false;
                stairsGroup.visible = false;
                fixturesGroup.visible = false;
                roofGroup.visible = false;
                boundaryGroup.visible = false;
                gateGroup.visible = false;
                gardenGroup.visible = false;
                rebarGroup.visible = layerState.rebar;
            }} else {{
                buildingGroup.visible = true;
                stairsGroup.visible = layerState.stairs;
                fixturesGroup.visible = layerState.fixtures;
                roofGroup.visible = layerState.roof;
                boundaryGroup.visible = layerState.boundary;
                gateGroup.visible = layerState.gate;
                gardenGroup.visible = layerState.garden;
                rebarGroup.visible = layerState.rebar;
            }}
            buildBuildingScene();
        }}

        function setCameraView(preset) {{
            const centerX = data.plot.length / 2;
            const centerZ = data.plot.width / 2;
            const h = data.plot.height;

            if (preset === 'orbit') {{
                camera.position.set(data.plot.length * 1.4, h * 2.2, data.plot.width * 1.6);
                controls.target.set(centerX, h / 3, centerZ);
            }} else if (preset === 'top') {{
                camera.position.set(centerX, Math.max(data.plot.length, data.plot.width) * 2.2, centerZ);
                controls.target.set(centerX, 0, centerZ);
            }} else if (preset === 'front') {{
                camera.position.set(centerX, h * 0.8, data.plot.width * 2.5);
                controls.target.set(centerX, h / 3, centerZ);
            }} else if (preset === 'walkthrough') {{
                camera.position.set(1.5, 1.7, 1.5);
                controls.target.set(data.plot.length / 2, 1.7, data.plot.width / 2);
            }}
            controls.update();
        }}

        function toggleLayer(layer) {{
            layerState[layer] = !layerState[layer];
            const btn = document.getElementById('btn-toggle-' + layer);
            if (btn) {{
                if (layerState[layer]) btn.classList.add('active'); else btn.classList.remove('active');
            }}

            if (layer === 'stairs') stairsGroup.visible = layerState.stairs;
            if (layer === 'fixtures') fixturesGroup.visible = layerState.fixtures;
            if (layer === 'roof') roofGroup.visible = layerState.roof;
            if (layer === 'gate') gateGroup.visible = layerState.gate;
            if (layer === 'garden') gardenGroup.visible = layerState.garden;
            if (layer === 'boundary') boundaryGroup.visible = layerState.boundary;
            if (layer === 'rebar') rebarGroup.visible = layerState.rebar;
        }}

        function setFloorFilter(floor) {{
            document.querySelectorAll('#ui-panel button[id^="btn-f"]').forEach(b => b.classList.remove('active'));
            document.getElementById('btn-f' + floor).classList.add('active');
            
            buildingGroup.children.forEach(c => {{
                c.visible = (floor === 0);
            }});
            if (floor === 0) buildBuildingScene();
        }}

        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}

        function animate() {{
            requestAnimationFrame(animate);
            const delta = walkthroughClock.getDelta();
            if (walkthroughActive) {{
                updateWalkthrough(delta);
            }} else {{
                controls.update();
            }}
            renderer.render(scene, camera);
        }}

        function setLighting(mode) {{
            document.querySelectorAll('#ui-panel button[id^="btn-light"]').forEach(b => b.classList.remove('active'));
            document.getElementById('btn-light-' + mode).classList.add('active');

            if (mode === 'day') {{
                scene.background = new THREE.Color(0x87CEEB); // Sky blue
                ambientLight.color.setHex(0xffffff);
                ambientLight.intensity = 0.75;
                dirLight.color.setHex(0xffffff);
                dirLight.intensity = 1.0;
            }} else if (mode === 'golden') {{
                scene.background = new THREE.Color(0xFD5E53); // Sunset orange
                ambientLight.color.setHex(0xffaa88);
                ambientLight.intensity = 0.5;
                dirLight.color.setHex(0xff8844);
                dirLight.intensity = 1.2;
            }} else if (mode === 'night') {{
                scene.background = new THREE.Color(0x0d1117); // Dark night
                ambientLight.color.setHex(0x224488);
                ambientLight.intensity = 0.2;
                dirLight.color.setHex(0x5588ff);
                dirLight.intensity = 0.5;
            }}
        }}

        function createFixtureMesh(f, mode, mats) {{
            const group = new THREE.Group();
            const mat = mode === 'wireframe' ? mats.wireframe : mats.fixture_mat;
            
            if (f.type === 'bed') {{
                const base = new THREE.Mesh(new THREE.BoxGeometry(f.w, 0.4, f.h), mat);
                base.position.y = 0.2;
                const headboard = new THREE.Mesh(new THREE.BoxGeometry(f.w, 1.0, 0.1), mat);
                headboard.position.set(0, 0.5, -f.h/2 + 0.05);
                group.add(base, headboard);
            }} else if (f.type === 'sofa') {{
                const seat = new THREE.Mesh(new THREE.BoxGeometry(f.w, 0.4, f.h), mat);
                seat.position.y = 0.2;
                const back = new THREE.Mesh(new THREE.BoxGeometry(f.w, 0.8, 0.2), mat);
                back.position.set(0, 0.4, -f.h/2 + 0.1);
                group.add(seat, back);
            }} else if (f.type === 'dining_table') {{
                const top = new THREE.Mesh(new THREE.BoxGeometry(f.w, 0.1, f.h), mat);
                top.position.y = 0.75;
                const legGeom = new THREE.CylinderGeometry(0.05, 0.05, 0.7);
                const l1 = new THREE.Mesh(legGeom, mat); l1.position.set(-f.w/2+0.1, 0.35, -f.h/2+0.1);
                const l2 = new THREE.Mesh(legGeom, mat); l2.position.set(f.w/2-0.1, 0.35, -f.h/2+0.1);
                const l3 = new THREE.Mesh(legGeom, mat); l3.position.set(-f.w/2+0.1, 0.35, f.h/2-0.1);
                const l4 = new THREE.Mesh(legGeom, mat); l4.position.set(f.w/2-0.1, 0.35, f.h/2-0.1);
                group.add(top, l1, l2, l3, l4);
            }} else {{
                // Default generic box
                const box = new THREE.Mesh(new THREE.BoxGeometry(f.w, f.h, f.w), mat); // using w, h, w to keep it simple since h was height in 2D
                box.position.y = f.h/2;
                group.add(box);
            }}
            return group;
        }}

        window.onload = init;
    </script>
</body>
</html>"""
        return html_code
