"""
BUILD-MATRIX.ai 2D Blueprint Renderer
Draws crisp 2D architectural blueprints complete with wall hatches, pillars, beams, doors, windows, dimensions, compass, and title blocks.
"""

import io
import math

import matplotlib
import numpy as np

matplotlib.use('Agg')
from typing import Any

import cv2
import matplotlib.pyplot as plt
from matplotlib import patches

from .labeling import LabelingManager
from .models import Blueprint2DConfig, BuildingModel


class Blueprint2DRenderer:
    """High-resolution 2D architectural blueprint vector/raster drawing engine."""

    import typing
    THEME_COLORS: typing.ClassVar[dict] = {
        "Classic Blueprint": {
            "bg": "#0D47A1",  # Deep Blueprint Blue
            "grid": "#1976D2",
            "wall_ext": "#FFFFFF",
            "wall_int": "#E0E0E0",
            "pillar": "#FFD54F",
            "beam": "#FF8A65",
            "door": "#80DEEA",
            "window": "#4FC3F7",
            "text": "#FFFFFF",
            "dim": "#80CBC4",
            "title_bg": "#0A3B85",
            "hatch": "#1565C0",
            "garden": "#1565C0",
            "gate": "#FFD54F",
            "pathway": "#80CBC4",
        },
        "Paper White": {
            "bg": "#FFFFFF",
            "grid": "#F0F0F0",
            "wall_ext": "#212121",
            "wall_int": "#424242",
            "pillar": "#D32F2F",
            "beam": "#E65100",
            "door": "#0288D1",
            "window": "#0097A7",
            "text": "#1A237E",
            "dim": "#37474F",
            "title_bg": "#F5F5F5",
            "hatch": "#E0E0E0",
            "garden": "#C8E6C9",
            "gate": "#D32F2F",
            "pathway": "#B0BEC5",
        },
        "Architectural Dark": {
            "bg": "#1E1E1E",
            "grid": "#2D2D2D",
            "wall_ext": "#00E676",
            "wall_int": "#B9F6CA",
            "pillar": "#FF5252",
            "beam": "#FFAB40",
            "door": "#40C4FF",
            "window": "#18FFFF",
            "text": "#FFFFFF",
            "dim": "#B0BEC5",
            "title_bg": "#252526",
            "hatch": "#333333",
            "garden": "#1B5E20",
            "gate": "#FFAB40",
            "pathway": "#546E7A",
        },
        "Japandi Earth": {
            "bg": "#F7F5F0",
            "grid": "#EAE5D9",
            "wall_ext": "#3D3835",
            "wall_int": "#655E59",
            "pillar": "#A65B32",
            "beam": "#C89D7C",
            "door": "#5C7C66",
            "window": "#83A090",
            "text": "#2C2623",
            "dim": "#7D7571",
            "title_bg": "#EFECE6",
            "hatch": "#DDD8CE",
            "garden": "#C5D8C4",
            "gate": "#A65B32",
            "pathway": "#C89D7C",
        },
        "Scandinavian Light": {
            "bg": "#FAFAFA",
            "grid": "#E0E0E0",
            "wall_ext": "#263238",
            "wall_int": "#455A64",
            "pillar": "#D84315",
            "beam": "#EF6C00",
            "door": "#0277BD",
            "window": "#00838F",
            "text": "#1A237E",
            "dim": "#546E7A",
            "title_bg": "#ECEFF1",
            "hatch": "#CFD8DC",
            "garden": "#DCEDC8",
            "gate": "#D84315",
            "pathway": "#B0BEC5",
        },
        "Tropical Emerald": {
            "bg": "#F4F9F5",
            "grid": "#E1EFE4",
            "wall_ext": "#1B4332",
            "wall_int": "#2D6A4F",
            "pillar": "#D97706",
            "beam": "#B45309",
            "door": "#059669",
            "window": "#0284C7",
            "text": "#064E3B",
            "dim": "#4B5563",
            "title_bg": "#D8F3DC",
            "hatch": "#B7E4C7",
            "garden": "#A7F3D0",
            "gate": "#D97706",
            "pathway": "#6EE7B7",
        },
    }


    def __init__(self, config: Blueprint2DConfig | None = None):
        self.config = config or Blueprint2DConfig()

    def render(self, building: BuildingModel, floor: int = 1) -> plt.Figure:
        """Renders the 2D blueprint for the specified floor as a Matplotlib Figure."""
        theme = self.THEME_COLORS.get(self.config.theme, self.THEME_COLORS["Classic Blueprint"])
        plot = building.plot

        # Create Figure & Axis
        fig, ax = plt.subplots(figsize=(12, 10), dpi=self.config.dpi)
        fig.patch.set_facecolor(theme["bg"])
        ax.set_facecolor(theme["bg"])

        # Grid setup
        margin_offset = 3.5
        ax.set_xlim(-margin_offset, plot.length + margin_offset)
        ax.set_ylim(-margin_offset - 2.0, plot.width + margin_offset)
        ax.set_aspect("equal")

        if self.config.show_grid:
            ax.grid(True, which="both", color=theme["grid"], linestyle=":", linewidth=0.5, alpha=0.7)
            ax.set_xticks(np.arange(0, plot.length + 1, self.config.grid_spacing))
            ax.set_yticks(np.arange(0, plot.width + 1, self.config.grid_spacing))
            ax.tick_params(colors=theme["text"], labelsize=8)

        # 1. Draw Axis Grid Lines & Bubbles
        if self.config.show_axis_grid and building.axis_grids:
            self._draw_axis_grid(ax, building, theme)

        # 2. Draw Plot Boundary & Boundary Wall
        plot_rect = patches.Rectangle(
            (0, 0),
            plot.length,
            plot.width,
            linewidth=0.75,
            edgecolor=theme["dim"],
            facecolor="none",
            linestyle="--",
        )
        ax.add_patch(plot_rect)

        if self.config.show_boundary_wall and getattr(building, "boundary_walls", None):
            self._draw_boundary_walls(ax, building, theme)

        # 2b. Draw Garden & Landscape Area
        if self.config.show_garden and getattr(building, "gardens", None):
            self._draw_garden_area(ax, building, theme)

        # 3. Draw Rooms
        floor_rooms = [r for r in building.rooms if r.floor == floor]
        for room in floor_rooms:
            room_rect = patches.Rectangle(
                (room.x, room.y),
                room.width,
                room.height,
                facecolor=room.color if self.config.theme == "Paper White" else "none",
                alpha=0.25 if self.config.theme == "Paper White" else 0.0,
                edgecolor="none",
            )
            ax.add_patch(room_rect)

            # Room Label
            if self.config.show_room_labels:
                ax.text(
                    room.x + room.width / 2,
                    room.y + room.height / 2,
                    f"{room.name}\n{room.width:.2f}m x {room.height:.2f}m\n({room.area:.1f} m²)",
                    color=theme["text"],
                    ha="center",
                    va="center",
                    fontsize=8,
                    fontweight="bold",
                    bbox={'boxstyle': "round,pad=0.3", 'facecolor': theme["bg"], 'edgecolor': theme["dim"], 'alpha': 0.75},
                    zorder=10,
                )

        # 4. Draw Walls (With Hatching & Cutouts)
        floor_walls = [w for w in building.walls if w.floor == floor]
        for wall in floor_walls:
            lw = 3.0 if wall.is_exterior else 2.5
            color = theme["wall_ext"] if wall.is_exterior else theme["wall_int"]
            ax.plot([wall.x1, wall.x2], [wall.y1, wall.y2], color=color, linewidth=lw, solid_capstyle="butt", zorder=3)
            # Exterior Wall Hatching
            if wall.is_exterior and self.config.show_hatches and self.config.theme == "Paper White":
                dx = wall.x2 - wall.x1
                dy = wall.y2 - wall.y1
                w_len = math.hypot(dx, dy)
                if w_len > 0.5:
                    midx, midy = (wall.x1 + wall.x2) / 2, (wall.y1 + wall.y2) / 2
                    ang = math.degrees(math.atan2(dy, dx))
                    rect_h = patches.Rectangle(
                        (midx - w_len / 2, midy - wall.thickness / 2),
                        w_len,
                        wall.thickness,
                        angle=ang,
                        rotation_point='center',
                        facecolor="none",
                        edgecolor=theme["hatch"],
                        hatch="///",
                        linewidth=0.5,
                        zorder=2,
                    )
                    ax.add_patch(rect_h)

        # 5. Draw Architectural Fixtures & Furniture CAD Symbols
        if self.config.show_fixtures:
            floor_fixtures = [f for f in building.fixtures if f.floor == floor]
            for fix in floor_fixtures:
                self._draw_fixture(ax, fix, theme)

        # 6. Draw Staircases
        if self.config.show_stairs:
            floor_stairs = [s for s in building.stairs if s.floor == floor]
            for stair in floor_stairs:
                self._draw_staircase(ax, stair, theme)

        # 7. Draw Structural Beams
        if self.config.show_beams:
            floor_beams = [b for b in building.beams if b.floor == floor]
            for beam in floor_beams:
                ax.plot(
                    [beam.x1, beam.x2],
                    [beam.y1, beam.y2],
                    color=theme["beam"], linestyle="--", linewidth=2.5,
                    alpha=0.8,
                    zorder=4,
                )
                mid_x = (beam.x1 + beam.x2) / 2
                mid_y = (beam.y1 + beam.y2) / 2
                ax.text(mid_x, mid_y, beam.id, color=theme["beam"], fontsize=6, ha="center", va="center", zorder=10)

        # 8. Draw Structural Pillars
        if self.config.show_pillars:
            floor_pillars = [p for p in building.pillars if p.floor == floor]
            for p in floor_pillars:
                if p.shape == "cylindrical":
                    pillar_patch = patches.Circle(
                        (p.x, p.y),
                        radius=p.width / 2,
                        facecolor=theme["pillar"],
                        edgecolor=theme["wall_ext"],
                        linewidth=1.0,
                        zorder=6,
                    )
                else:
                    pillar_patch = patches.Rectangle(
                        (p.x - p.width / 2, p.y - p.height / 2),
                        p.width,
                        p.height,
                        facecolor=theme["pillar"],
                        edgecolor=theme["wall_ext"],
                        hatch="//",
                        linewidth=1.0,
                        zorder=6,
                    )
                ax.add_patch(pillar_patch)
                ax.text(p.x, p.y + 0.3, p.id, color=theme["pillar"], fontsize=6, fontweight="bold", ha="center", zorder=10)

        # 9. Draw Doors
        floor_doors = [d for d in building.doors if d.floor == floor]
        for door in floor_doors:
            self._draw_door(ax, door, theme)

        # 10. Draw Windows
        floor_windows = [w for w in building.windows if w.floor == floor]
        for win in floor_windows:
            self._draw_window(ax, win, theme)

        # 10b. Draw Main Compound Gates
        if self.config.show_main_gate and getattr(building, "main_gates", None):
            for gate in building.main_gates:
                self._draw_main_gate(ax, gate, theme, building)

        # 11. Draw Dimension Callouts & Markers
        if self.config.show_dimensions:
            self._draw_dimension_line(ax, 0, plot.width + 1.2, plot.length, plot.width + 1.2, f"{plot.length:.2f} m", theme)
            self._draw_dimension_line(ax, plot.length + 1.2, 0, plot.length + 1.2, plot.width, f"{plot.width:.2f} m", theme, vertical=True)

        # 12. Draw Compass Rose (North Arrow)
        if self.config.show_compass:
            self._draw_compass_rose(ax, plot.length + 2.0, plot.width + 1.5, theme)

        # 12b. Draw Compliance Annotations
        for ann in building.annotations:
            if ann.category == "compliance_tag":
                color = "#388E3C" if ann.style_props.get("color") == "green" else "#D32F2F"
                ax.text(
                    ann.x,
                    ann.y,
                    ann.text,
                    color="white",
                    ha="center",
                    va="center",
                    fontsize=ann.style_props.get("fontsize", 6),
                    fontweight="bold",
                    bbox={'boxstyle': "round,pad=0.2", 'facecolor': color, 'edgecolor': "none", 'alpha': 0.9},
                    zorder=25,
                )

        # 13. Draw Architectural Title Block & Legend
        if self.config.show_title_block:
            self._draw_title_block(ax, building, floor, theme)

        ax.set_title(
            f"BUILD-MATRIX.ai — 2D Architectural Floor Plan ({building.style.value}) — Floor {floor}",
            color=theme["text"],
            fontsize=12,
            fontweight="bold",
            pad=15,
        )

        plt.tight_layout()
        return fig

    def _draw_axis_grid(self, ax: plt.Axes, building: BuildingModel, theme: dict[str, str]) -> None:
        """Draws architectural structural axis grid lines and callout bubbles."""
        plot = building.plot
        for grid in building.axis_grids:
            if grid.axis_type == "x":
                # Vertical grid line
                ax.plot([grid.position, grid.position], [-0.5, plot.width + 0.5], color=theme["dim"], linestyle="--", linewidth=0.7, alpha=0.6)
                # Top bubble
                bubble = patches.Circle((grid.position, plot.width + 0.6), radius=0.35, facecolor=theme["title_bg"], edgecolor=theme["dim"], lw=1.0, zorder=8)
                ax.add_patch(bubble)
                ax.text(grid.position, plot.width + 0.6, grid.label, color=theme["text"], fontsize=8, fontweight="bold", ha="center", va="center", zorder=9)
            else:
                # Horizontal grid line
                ax.plot([-0.5, plot.length + 0.5], [grid.position, grid.position], color=theme["dim"], linestyle="--", linewidth=0.7, alpha=0.6)
                # Left bubble
                bubble = patches.Circle((-0.6, grid.position), radius=0.35, facecolor=theme["title_bg"], edgecolor=theme["dim"], lw=1.0, zorder=8)
                ax.add_patch(bubble)
                ax.text(-0.6, grid.position, grid.label, color=theme["text"], fontsize=8, fontweight="bold", ha="center", va="center", zorder=9)

    def _draw_staircase(self, ax: plt.Axes, stair: Any, theme: dict[str, str]) -> None:
        """Renders detailed 2D architectural staircase drawing with step treads, UP/DN arrow, and railing."""
        sx, sy, sw, sl = stair.x, stair.y, stair.width, stair.length
        # Stair boundary rectangle
        stair_rect = patches.Rectangle((sx, sy), sw, sl, facecolor="none", edgecolor=theme["text"], linewidth=1.2, zorder=5)
        ax.add_patch(stair_rect)

        # Draw step treads
        num_steps = stair.num_steps
        step_h = sl / (num_steps / 2 if stair.stair_type == "u-shaped" else num_steps)

        for i in range(1, int(num_steps / (2 if stair.stair_type == "u-shaped" else 1))):
            step_y = sy + i * step_h
            ax.plot([sx, sx + sw], [step_y, step_y], color=theme["text"], linewidth=0.8, linestyle="-", zorder=5)

        # Draw central divider for U-shaped stairs
        if stair.stair_type == "u-shaped":
            ax.plot([sx + sw / 2, sx + sw / 2], [sy, sy + sl], color=theme["text"], linewidth=1.0, zorder=5)

        # Draw Handrails
        ax.plot([sx + 0.05, sx + 0.05], [sy, sy + sl], color=theme["beam"], linewidth=1.5, zorder=6)
        ax.plot([sx + sw - 0.05, sx + sw - 0.05], [sy, sy + sl], color=theme["beam"], linewidth=1.5, zorder=6)

        # Direction Arrow (UP -> or DN ->)
        arr_x = sx + sw / 2
        ax.annotate(
            f"{stair.direction.upper()} ({stair.num_steps} R)",
            xy=(arr_x, sy + sl - 0.3),
            xytext=(arr_x, sy + 0.3),
            arrowprops={'facecolor': theme["door"], 'edgecolor': theme["door"], 'width': 1.5, 'headwidth': 6},
            color=theme["door"],
            fontsize=7,
            fontweight="bold",
            ha="center",
            zorder=7,
        )

    def _draw_fixture(self, ax: plt.Axes, fix: Any, theme: dict[str, str]) -> None:
        """Renders architect CAD symbols for furniture and plumbing fixtures."""
        fx, fy, fw, fh = fix.x, fix.y, fix.width, fix.height
        ftype = fix.fixture_type

        col = theme["dim"]

        if ftype == "toilet":
            # Tank rectangle + Bowl oval
            tank = patches.Rectangle((fx - fw / 2, fy + fh / 2 - 0.2), fw, 0.2, facecolor="none", edgecolor=col, linewidth=0.5, linestyle=":", zorder=4)
            bowl = patches.Ellipse((fx, fy - 0.1), fw * 0.9, fh * 0.7, facecolor="none", edgecolor=col, linewidth=0.5, linestyle=":", zorder=4)
            ax.add_patch(tank)
            ax.add_patch(bowl)

        elif ftype == "sink":
            # Counter rect + inner basin oval
            rect = patches.Rectangle((fx - fw / 2, fy - fh / 2), fw, fh, facecolor="none", edgecolor=col, linewidth=0.5, linestyle=":", zorder=4)
            basin = patches.Ellipse((fx, fy), fw * 0.7, fh * 0.7, facecolor="none", edgecolor=col, linewidth=0.8, zorder=4)
            ax.add_patch(rect)
            ax.add_patch(basin)

        elif ftype == "shower":
            # Shower enclosure box with diagonal cross
            box = patches.Rectangle((fx - fw / 2, fy - fh / 2), fw, fh, facecolor="none", edgecolor=col, linewidth=0.5, linestyle=":", zorder=4)
            ax.add_patch(box)
            ax.plot([fx - fw / 2, fx + fw / 2], [fy - fh / 2, fy + fh / 2], color=col, linewidth=0.5, linestyle=":", zorder=4)
            circle = patches.Circle((fx, fy), radius=0.1, facecolor="none", edgecolor=col, lw=0.5, linestyle=":", zorder=4)
            ax.add_patch(circle)

        elif ftype == "kitchen_counter":
            counter = patches.Rectangle((fx - fw / 2, fy - fh / 2), fw, fh, facecolor="none", edgecolor=col, linewidth=0.5, linestyle=":", zorder=4)
            ax.add_patch(counter)

        elif ftype == "stove":
            box = patches.Rectangle((fx - fw / 2, fy - fh / 2), fw, fh, facecolor="none", edgecolor=col, linewidth=0.5, linestyle=":", zorder=4)
            ax.add_patch(box)
            # 4 Burners
            r_b = min(fw, fh) * 0.18
            for dx in [-fw * 0.25, fw * 0.25]:
                for dy in [-fh * 0.25, fh * 0.25]:
                    burner = patches.Circle((fx + dx, fy + dy), radius=r_b, facecolor="none", edgecolor=col, lw=0.5, linestyle=":", zorder=4)
                    ax.add_patch(burner)

        elif ftype == "bed":
            # Frame rect + Pillows + Blanket fold
            frame = patches.Rectangle((fx - fw / 2, fy - fh / 2), fw, fh, facecolor="none", edgecolor=col, linewidth=0.5, linestyle=":", zorder=4)
            ax.add_patch(frame)
            # Pillows
            p1 = patches.Rectangle((fx - fw * 0.45, fy + fh * 0.25), fw * 0.4, fh * 0.2, facecolor="none", edgecolor=col, linewidth=0.8, zorder=4)
            p2 = patches.Rectangle((fx + fw * 0.05, fy + fh * 0.25), fw * 0.4, fh * 0.2, facecolor="none", edgecolor=col, linewidth=0.8, zorder=4)
            ax.add_patch(p1)
            ax.add_patch(p2)
            # Blanket fold line
            ax.plot([fx - fw / 2, fx + fw / 2], [fy - fh * 0.1, fy - fh * 0.1], color=col, linewidth=0.8, linestyle="--", zorder=4)

        elif ftype == "wardrobe":
            ward = patches.Rectangle((fx - fw / 2, fy - fh / 2), fw, fh, facecolor="none", edgecolor=col, linewidth=0.5, linestyle=":", zorder=4)
            ax.add_patch(ward)
            ax.plot([fx - fw / 2, fx + fw / 2], [fy - fh / 2, fy + fh / 2], color=col, linewidth=0.5, linestyle=":", zorder=4)

        elif ftype == "sofa":
            # Couch backrest + seat cushion
            sofa = patches.Rectangle((fx - fw / 2, fy - fh / 2), fw, fh, facecolor="none", edgecolor=col, linewidth=0.5, linestyle=":", zorder=4)
            back = patches.Rectangle((fx - fw / 2, fy + fh / 2 - 0.2), fw, 0.2, facecolor="none", edgecolor=col, linewidth=0.8, zorder=4)
            ax.add_patch(sofa)
            ax.add_patch(back)

        elif ftype == "dining_table":
            tbl = patches.Rectangle((fx - fw / 2, fy - fh / 2), fw, fh, facecolor="none", edgecolor=col, linewidth=0.5, linestyle=":", zorder=4)
            ax.add_patch(tbl)
            # Chairs around table
            c_w, c_h = 0.4, 0.4
            for cx in [fx - fw * 0.3, fx, fx + fw * 0.3]:
                c_top = patches.Rectangle((cx - c_w / 2, fy + fh / 2 + 0.05), c_w, c_h, facecolor="none", edgecolor=col, lw=0.5, linestyle=":", zorder=4)
                c_bot = patches.Rectangle((cx - c_w / 2, fy - fh / 2 - c_h - 0.05), c_w, c_h, facecolor="none", edgecolor=col, lw=0.5, linestyle=":", zorder=4)
                ax.add_patch(c_top)
                ax.add_patch(c_bot)

    def _draw_door(self, ax: plt.Axes, door: Any, theme: dict[str, str]) -> None:
        """Renders architectural doors with wall cutouts, swing arcs, double doors, and sliding doors."""
        dx, dy, dw = door.x, door.y, door.width
        swing = door.swing
        dtype = getattr(door, "door_type", "single")

        if door.orientation == "horizontal":
            # Wall cutout gap mask
            ax.plot([dx - dw / 2, dx + dw / 2], [dy, dy], color=theme["bg"], linewidth=5.0, zorder=6)

            if dtype == "double":
                # Double Entrance Door (two leaves, two 90° arcs)
                half_w = dw / 2
                ax.plot([dx - dw / 2, dx - dw / 2], [dy, dy + half_w * swing], color=theme["door"], linewidth=1.5, zorder=7)
                ax.plot([dx + dw / 2, dx + dw / 2], [dy, dy + half_w * swing], color=theme["door"], linewidth=1.5, zorder=7)
                arc1 = patches.Arc((dx - dw / 2, dy), width=2 * half_w, height=2 * half_w, angle=0, theta1=0 if swing > 0 else 270, theta2=90 if swing > 0 else 360, color=theme["door"], linestyle=":", linewidth=0.5, zorder=7)
                arc2 = patches.Arc((dx + dw / 2, dy), width=2 * half_w, height=2 * half_w, angle=0, theta1=90 if swing > 0 else 180, theta2=180 if swing > 0 else 270, color=theme["door"], linestyle=":", linewidth=0.5, zorder=7)
                ax.add_patch(arc1)
                ax.add_patch(arc2)

            elif dtype == "sliding":
                # Sliding Patio Door (overlapping double glass lines)
                ax.plot([dx - dw / 2, dx + 0.1], [dy + 0.05, dy + 0.05], color=theme["door"], linewidth=1.5, zorder=7)
                ax.plot([dx - 0.1, dx + dw / 2], [dy - 0.05, dy - 0.05], color=theme["door"], linewidth=1.5, zorder=7)
                ax.annotate("", xy=(dx + dw / 2 - 0.2, dy - 0.12), xytext=(dx + 0.2, dy - 0.12), arrowprops={'arrowstyle': "->", 'color': theme["door"], 'lw': 0.5}, zorder=7)

            else:
                # Single Swing Door
                ax.plot([dx - dw / 2, dx - dw / 2], [dy, dy + dw * swing], color=theme["door"], linewidth=1.5, zorder=7)
                arc = patches.Arc((dx - dw / 2, dy), width=2 * dw, height=2 * dw, angle=0, theta1=0 if swing > 0 else 270, theta2=90 if swing > 0 else 360, color=theme["door"], linestyle=":", linewidth=0.5, zorder=7)
                ax.add_patch(arc)
        else:
            # Vertical Door
            ax.plot([dx, dx], [dy - dw / 2, dy + dw / 2], color=theme["bg"], linewidth=5.0, zorder=6)
            ax.plot([dx, dx + dw * swing], [dy - dw / 2, dy - dw / 2], color=theme["door"], linewidth=1.5, zorder=7)
            arc = patches.Arc((dx, dy - dw / 2), width=2 * dw, height=2 * dw, angle=0, theta1=0, theta2=90, color=theme["door"], linestyle=":", linewidth=0.5, zorder=7)
            ax.add_patch(arc)

    def _draw_window(self, ax: plt.Axes, win: Any, theme: dict[str, str]) -> None:
        """Renders architectural windows with wall cutout gaps, double glass lines, and jambs."""
        wx, wy, ww = win.x, win.y, win.width

        if win.orientation == "horizontal":
            # Wall cutout gap mask
            ax.plot([wx - ww / 2, wx + ww / 2], [wy, wy], color=theme["bg"], linewidth=5.0, zorder=6)
            # Double Glass Pane Lines
            ax.plot([wx - ww / 2, wx + ww / 2], [wy - 0.08, wy - 0.08], color=theme["window"], linewidth=1.5, zorder=7)
            ax.plot([wx - ww / 2, wx + ww / 2], [wy + 0.08, wy + 0.08], color=theme["window"], linewidth=1.5, zorder=7)
            # Window Frame Jambs at ends
            ax.plot([wx - ww / 2, wx - ww / 2], [wy - 0.12, wy + 0.12], color=theme["window"], linewidth=1.5, zorder=7)
            ax.plot([wx + ww / 2, wx + ww / 2], [wy - 0.12, wy + 0.12], color=theme["window"], linewidth=1.5, zorder=7)
        else:
            ax.plot([wx, wx], [wy - ww / 2, wy + ww / 2], color=theme["bg"], linewidth=5.0, zorder=6)
            ax.plot([wx - 0.08, wx - 0.08], [wy - ww / 2, wy + ww / 2], color=theme["window"], linewidth=1.5, zorder=7)
            ax.plot([wx + 0.08, wx + 0.08], [wy - ww / 2, wy + ww / 2], color=theme["window"], linewidth=1.5, zorder=7)
            ax.plot([wx - 0.12, wx + 0.12], [wy - ww / 2, wy - ww / 2], color=theme["window"], linewidth=1.5, zorder=7)
            ax.plot([wx - 0.12, wx + 0.12], [wy + ww / 2, wy + ww / 2], color=theme["window"], linewidth=1.5, zorder=7)

    def _draw_dimension_line(

        self, ax: plt.Axes, x1: float, y1: float, x2: float, y2: float, label: str, theme: dict[str, str], vertical: bool = False
    ) -> None:
        """Draws dimension line with extension ticks and text label."""
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops={'arrowstyle': "<->", 'color': theme["dim"], 'lw': 0.5},
        )
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        rot = 90 if vertical else 0
        ax.text(
            mid_x,
            mid_y,
            label,
            color=theme["dim"],
            fontsize=8,
            fontweight="bold",
            ha="center",
            va="center",
            rotation=rot,
            bbox={'boxstyle': "square,pad=0.2", 'facecolor': theme["bg"], 'edgecolor': "none"},
        )

    def _draw_compass_rose(self, ax: plt.Axes, cx: float, cy: float, theme: dict[str, str]) -> None:
        """Draws North Compass Rose."""
        ax.annotate(
            "N",
            xy=(cx, cy + 0.8),
            xytext=(cx, cy - 0.2),
            arrowprops={'facecolor': theme["text"], 'edgecolor': theme["text"], 'width': 2, 'headwidth': 8},
            color=theme["text"],
            fontsize=10,
            fontweight="bold",
            ha="center",
        )
        circle = patches.Circle((cx, cy + 0.3), radius=0.6, facecolor="none", edgecolor=theme["dim"], linestyle=":")
        ax.add_patch(circle)

    def _draw_title_block(self, ax: plt.Axes, building: BuildingModel, floor: int, theme: dict[str, str]) -> None:
        """Draws professional architectural title block at bottom of blueprint."""
        meta = LabelingManager.get_title_block_data(building, floor=floor)
        
        # Professional standard A3 Architectural Title Block format
        block_w = building.plot.length * 0.9
        block_h = 2.0
        bx = building.plot.length * 0.05
        by = -3.5
        
        # Main Title Box
        rect = patches.Rectangle((bx, by), block_w, block_h, facecolor=theme["title_bg"], edgecolor=theme["dim"], lw=0.75, zorder=20)
        ax.add_patch(rect)
        
        # Vertical Separator Lines
        ax.plot([bx + block_w*0.3, bx + block_w*0.3], [by, by + block_h], color=theme["dim"], lw=0.5, zorder=21)
        ax.plot([bx + block_w*0.7, bx + block_w*0.7], [by, by + block_h], color=theme["dim"], lw=0.5, zorder=21)
        
        # Content Left: Branding & Project
        ax.text(bx + 0.5, by + 1.4, "Buildmetrics AI", color=theme["door"], fontsize=9, fontweight="black", zorder=22)
        ax.text(bx + 0.5, by + 0.7, "ARCHITECTURAL BLUEPRINT", color=theme["text"], fontsize=7, fontweight="bold", zorder=22)
        ax.text(bx + 0.5, by + 0.3, f"STYLE: {meta['ARCHITECTURAL_STYLE']}", color=theme["dim"], fontsize=6, zorder=22)

        # Content Center: Specs
        ax.text(bx + block_w*0.35, by + 1.4, f"FLOOR LEVEL: {meta['FLOOR_LEVEL']}", color=theme["text"], fontsize=7, fontweight="bold", zorder=22)
        ax.text(bx + block_w*0.35, by + 0.8, f"PLOT: {meta['PLOT_DIMENSIONS']}", color=theme["dim"], fontsize=6, zorder=22)
        ax.text(bx + block_w*0.35, by + 0.3, f"BUILT AREA: {meta['TOTAL_BUILT_AREA']}", color=theme["dim"], fontsize=6, zorder=22)

        # Content Right: Meta
        import datetime
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        ax.text(bx + block_w*0.75, by + 1.4, f"SCALE: {meta['SCALE']} @ A3", color=theme["text"], fontsize=7, fontweight="bold", zorder=22)
        ax.text(bx + block_w*0.75, by + 0.8, "DRAWN BY: Buildmetrics Engine", color=theme["dim"], fontsize=6, zorder=22)
        ax.text(bx + block_w*0.75, by + 0.3, f"DATE: {date_str}  REV: 01", color=theme["dim"], fontsize=6, zorder=22)

    def _draw_boundary_walls(self, ax: plt.Axes, building: BuildingModel, theme: dict[str, str]) -> None:
        """Draws boundary compound wall around the plot perimeter."""
        for wall in building.boundary_walls:
            ax.plot([wall.x1, wall.x2], [wall.y1, wall.y2], color=theme["dim"], linewidth=2.2, linestyle="-", zorder=2)

    def _draw_garden_area(self, ax: plt.Axes, building: BuildingModel, theme: dict[str, str]) -> None:
        """Draws landscape garden area, grass lawn, paved pathway, and tree CAD symbols."""
        for garden in building.gardens:
            # 1. Grass Lawn Background Fill
            lawn_box = patches.Rectangle(
                (garden.x, garden.y),
                garden.width,
                garden.height,
                facecolor=theme.get("garden", "#C8E6C9"),
                edgecolor=theme["dim"],
                linestyle=":",
                linewidth=0.8,
                alpha=0.35,
                zorder=1,
            )
            ax.add_patch(lawn_box)

            # 2. Paved Stone Walkway Path (Main Gate -> Building Entrance Door)
            if self.config.show_pathway and building.main_gates and building.doors:
                gate = building.main_gates[0]
                entrance_door = next((d for d in building.doors if d.floor == 1 and getattr(d, "door_type", "") == "double"), building.doors[0])

                path_x1, path_y1 = gate.x, gate.y
                path_x2, path_y2 = entrance_door.x, entrance_door.y

                ax.plot([path_x1, path_x2], [path_y1, path_y2], color=theme.get("pathway", theme["dim"]), linewidth=3.5, linestyle="--", alpha=0.75, zorder=2)
                mid_px = (path_x1 + path_x2) / 2
                mid_py = (path_y1 + path_y2) / 2
                ax.text(mid_px, mid_py, "PAVED PATHWAY", color=theme["text"], fontsize=6, fontweight="bold", ha="center", va="center", zorder=10)

            # 3. Tree CAD Symbols (Circles with crosshairs and foliage ring)
            if garden.tree_count > 0:
                spacing = garden.width / (garden.tree_count + 1)
                tree_radius = min(0.6, garden.height * 0.35)
                for i in range(1, garden.tree_count + 1):
                    tx = garden.x + i * spacing
                    ty = garden.y + garden.height * 0.5
                    
                    # Outer foliage circle
                    tree_foliage = patches.Circle((tx, ty), radius=tree_radius, facecolor="none", edgecolor=theme.get("garden", theme["dim"]), linewidth=1.2, zorder=5)
                    ax.add_patch(tree_foliage)
                    
                    # Inner trunk cross
                    ax.plot([tx - tree_radius * 0.4, tx + tree_radius * 0.4], [ty, ty], color=theme["dim"], lw=0.8, zorder=5)
                    ax.plot([tx, tx], [ty - tree_radius * 0.4, ty + tree_radius * 0.4], color=theme["dim"], lw=0.8, zorder=5)

            # 4. Garden Area Text Tag
            ax.text(
                garden.x + garden.width / 2,
                garden.y + garden.height * 0.25,
                f"{garden.name.upper()} ({garden.area:.1f} m²)",
                color=theme["text"],
                fontsize=7.5,
                fontweight="bold",
                ha="center",
                va="center",
                bbox={'boxstyle': "round,pad=0.2", 'facecolor': theme["bg"], 'edgecolor': theme["dim"], 'alpha': 0.8},
                zorder=10,
            )

    def _draw_main_gate(self, ax: plt.Axes, gate: Any, theme: dict[str, str], building: BuildingModel) -> None:
        """Draws architectural Main Compound Gate CAD symbol with pillars, swing arcs/sliding panels, and ENTRANCE arrow."""
        gx, gy, gw = gate.x, gate.y, gate.width
        pw = gate.pillar_width

        # 1. Gate Opening Mask on Boundary Wall
        ax.plot([gx - gw / 2, gx + gw / 2], [gy, gy], color=theme["bg"], linewidth=6.0, zorder=5)

        # 2. Left & Right Gate Columns / Pillars
        left_pillar = patches.Rectangle((gx - gw / 2 - pw, gy - pw / 2), pw, pw, facecolor=theme.get("gate", theme["pillar"]), edgecolor=theme["text"], hatch="///", lw=1.2, zorder=7)
        right_pillar = patches.Rectangle((gx + gw / 2, gy - pw / 2), pw, pw, facecolor=theme.get("gate", theme["pillar"]), edgecolor=theme["text"], hatch="///", lw=1.2, zorder=7)
        ax.add_patch(left_pillar)
        ax.add_patch(right_pillar)

        # 3. Gate Leaves & Swing / Sliding CAD Graphics
        gtype = getattr(gate, "gate_type", "double_swing")
        half_w = gw / 2

        if gtype == "sliding":
            ax.plot([gx - gw / 2, gx + 0.2], [gy + 0.1, gy + 0.1], color=theme.get("gate", theme["door"]), linewidth=2.5, zorder=8)
            ax.plot([gx - 0.2, gx + gw / 2], [gy - 0.1, gy - 0.1], color=theme.get("gate", theme["door"]), linewidth=2.5, zorder=8)
            ax.annotate("", xy=(gx + gw / 2 - 0.3, gy - 0.2), xytext=(gx, gy - 0.2), arrowprops={'arrowstyle': "->", 'color': theme.get("gate", theme["door"]), 'lw': 1.5}, zorder=8)
        else:
            # Double Swing Gate Panels & 90° Swing Arcs
            ax.plot([gx - gw / 2, gx - gw / 2], [gy, gy + half_w], color=theme.get("gate", theme["door"]), linewidth=2.2, zorder=8)
            ax.plot([gx + gw / 2, gx + gw / 2], [gy, gy + half_w], color=theme.get("gate", theme["door"]), linewidth=2.2, zorder=8)
            
            arc1 = patches.Arc((gx - gw / 2, gy), width=2 * half_w, height=2 * half_w, angle=0, theta1=0, theta2=90, color=theme.get("gate", theme["door"]), linestyle=":", linewidth=1.2, zorder=8)
            arc2 = patches.Arc((gx + gw / 2, gy), width=2 * half_w, height=2 * half_w, angle=0, theta1=90, theta2=180, color=theme.get("gate", theme["door"]), linestyle=":", linewidth=1.2, zorder=8)
            ax.add_patch(arc1)
            ax.add_patch(arc2)

        # 4. ENTRANCE Arrow Annotation
        ax.annotate(
            "MAIN ENTRANCE GATE ↑",
            xy=(gx, gy + 0.8),
            xytext=(gx, gy - 0.8),
            arrowprops={'facecolor': theme["text"], 'edgecolor': theme["text"], 'width': 2, 'headwidth': 7},
            color=theme["text"],
            fontsize=8,
            fontweight="bold",
            ha="center",
            va="center",
            zorder=10,
        )

    def to_opencv_image(self, fig: plt.Figure) -> np.ndarray:
        """Converts Matplotlib Figure into an OpenCV BGR numpy array."""
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=self.config.dpi, bbox_inches="tight")
        buf.seek(0)
        img_array = np.frombuffer(buf.getvalue(), dtype=np.uint8)
        img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img_bgr
