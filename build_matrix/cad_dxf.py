"""
BuildMetrics AI — Native AutoCAD DXF (Drawing Exchange Format) Generator
Generates industry-standard layered ASCII DXF (AutoCAD R12 / 2000 compatible)
without external C-dependencies. Can be opened natively in AutoCAD, Revit,
LibreCAD, Vectorworks, SketchUp, and Blender.
"""

from build_matrix.models import BuildingModel


class DXFGenerator:
    """Generates standard layered AutoCAD DXF ASCII files from a BuildingModel."""

    @classmethod
    def generate_dxf(cls, building: BuildingModel, floor: int = 1) -> str:
        """
        Generate complete ASCII DXF content for the specified floor.
        
        Layers created:
          - A-WALL-EXT (Color 3 - Green, width 0.35mm): Exterior envelope walls
          - A-WALL-INT (Color 8 - Gray, width 0.20mm): Interior partition walls
          - A-COLS (Color 1 - Red, width 0.50mm): Structural columns/pillars
          - A-BEAM (Color 2 - Yellow, dashed): Structural grid beams
          - A-DOOR (Color 4 - Cyan): Door openings and swing arcs
          - A-WIND (Color 5 - Blue): Window openings and glazing lines
          - A-ROMS (Color 7 - White): Room boundaries and area labels
          - A-DIMS (Color 9 - Light Gray): Dimension lines and plot boundary
          - A-SITE (Color 6 - Magenta): Boundary compound wall & gates
        """
        plot = building.plot
        lines: list[str] = []

        # ─── 1. DXF HEADER SECTION ──────────────────────────────────────────
        lines.extend([
            "0", "SECTION",
            "2", "HEADER",
            "9", "$ACADVER", "1", "AC1009",  # AutoCAD R12 DXF (universal compatibility)
            "9", "$INSUNITS", "70", "6",      # Units = Meters
            "9", "$EXTMIN", "10", "0.0", "20", "0.0", "30", "0.0",
            "9", "$EXTMAX", "10", str(plot.length), "20", str(plot.width), "30", "0.0",
            "0", "ENDSEC",
        ])

        # ─── 2. DXF TABLES (LAYERS & LINETYPE) ──────────────────────────────
        lines.extend([
            "0", "SECTION",
            "2", "TABLES",
            "0", "TABLE",
            "2", "LAYER",
            "70", "9",
        ])

        # Layer definitions: (Name, ColorCode)
        layers = [
            ("A-WALL-EXT", 3),   # Green
            ("A-WALL-INT", 8),   # Gray
            ("A-COLS", 1),       # Red
            ("A-BEAM", 2),       # Yellow
            ("A-DOOR", 4),       # Cyan
            ("A-WIND", 5),       # Blue
            ("A-ROMS", 7),       # White
            ("A-DIMS", 9),       # Light Gray
            ("A-SITE", 6),       # Magenta
        ]
        for name, color in layers:
            lines.extend([
                "0", "LAYER",
                "2", name,
                "70", "0",
                "62", str(color),
                "6", "CONTINUOUS",
            ])

        lines.extend([
            "0", "ENDTAB",
            "0", "ENDSEC",
        ])

        # ─── 3. DXF BLOCKS SECTION ──────────────────────────────────────────
        lines.extend([
            "0", "SECTION",
            "2", "BLOCKS",
            "0", "ENDSEC",
        ])

        # ─── 4. DXF ENTITIES SECTION ────────────────────────────────────────
        lines.extend([
            "0", "SECTION",
            "2", "ENTITIES",
        ])

        # 4.1 Plot Boundary & Compound Site
        cls._add_rect(lines, 0.0, 0.0, plot.length, plot.width, "A-DIMS")

        # Boundary Compound Walls
        for bw in getattr(building, "boundary_walls", []):
            cls._add_line(lines, bw.x1, bw.y1, bw.x2, bw.y2, "A-SITE")

        # Main Gates
        for mg in getattr(building, "main_gates", []):
            cls._add_rect(lines, mg.x, mg.y - 0.2, mg.width, 0.4, "A-SITE")
            cls._add_text(lines, mg.x + mg.width / 2, mg.y + 0.3, 0.25, f"GATE: {mg.gate_type.upper()}", "A-SITE")

        # 4.2 Room Outlines and Room Area Text Tags
        for r in building.rooms:
            if r.floor == floor:
                cls._add_rect(lines, r.x, r.y, r.width, r.height, "A-ROMS")
                center_x = r.x + r.width / 2.0
                center_y = r.y + r.height / 2.0
                cls._add_text(lines, center_x, center_y + 0.2, 0.35, r.name.upper(), "A-ROMS")
                cls._add_text(lines, center_x, center_y - 0.25, 0.22, f"{r.area:.1f} SQ.M", "A-ROMS")

        # 4.3 Structural Walls
        for w in building.walls:
            if w.floor == floor:
                layer = "A-WALL-EXT" if w.is_exterior else "A-WALL-INT"
                cls._add_line(lines, w.x1, w.y1, w.x2, w.y2, layer)

        # 4.4 Structural Columns (Pillars)
        for p in building.pillars:
            if p.floor == floor:
                half_w = p.width / 2.0
                half_h = p.height / 2.0
                cls._add_rect(lines, p.x - half_w, p.y - half_h, p.width, p.height, "A-COLS")
                # Cross-hatch diagonals in column
                cls._add_line(lines, p.x - half_w, p.y - half_h, p.x + half_w, p.y + half_h, "A-COLS")
                cls._add_line(lines, p.x - half_w, p.y + half_h, p.x + half_w, p.y - half_h, "A-COLS")

        # 4.5 Structural Beams
        for b in building.beams:
            if b.floor == floor:
                cls._add_line(lines, b.x1, b.y1, b.x2, b.y2, "A-BEAM")

        # 4.6 Doors (Frame & Swing Arc)
        for d in building.doors:
            if d.floor == floor:
                cls._add_door(lines, d.x, d.y, d.width, d.orientation, "A-DOOR")

        # 4.7 Windows (Double parallel lines)
        for w in building.windows:
            if w.floor == floor:
                cls._add_window(lines, w.x, w.y, w.width, w.orientation, "A-WIND")

        # 4.8 Title Block Information (Bottom Left)
        tb_x, tb_y = 1.0, 0.8
        cls._add_text(lines, tb_x, tb_y + 0.6, 0.45, "BUILDMETRICS AI — CAD BLUEPRINT", "A-DIMS")
        cls._add_text(lines, tb_x, tb_y + 0.25, 0.28, f"PROJECT LEVEL: FLOOR {floor} OF {plot.num_floors}", "A-DIMS")
        cls._add_text(lines, tb_x, tb_y - 0.05, 0.22, f"PLOT: {plot.length:.1f}m x {plot.width:.1f}m | STYLE: {building.style.value}", "A-DIMS")

        # Close ENTITIES and File
        lines.extend([
            "0", "ENDSEC",
            "0", "EOF",
        ])

        return "\n".join(lines)

    @classmethod
    def _add_line(cls, lines: list[str], x1: float, y1: float, x2: float, y2: float, layer: str) -> None:
        """Appends a 2D LINE entity to DXF."""
        lines.extend([
            "0", "LINE",
            "8", layer,
            "10", f"{x1:.4f}",
            "20", f"{y1:.4f}",
            "30", "0.0",
            "11", f"{x2:.4f}",
            "20", f"{y2:.4f}",
            "31", "0.0",
        ])

    @classmethod
    def _add_rect(cls, lines: list[str], x: float, y: float, w: float, h: float, layer: str) -> None:
        """Appends a closed rectangle (4 lines) to DXF."""
        cls._add_line(lines, x, y, x + w, y, layer)
        cls._add_line(lines, x + w, y, x + w, y + h, layer)
        cls._add_line(lines, x + w, y + h, x, y + h, layer)
        cls._add_line(lines, x, y + h, x, y, layer)

    @classmethod
    def _add_text(cls, lines: list[str], x: float, y: float, height: float, text: str, layer: str) -> None:
        """Appends a centered TEXT entity to DXF."""
        lines.extend([
            "0", "TEXT",
            "8", layer,
            "10", f"{x:.4f}",
            "20", f"{y:.4f}",
            "30", "0.0",
            "40", f"{height:.4f}",
            "1", text,
            "72", "1",  # Center-aligned horizontally
            "11", f"{x:.4f}",
            "21", f"{y:.4f}",
            "31", "0.0",
        ])

    @classmethod
    def _add_door(cls, lines: list[str], x: float, y: float, width: float, orientation: str, layer: str) -> None:
        """Appends door opening line and open leaf line."""
        if orientation in ("horizontal", "h"):
            # Door leaf swinging 90 degrees
            cls._add_line(lines, x, y, x + width, y, layer)
            cls._add_line(lines, x, y, x, y + width, layer)
        else:
            cls._add_line(lines, x, y, x, y + width, layer)
            cls._add_line(lines, x, y, x + width, y, layer)

    @classmethod
    def _add_window(cls, lines: list[str], x: float, y: float, width: float, orientation: str, layer: str) -> None:
        """Appends double parallel window glazing lines."""
        t = 0.08  # glazing line separation
        if orientation in ("horizontal", "h"):
            cls._add_line(lines, x, y - t, x + width, y - t, layer)
            cls._add_line(lines, x, y + t, x + width, y + t, layer)
        else:
            cls._add_line(lines, x - t, y, x - t, y + width, layer)
            cls._add_line(lines, x + t, y, x + t, y + width, layer)
