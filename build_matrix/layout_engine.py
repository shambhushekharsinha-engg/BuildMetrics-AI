"""
BUILD-MATRIX.ai Procedural Layout Engine
Generates complete structural architectural floor plans, pillar placement grids, load-bearing beam networks, wall partitions, doors, and windows.
"""

import math
from typing import List, Dict, Tuple, Optional, Any
from .models import (
    PlotDimensions,
    ArchitecturalStyle,
    RoomSpec,
    PillarSpec,
    BeamSpec,
    WallSpec,
    DoorSpec,
    WindowSpec,
    StairSpec,
    FixtureSpec,
    AxisGridSpec,
    BuildingModel,
    Annotation,
    MainGateSpec,
    GardenAreaSpec,
)
from .labeling import LabelingManager
from .engineering import EngineeringEngine



class BSPNode:
    def __init__(self, room=None):
        self.room = room
        self.left = None
        self.right = None
        self.split_horizontal = True
        self.split_ratio = 0.5
        self.rect = (0, 0, 10, 10)
        
    def is_leaf(self): return self.room is not None

def _build_random_bsp(rooms):
    import random
    if len(rooms) == 1: return BSPNode(room=rooms[0])
    node = BSPNode()
    node.split_horizontal = random.choice([True, False])
    node.split_ratio = random.uniform(0.3, 0.7)
    random.shuffle(rooms)
    mid = len(rooms) // 2
    node.left = _build_random_bsp(rooms[:mid])
    node.right = _build_random_bsp(rooms[mid:])
    return node

def _update_rects(node, x, y, w, h):
    node.rect = (x, y, w, h)
    if node.is_leaf(): return
    if node.split_horizontal:
        h_left = h * node.split_ratio
        h_right = h - h_left
        _update_rects(node.left, x, y, w, h_left)
        _update_rects(node.right, x, y + h_left, w, h_right)
    else:
        w_left = w * node.split_ratio
        w_right = w - w_left
        _update_rects(node.left, x, y, w_left, h)
        _update_rects(node.right, x + w_left, y, w_right, h)

def _get_leaves(node):
    if node.is_leaf(): return [node]
    return _get_leaves(node.left) + _get_leaves(node.right)

def _get_all_nodes(node):
    if node.is_leaf(): return []
    return [node] + _get_all_nodes(node.left) + _get_all_nodes(node.right)

def _mutate_bsp(node):
    import copy
    import random
    new_node = copy.deepcopy(node)
    nodes = _get_all_nodes(new_node)
    if not nodes: return new_node
    target = random.choice(nodes)
    mut_type = random.choice(["ratio", "flip", "swap"])
    if mut_type == "ratio":
        target.split_ratio = min(0.8, max(0.2, target.split_ratio + random.uniform(-0.15, 0.15)))
    elif mut_type == "flip":
        target.split_horizontal = not target.split_horizontal
    elif mut_type == "swap":
        target.left, target.right = target.right, target.left
    return new_node

def _evaluate_layout(node, prev_floor_rooms):
    import math
    score = 0.0
    leaves = _get_leaves(node)
    centroids = {}
    
    for leaf in leaves:
        x, y, w, h = leaf.rect
        centroids[leaf.room["id"]] = (x + w/2, y + h/2)
        rtype = leaf.room.get("type", "Bedroom").lower()
        min_w, min_h = 2.0, 2.0
        if "bedroom" in rtype: min_w, min_h = 2.4, 2.5
        elif "kitchen" in rtype: min_w, min_h = 1.8, 2.0
        elif "bathroom" in rtype: min_w, min_h = 1.4, 1.6
        elif "living" in rtype: min_w, min_h = 3.0, 3.0
        
        if w < min_w: score -= (min_w - w) * 100
        if h < min_h: score -= (min_h - h) * 100
        
        aspect = max(w/h, h/w)
        if aspect > 3.0:
            score -= (aspect - 3.0) * 50
        
        if prev_floor_rooms and ("bathroom" in rtype or "kitchen" in rtype):
            for pr in prev_floor_rooms:
                if "bathroom" in pr.room_type.lower() or "kitchen" in pr.room_type.lower():
                    dist = math.hypot(centroids[leaf.room["id"]][0] - pr.x, centroids[leaf.room["id"]][1] - pr.y)
                    score -= dist * 20

    for l1 in leaves:
        rt1 = l1.room.get("type", "").lower()
        c1 = centroids[l1.room["id"]]
        for l2 in leaves:
            if l1 == l2: continue
            rt2 = l2.room.get("type", "").lower()
            c2 = centroids[l2.room["id"]]
            dist = math.hypot(c1[0]-c2[0], c1[1]-c2[1])
            
            if "kitchen" in rt1 and "dining" in rt2:
                score -= dist * 10
            if "bedroom" in rt1 and "living" in rt2:
                score += dist * 5
                
        if "bedroom" in rt1:
            score += c1[1] * 5
            
    return score


class LayoutEngine:
    """Procedural Architectural Spatial Solver & High-Rise Core Engine."""

    ROOM_COLOR_PALETTE = {
        "Living Room": "#E3F2FD",  # Soft Blue
        "Master Bedroom": "#F3E5F5",  # Soft Purple
        "Bedroom": "#EDE7F6",  # Soft Lavender
        "Kitchen": "#FFF3E0",  # Soft Orange/Warm
        "Dining Room": "#FFF8E1",  # Soft Yellow
        "Bathroom": "#E0F2F1",  # Soft Teal
        "Home Office": "#F1F8E9",  # Soft Sage
        "Gym": "#FBE9E7",  # Soft Coral
        "Home Theater": "#E8EAF6",  # Soft Indigo
        "Laundry": "#E0F7FA",  # Soft Cyan
        "Store Room": "#EFEBE9",  # Soft Brown/Neutral
        "Prayer Room": "#FFFDE7",  # Soft Light Gold
        "Garage": "#ECEFF1",  # Light Slate
        "Balcony / Patio": "#F4FF81",  # Soft Lime
        "Courtyard": "#E8F5E9",  # Soft Green
        "Elevator Core": "#D1C4E9",  # Soft Violet
        "Hallway": "#FAFAFA",  # Light Neutral
    }

    ROOM_WEIGHTS = {
        "Living Room": 3.5,
        "Master Bedroom": 2.8,
        "Bedroom": 2.0,
        "Kitchen": 2.2,
        "Dining Room": 2.0,
        "Home Theater": 2.5,
        "Gym": 2.0,
        "Garage": 3.0,
        "Elevator Core": 2.5,
        "Home Office": 1.8,
        "Balcony / Patio": 1.5,
        "Bathroom": 1.0,
        "Laundry": 1.0,
        "Store Room": 0.9,
        "Prayer Room": 0.9,
        "Courtyard": 2.0,
    }

    def __init__(self, plot: PlotDimensions, style: ArchitecturalStyle = ArchitecturalStyle.MODERN):
        self.plot = plot
        self.style = style

    def generate_building(self, prompt_parsed: Optional[Dict[str, Any]] = None) -> BuildingModel:
        """Main procedural generation entry point."""
        prompt_info = prompt_parsed or {}
        rooms_spec_list = prompt_info.get("rooms", [])

        # Check explicit length/width overrides from prompt parser
        if prompt_info.get("explicit_length") and prompt_info.get("explicit_width"):
            self.plot.length = prompt_info["explicit_length"]
            self.plot.width = prompt_info["explicit_width"]

        if prompt_info.get("num_floors"):
            self.plot.num_floors = prompt_info["num_floors"]

        building = BuildingModel(
            plot=self.plot,
            style=self.style,
            prompt=prompt_info.get("raw_prompt", ""),
        )

        all_pillars: List[PillarSpec] = []
        import copy

        # Variables to store typical floor geometries for rapid cloning
        typ_rooms = []; typ_walls = []; typ_pillars = []
        typ_beams = []; typ_doors = []; typ_windows = []
        typ_stairs = []; typ_fixtures = []

        for floor in range(1, self.plot.num_floors + 1):
            if floor > 2 and typ_rooms:
                # Fast Clone Mode for Typical Floors (Performance Optimization for 50-100 floors)
                def clone_elements(elements, f):
                    cloned = copy.deepcopy(elements)
                    for el in cloned:
                        el.floor = f
                        if hasattr(el, 'id'):
                            el.id = el.id.replace(f"F2_", f"F{f}_")
                    return cloned
                
                f_rooms = clone_elements(typ_rooms, floor)
                f_walls = clone_elements(typ_walls, floor)
                f_pillars = clone_elements(typ_pillars, floor)
                f_beams = clone_elements(typ_beams, floor)
                f_doors = clone_elements(typ_doors, floor)
                f_windows = clone_elements(typ_windows, floor)
                f_stairs = clone_elements(typ_stairs, floor)
                f_fixtures = clone_elements(typ_fixtures, floor)

                building.rooms.extend(f_rooms)
                building.walls.extend(f_walls)
                building.pillars.extend(f_pillars)
                all_pillars.extend(f_pillars)
                building.beams.extend(f_beams)
                building.doors.extend(f_doors)
                building.windows.extend(f_windows)
                building.stairs.extend(f_stairs)
                building.fixtures.extend(f_fixtures)
                continue

            floor_rooms = self._layout_floor_rooms(rooms_spec_list, floor)
            building.rooms.extend(floor_rooms)

            floor_walls = self._generate_walls_for_rooms(floor_rooms, floor)
            building.walls.extend(floor_walls)

            floor_pillars = self._generate_pillars(floor_rooms, floor, prompt_info.get("num_pillars"))
            building.pillars.extend(floor_pillars)
            all_pillars.extend(floor_pillars)

            floor_beams = self._generate_beams(floor_pillars, floor, prompt_info.get("num_beams"))
            building.beams.extend(floor_beams)

            floor_doors, floor_windows = self._generate_openings(floor_rooms, floor_walls, floor)
            building.doors.extend(floor_doors)
            building.windows.extend(floor_windows)

            floor_stairs = self._generate_stairs(floor_rooms, floor)
            building.stairs.extend(floor_stairs)

            floor_fixtures = self._generate_fixtures(floor_rooms, floor)
            building.fixtures.extend(floor_fixtures)

            if floor == 2:
                typ_rooms = floor_rooms
                typ_walls = floor_walls
                typ_pillars = floor_pillars
                typ_beams = floor_beams
                typ_doors = floor_doors
                typ_windows = floor_windows
                typ_stairs = floor_stairs
                typ_fixtures = floor_fixtures

        # Generate Plot Boundary Walls, Main Compound Gate, and Garden & Lawn Areas
        building.boundary_walls = self._generate_boundary_walls()
        building.main_gates = self._generate_main_gates(prompt_info, building.doors)
        building.gardens = self._generate_gardens(prompt_info, building.rooms)

        # Generate Architectural Axis Grid
        building.axis_grids = self._generate_axis_grid(all_pillars)

        # Generate automatic room tags, dimensions, structural annotations
        LabelingManager.annotate_building(building)

        # Calculate IS 456 / ACI 318 Structural Engineering Schedules & BOQ Cost Estimates
        EngineeringEngine.calculate_engineering_schedules(building)

        # Validate architectural code compliance (defaulting to NBC India 2016)
        EngineeringEngine.calculate_compliance(building)

        return building

    def _generate_boundary_walls(self) -> List[WallSpec]:
        """Generates perimeter boundary walls surrounding the plot compound."""
        l, w = self.plot.length, self.plot.width
        t = 0.20  # boundary wall thickness (20 cm)
        return [
            WallSpec(x1=0, y1=0, x2=l, y2=0, thickness=t, is_exterior=True, floor=1),
            WallSpec(x1=l, y1=0, x2=l, y2=w, thickness=t, is_exterior=True, floor=1),
            WallSpec(x1=l, y1=w, x2=0, y2=w, thickness=t, is_exterior=True, floor=1),
            WallSpec(x1=0, y1=w, x2=0, y2=0, thickness=t, is_exterior=True, floor=1),
        ]

    def _generate_main_gates(self, prompt_info: Dict[str, Any], doors: List[DoorSpec]) -> List[MainGateSpec]:
        """Generates Main Compound Gate aligned with plot entrance if requested."""
        if not prompt_info.get("include_main_gate", False):
            return []

        gate_type = prompt_info.get("main_gate_type", "double_swing")
        gate_w = min(5.0, max(3.0, self.plot.length * 0.2))

        # Align gate with main entrance door if available
        gate_x = self.plot.length / 2
        for d in doors:
            if d.floor == 1 and getattr(d, "door_type", "") == "double":
                gate_x = d.x
                break

        # Keep gate within plot bounds
        gate_x = max(gate_w / 2 + 1.0, min(self.plot.length - gate_w / 2 - 1.0, gate_x))

        return [
            MainGateSpec(
                id="MG1",
                x=round(gate_x, 2),
                y=0.0,
                width=round(gate_w, 2),
                gate_type=gate_type,
                side="front",
                pillar_width=0.5,
                height=2.2,
                floor=1,
            )
        ]

    def _generate_gardens(self, prompt_info: Dict[str, Any], rooms: List[RoomSpec]) -> List[GardenAreaSpec]:
        """Generates landscape garden area & lawn within plot setback space if requested."""
        if not prompt_info.get("include_garden", False):
            return []

        gardens: List[GardenAreaSpec] = []
        margin = self.plot.margin
        l, w = self.plot.length, self.plot.width

        # Front Lawn & Garden Area
        front_h = max(1.2, margin - 0.1)
        front_w = l - 0.8
        front_x = 0.4
        front_y = 0.2

        num_trees = max(2, min(8, int(front_w / 4.0)))

        gardens.append(
            GardenAreaSpec(
                id="G1",
                name="Front Garden & Lawn",
                x=round(front_x, 2),
                y=round(front_y, 2),
                width=round(front_w, 2),
                height=round(front_h, 2),
                garden_type=prompt_info.get("garden_type", "front_lawn"),
                has_pathway=True,
                tree_count=num_trees,
                floor=1,
            )
        )

        return gardens


    def _layout_floor_rooms(self, room_requests: List[Dict[str, Any]], floor: int) -> List[RoomSpec]:
        """Tries to generate layout using LLM, falls back to Neufert grid solver."""
        import os, json
        try:
            import google.generativeai as genai
        except ImportError:
            genai = None

        api_key = os.environ.get("GEMINI_API_KEY")
        if genai and api_key and room_requests:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                usable_w = round(self.plot.length - 2 * self.plot.margin, 2)
                usable_h = round(self.plot.width - 2 * self.plot.margin, 2)
                
                rooms_to_place = []
                if floor == 1:
                    rooms_to_place = [r for r in room_requests if "bedroom" not in r["name"].lower() or "master" in r["name"].lower()]
                    if not rooms_to_place:
                        rooms_to_place = room_requests[: max(3, len(room_requests) // 2)]
                else:
                    rooms_to_place = [r for r in room_requests]

                rooms_json = json.dumps(rooms_to_place)
                prompt = f'''
You are an expert architect. Arrange the following rooms for floor {floor} inside a plot with width {usable_w}m and depth {usable_h}m.
The origin (x=0, y=0) is the bottom-left of the usable area.
Rooms to place: {rooms_json}
Return a JSON array of objects, each containing:
"name": room name, "type": room type, "x": x-coordinate (float), "y": y-coordinate (float), "width": width (float), "height": height (float).
The rooms must not overlap, and must fit within the {usable_w}x{usable_h} area.
Ensure logical adjacencies (e.g. Living room near entrance).
Return ONLY valid JSON.
'''
                response = model.generate_content(prompt)
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                
                layout_data = json.loads(text.strip())
                
                rooms: List[RoomSpec] = []
                for idx, r_data in enumerate(layout_data):
                    r_type = r_data.get("type", "Bedroom")
                    r_name = r_data.get("name", f"Room {idx+1}")
                    color = self.ROOM_COLOR_PALETTE.get(r_type, "#F5F5F5")
                    # Shift coordinates by margin
                    x = round(float(r_data.get("x", 0)) + self.plot.margin, 2)
                    y = round(float(r_data.get("y", 0)) + self.plot.margin, 2)
                    w = round(float(r_data.get("width", 3.0)), 2)
                    h = round(float(r_data.get("height", 3.0)), 2)
                    
                    rooms.append(
                        RoomSpec(
                            id=f"F{floor}_R{len(rooms)+1}",
                            name=r_name,
                            room_type=r_type,
                            x=x, y=y, width=w, height=h,
                            floor=floor, color=color,
                        )
                    )
                if rooms:
                    return rooms
            except Exception as e:
                print(f"Generative layout failed, falling back to grid: {e}")

        return self._layout_floor_rooms_grid(room_requests, floor, prev_floor_rooms=None)

    def _layout_floor_rooms_grid(self, room_requests: List[Dict[str, Any]], floor: int, prev_floor_rooms: Optional[List[RoomSpec]] = None) -> List[RoomSpec]:
        """Constraint-Satisfaction / Simulated Annealing Spatial Solver."""
        import random
        import math
        x0 = self.plot.margin
        y0 = self.plot.margin
        usable_w = self.plot.length - 2 * self.plot.margin
        usable_h = self.plot.width - 2 * self.plot.margin

        if floor == 1:
            reqs = [r for r in room_requests if "bedroom" not in r["name"].lower() or "master" in r["name"].lower()]
            if not reqs:
                reqs = room_requests[: max(3, len(room_requests) // 2)]
        else:
            reqs = room_requests[max(3, len(room_requests) // 2):] if len(room_requests) > 3 else room_requests
            if not reqs:
                reqs = [
                    {"name": f"Bedroom {floor}-A", "type": "Bedroom"},
                    {"name": f"Bedroom {floor}-B", "type": "Bedroom"},
                    {"name": f"Bathroom {floor}", "type": "Bathroom"},
                    {"name": f"Balcony {floor}", "type": "Balcony / Patio"},
                ]

        if not reqs:
            reqs = [{"name": "Room", "type": "Bedroom"}]

        for i, r in enumerate(reqs):
            r["id"] = i

        best_bsp = _build_random_bsp(reqs)
        _update_rects(best_bsp, x0, y0, usable_w, usable_h)
        best_score = _evaluate_layout(best_bsp, prev_floor_rooms)
        
        temp = 100.0
        cooling = 0.95
        
        for i in range(200):
            candidate = _mutate_bsp(best_bsp)
            _update_rects(candidate, x0, y0, usable_w, usable_h)
            score = _evaluate_layout(candidate, prev_floor_rooms)
            
            if score > best_score or random.random() < math.exp((score - best_score) / temp):
                best_bsp = candidate
                best_score = score
                
            temp *= cooling
            if temp < 0.1: temp = 0.1

        _update_rects(best_bsp, x0, y0, usable_w, usable_h)
        
        rooms = []
        for leaf in _get_leaves(best_bsp):
            rx, ry, rw, rh = leaf.rect
            r_type = leaf.room.get("type", "Living Room")
            r_name = leaf.room.get("name", "Room")
            color = self.ROOM_COLOR_PALETTE.get(r_type, "#F5F5F5")
            
            rooms.append(
                RoomSpec(
                    id=f"F{floor}_R{len(rooms)+1}",
                    name=r_name,
                    room_type=r_type,
                    x=round(rx, 2),
                    y=round(ry, 2),
                    width=round(rw, 2),
                    height=round(rh, 2),
                    floor=floor,
                    color=color,
                )
            )
            
        return rooms

    def _generate_walls_for_rooms(self, rooms: List[RoomSpec], floor: int) -> List[WallSpec]:
        """Extracts exterior boundary walls and interior dividing walls from room geometry."""
        walls: List[WallSpec] = []
        x0 = self.plot.margin
        y0 = self.plot.margin
        x1 = self.plot.length - self.plot.margin
        y1 = self.plot.width - self.plot.margin
        t = self.plot.wall_thickness

        # Outer perimeter walls
        walls.append(WallSpec(x1=x0, y1=y0, x2=x1, y2=y0, thickness=t, is_exterior=True, floor=floor))
        walls.append(WallSpec(x1=x1, y1=y0, x2=x1, y2=y1, thickness=t, is_exterior=True, floor=floor))
        walls.append(WallSpec(x1=x1, y1=y1, x2=x0, y2=y1, thickness=t, is_exterior=True, floor=floor))
        walls.append(WallSpec(x1=x0, y1=y1, x2=x0, y2=y0, thickness=t, is_exterior=True, floor=floor))

        # Interior room boundary walls
        for room in rooms:
            # Right wall
            if abs(room.x + room.width - x1) > 0.1:
                walls.append(
                    WallSpec(
                        x1=room.x + room.width,
                        y1=room.y,
                        x2=room.x + room.width,
                        y2=room.y + room.height,
                        thickness=t * 0.7,
                        is_exterior=False,
                        floor=floor,
                    )
                )
            # Top wall
            if abs(room.y + room.height - y1) > 0.1:
                walls.append(
                    WallSpec(
                        x1=room.x,
                        y1=room.y + room.height,
                        x2=room.x + room.width,
                        y2=room.y + room.height,
                        thickness=t * 0.7,
                        is_exterior=False,
                        floor=floor,
                    )
                )

        return walls

    def _generate_pillars(
        self, rooms: List[RoomSpec], floor: int, requested_pillars: Optional[int] = None
    ) -> List[PillarSpec]:
        """Places structural support columns at corners and intermediate span points."""
        pillars: List[PillarSpec] = []
        corner_coords = set()

        for room in rooms:
            corner_coords.add((round(room.x, 2), round(room.y, 2)))
            corner_coords.add((round(room.x + room.width, 2), round(room.y, 2)))
            corner_coords.add((round(room.x, 2), round(room.y + room.height, 2)))
            corner_coords.add((round(room.x + room.width, 2), round(room.y + room.height, 2)))

        sorted_coords = sorted(list(corner_coords))
        shape = "cylindrical" if self.style in [ArchitecturalStyle.LUXURY_VILLA, ArchitecturalStyle.CLASSIC] else "rectangular"

        p_idx = 1
        for px, py in sorted_coords:
            pillars.append(
                PillarSpec(
                    id=f"P{floor}_{p_idx}",
                    x=px,
                    y=py,
                    width=0.4,
                    height=0.4,
                    shape=shape,
                    floor=floor,
                )
            )
            p_idx += 1

        return pillars

    def _generate_beams(
        self, pillars: List[PillarSpec], floor: int, requested_beams: Optional[int] = None
    ) -> List[BeamSpec]:
        """Connects adjacent pillar columns with load-bearing structural beams."""
        beams: List[BeamSpec] = []
        b_idx = 1

        # Group pillars by X and Y coordinates to form continuous grid beams
        xs = sorted(list(set(p.x for p in pillars)))
        ys = sorted(list(set(p.y for p in pillars)))

        # Horizontal Beams
        for py in ys:
            row_pillars = sorted([p for p in pillars if abs(p.y - py) < 0.01], key=lambda p: p.x)
            for i in range(len(row_pillars) - 1):
                p1, p2 = row_pillars[i], row_pillars[i + 1]
                beams.append(
                    BeamSpec(
                        id=f"BH{floor}_{b_idx}",
                        x1=p1.x,
                        y1=p1.y,
                        x2=p2.x,
                        y2=p2.y,
                        width=0.3,
                        depth=0.4,
                        floor=floor,
                    )
                )
                b_idx += 1

        # Vertical Beams
        for px in xs:
            col_pillars = sorted([p for p in pillars if abs(p.x - px) < 0.01], key=lambda p: p.y)
            for i in range(len(col_pillars) - 1):
                p1, p2 = col_pillars[i], col_pillars[i + 1]
                beams.append(
                    BeamSpec(
                        id=f"BV{floor}_{b_idx}",
                        x1=p1.x,
                        y1=p1.y,
                        x2=p2.x,
                        y2=p2.y,
                        width=0.3,
                        depth=0.4,
                        floor=floor,
                    )
                )
                b_idx += 1

        return beams

    def _generate_openings(
        self, rooms: List[RoomSpec], walls: List[WallSpec], floor: int
    ) -> Tuple[List[DoorSpec], List[WindowSpec]]:
        """Generates functional doors and exterior windows with proper architectural types."""
        doors: List[DoorSpec] = []
        windows: List[WindowSpec] = []
        x0 = self.plot.margin
        y0 = self.plot.margin
        x1 = self.plot.length - self.plot.margin
        y1 = self.plot.width - self.plot.margin

        d_idx = 1
        w_idx = 1

        for room in rooms:
            # Main entrance door for Living Room on Floor 1
            if floor == 1 and ("living" in room.name.lower() or "hall" in room.name.lower()):
                doors.append(
                    DoorSpec(
                        id=f"D{floor}_{d_idx}",
                        x=round(room.x + room.width / 2, 2),
                        y=round(y0, 2),
                        width=1.6,  # Grand Double Entrance Door
                        orientation="horizontal",
                        swing=1,
                        door_type="double",
                        floor=floor,
                    )
                )
                d_idx += 1
            elif "balcony" in room.name.lower() or "patio" in room.name.lower():
                # Sliding Glass Patio Door
                doors.append(
                    DoorSpec(
                        id=f"D{floor}_{d_idx}",
                        x=round(room.x + room.width / 2, 2),
                        y=round(room.y, 2),
                        width=2.0,
                        orientation="horizontal",
                        swing=1,
                        door_type="sliding",
                        floor=floor,
                    )
                )
                d_idx += 1
            else:
                # Standard Interior Single Door
                doors.append(
                    DoorSpec(
                        id=f"D{floor}_{d_idx}",
                        x=round(room.x + min(0.8, room.width * 0.3), 2),
                        y=round(room.y, 2),
                        width=0.9,
                        orientation="horizontal",
                        swing=1,
                        door_type="single",
                        floor=floor,
                    )
                )
                d_idx += 1

            # Windows on exterior facets
            if abs(room.y - y0) < 0.1:  # South exterior
                windows.append(
                    WindowSpec(
                        id=f"W{floor}_{w_idx}",
                        x=round(room.x + room.width * 0.7, 2),
                        y=round(y0, 2),
                        width=1.5,
                        orientation="horizontal",
                        window_type="sliding" if "living" in room.name.lower() else "standard",
                        floor=floor,
                    )
                )
                w_idx += 1
            if abs(room.y + room.height - y1) < 0.1:  # North exterior
                windows.append(
                    WindowSpec(
                        id=f"W{floor}_{w_idx}",
                        x=round(room.x + room.width * 0.5, 2),
                        y=round(y1, 2),
                        width=1.4,
                        orientation="horizontal",
                        window_type="standard",
                        floor=floor,
                    )
                )
                w_idx += 1
            if abs(room.x - x0) < 0.1:  # West exterior
                windows.append(
                    WindowSpec(
                        id=f"W{floor}_{w_idx}",
                        x=round(x0, 2),
                        y=round(room.y + room.height / 2, 2),
                        width=1.2,
                        orientation="vertical",
                        window_type="standard",
                        floor=floor,
                    )
                )
                w_idx += 1
            if abs(room.x + room.width - x1) < 0.1:  # East exterior
                windows.append(
                    WindowSpec(
                        id=f"W{floor}_{w_idx}",
                        x=round(x1, 2),
                        y=round(room.y + room.height / 2, 2),
                        width=1.2,
                        orientation="vertical",
                        window_type="standard",
                        floor=floor,
                    )
                )
                w_idx += 1

        return doors, windows

    def _generate_stairs(self, rooms: List[RoomSpec], floor: int) -> List[StairSpec]:
        """Generates architectural staircases for multi-story floor transitions or main access."""
        stairs: List[StairSpec] = []
        if not rooms:
            return stairs

        # Select room for staircase (prefer Living Room or Hallway)
        target_room = rooms[0]
        for r in rooms:
            if any(k in r.name.lower() for k in ["living", "hall", "foyer", "lounge"]):
                target_room = r
                break

        stair_w = 1.2
        stair_l = min(3.2, target_room.height * 0.7)
        sx = target_room.x + target_room.width - stair_w - 0.3
        sy = target_room.y + 0.5

        stair_dir = "up" if floor < self.plot.num_floors else "down"

        stairs.append(
            StairSpec(
                id=f"ST_{floor}_1",
                x=round(sx, 2),
                y=round(sy, 2),
                width=stair_w,
                length=stair_l,
                orientation="vertical",
                stair_type="u-shaped" if self.style in [ArchitecturalStyle.LUXURY_VILLA, ArchitecturalStyle.CLASSIC] else "straight",
                direction=stair_dir,
                num_steps=16,
                floor=floor,
            )
        )
        return stairs

    def _generate_fixtures(self, rooms: List[RoomSpec], floor: int) -> List[FixtureSpec]:
        """Generates architectural furniture & plumbing fixtures for each room."""
        fixtures: List[FixtureSpec] = []
        f_idx = 1

        for room in rooms:
            r_type = room.room_type.lower()
            rx, ry, rw, rh = room.x, room.y, room.width, room.height

            if "bathroom" in r_type:
                # Toilet (WC)
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="toilet",
                        name="WC Toilet",
                        x=round(rx + 0.5, 2),
                        y=round(ry + 0.5, 2),
                        width=0.5,
                        height=0.7,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1
                # Washbasin Vanity
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="sink",
                        name="Washbasin Vanity",
                        x=round(rx + rw - 0.6, 2),
                        y=round(ry + 0.5, 2),
                        width=0.7,
                        height=0.5,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1
                # Shower Box / Bathtub
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="shower",
                        name="Shower Enclosure",
                        x=round(rx + rw - 0.75, 2),
                        y=round(ry + rh - 0.75, 2),
                        width=1.1,
                        height=1.1,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1

            elif "kitchen" in r_type:
                # Kitchen Countertop
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="kitchen_counter",
                        name="Kitchen Countertop",
                        x=round(rx + rw / 2, 2),
                        y=round(ry + rh - 0.35, 2),
                        width=min(rw - 0.6, 3.5),
                        height=0.6,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1
                # Kitchen Sink
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="sink",
                        name="Double Sink",
                        x=round(rx + 0.9, 2),
                        y=round(ry + rh - 0.35, 2),
                        width=0.8,
                        height=0.5,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1
                # Stove / Cooktop
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="stove",
                        name="4-Burner Stove",
                        x=round(rx + rw - 1.0, 2),
                        y=round(ry + rh - 0.35, 2),
                        width=0.8,
                        height=0.55,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1

            elif "bedroom" in r_type:
                # Bed with Pillows
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="bed",
                        name="King/Queen Bed",
                        x=round(rx + rw / 2, 2),
                        y=round(ry + rh - 1.2, 2),
                        width=1.8,
                        height=2.0,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1
                # Wardrobe Closet
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="wardrobe",
                        name="Wardrobe Closet",
                        x=round(rx + 0.4, 2),
                        y=round(ry + rh / 2, 2),
                        width=0.6,
                        height=min(1.8, rh - 1.0),
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1

            elif "living" in r_type or "lounge" in r_type:
                # Sofa Set
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="sofa",
                        name="3-Seater Sofa",
                        x=round(rx + rw / 2, 2),
                        y=round(ry + 1.0, 2),
                        width=2.2,
                        height=0.9,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1

            elif "dining" in r_type:
                # Dining Table
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="dining_table",
                        name="6-Seater Dining Set",
                        x=round(rx + rw / 2, 2),
                        y=round(ry + rh / 2, 2),
                        width=1.8,
                        height=1.0,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1

            elif "gym" in r_type:
                # Treadmill & Workout Bench
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="gym_equipment",
                        name="Treadmill & Workout Station",
                        x=round(rx + rw / 2, 2),
                        y=round(ry + rh / 2, 2),
                        width=1.8,
                        height=1.2,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1

            elif "theater" in r_type or "cinema" in r_type:
                # Recliner Seating Row
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="sofa",
                        name="Theater Recliner Seats",
                        x=round(rx + rw / 2, 2),
                        y=round(ry + rh / 2, 2),
                        width=min(rw - 0.8, 2.8),
                        height=1.0,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1

            elif "office" in r_type or "study" in r_type:
                # Executive Desk
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="wardrobe",
                        name="Executive Desk & Shelving",
                        x=round(rx + rw / 2, 2),
                        y=round(ry + rh / 2, 2),
                        width=1.6,
                        height=0.8,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1

            elif "laundry" in r_type:
                # Washer & Dryer
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="sink",
                        name="Washer & Dryer Units",
                        x=round(rx + rw / 2, 2),
                        y=round(ry + rh / 2, 2),
                        width=1.4,
                        height=0.7,
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1

            elif "garage" in r_type:
                # Vehicle Parking Bay
                fixtures.append(
                    FixtureSpec(
                        id=f"FIX_{floor}_{f_idx}",
                        fixture_type="wardrobe",
                        name="Vehicle Bay",
                        x=round(rx + rw / 2, 2),
                        y=round(ry + rh / 2, 2),
                        width=min(rw - 0.8, 2.4),
                        height=min(rh - 0.8, 4.5),
                        rotation=0,
                        floor=floor,
                    )
                )
                f_idx += 1

        return fixtures


    def _generate_axis_grid(self, pillars: List[PillarSpec]) -> List[AxisGridSpec]:
        """Generates standard architectural axis grid lines (1,2,3... and A,B,C...)."""
        grid_lines: List[AxisGridSpec] = []
        if not pillars:
            return grid_lines

        xs = sorted(list(set(round(p.x, 2) for p in pillars)))
        ys = sorted(list(set(round(p.y, 2) for p in pillars)))

        # X-Axis Lines (Labeled 1, 2, 3...)
        for idx, x in enumerate(xs):
            grid_lines.append(AxisGridSpec(label=str(idx + 1), position=x, axis_type="x"))

        # Y-Axis Lines (Labeled A, B, C...)
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for idx, y in enumerate(ys):
            lbl = letters[idx] if idx < len(letters) else f"Y{idx+1}"
            grid_lines.append(AxisGridSpec(label=lbl, position=y, axis_type="y"))

        return grid_lines

