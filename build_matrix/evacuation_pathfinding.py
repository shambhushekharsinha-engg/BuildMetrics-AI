"""
BUILD-MATRIX.ai Evacuation Pathfinding & Weidmann Crowd Dynamics Engine
Simulates microscopic pedestrian egress using Weidmann speed-density relation (Chapter 15).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class EvacuationResult:
    """
    Full evacuation simulation output.

    Attributes
    ----------
    total_occupants      : Estimated occupant count.
    evacuation_time_s    : Estimated total evacuation time [seconds].
    max_density          : Peak pedestrian density at any grid cell [p/m2].
    bottleneck_locations : List of (row, col) tuples in the 8x8 heatmap with
                           density >= 75th-percentile of non-zero cells.
    nfpa_compliant       : True when NFPA 101 criteria are satisfied.
    egress_heatmap       : 8x8 numpy array of relative pedestrian density.
    weidmann_speeds      : Walking speeds [m/s] at integer densities 0-5 p/m2.
    """

    total_occupants: int
    evacuation_time_s: float
    max_density: float
    bottleneck_locations: list
    nfpa_compliant: bool
    egress_heatmap: np.ndarray          # shape (8, 8)
    weidmann_speeds: list               # speeds at k = 0, 1, 2, 3, 4, 5


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class EvacuationEngine:
    """
    Crowd Evacuation Engine using the Weidmann speed-density model.

    Weidmann (1993) speed-density relation
    ----------------------------------------
        v(k) = v0 * (1 - exp(-0.266 * (1/k - 1/5.4)))

    where
        v0 = 1.35 m/s  (free-flow walking speed)
        k  = crowd density [persons/m2]
        5.4 = maximum jam density [persons/m2]

    NFPA 101 compliance criteria (Life Safety Code)
    ------------------------------------------------
    1. Maximum travel distance to exit <= 61 m.
    2. At least 2 exits when occupancy > 50 persons.
    """

    # Weidmann parameters
    V0: float = 1.35          # Free-flow speed [m/s]
    GAMMA: float = 0.266      # Shape parameter
    K_JAM: float = 5.4        # Jam density [p/m2]

    # Occupancy load factor
    AREA_PER_PERSON_M2: float = 9.3   # 1 person per 9.3 m2 habitable area

    # NFPA 101
    NFPA_MAX_TRAVEL_M: float = 61.0
    NFPA_MIN_EXITS_FOR_50: int = 2

    # Heatmap grid
    GRID_SIZE: int = 8

    # ---------------------------------------------------------------------------
    # Public methods
    # ---------------------------------------------------------------------------

    def weidmann_speed(self, k: float) -> float:
        """
        Compute pedestrian walking speed using the Weidmann model.

        Parameters
        ----------
        k : float
            Crowd density [persons/m2].  Must be > 0 and < K_JAM.

        Returns
        -------
        float
            Walking speed [m/s].  Returns V0 for k <= 0, and 0 for k >= K_JAM.
        """
        if k <= 0.0:
            return self.V0
        if k >= self.K_JAM:
            return 0.0
        return self.V0 * (1.0 - math.exp(-self.GAMMA * (1.0 / k - 1.0 / self.K_JAM)))

    def get_weidmann_curve(self) -> tuple:
        """
        Generate the full Weidmann speed-density curve from k=0.1 to 5.0.

        Returns
        -------
        (densities, speeds)
            densities : list of float -- density values [persons/m2]
            speeds    : list of float -- corresponding speeds [m/s]
        """
        densities = list(np.round(np.arange(0.1, 5.1, 0.1), 2))
        speeds = [round(self.weidmann_speed(k), 4) for k in densities]
        return densities, speeds

    def simulate(self, building_model: Any) -> EvacuationResult:
        """
        Run the crowd evacuation simulation.

        Parameters
        ----------
        building_model : Any
            Domain model exposing:

            building_model.rooms   -- iterable of room objects with area,
                                      type (non-habitable: corridor, garage, etc.)
            building_model.exits   -- iterable of exit objects with x, y,
                                      width_m (door width)
            building_model.bounds  -- SimpleNamespace(width, depth) for floor plan
                                      dimensions [m]  (optional, default 20x20 m)

        Returns
        -------
        EvacuationResult
        """
        rooms  = list(getattr(building_model, "rooms",  []))
        exits  = list(getattr(building_model, "exits",  []))
        bounds = getattr(building_model, "bounds", None)

        bw = float(getattr(bounds, "width", 20.0)) if bounds else 20.0
        bd = float(getattr(bounds, "depth", 20.0)) if bounds else 20.0

        # --- Occupant count ---
        non_habitable = {"corridor", "staircase", "garage", "storage",
                         "balcony", "plant_room", "lobby", "lift"}
        habitable_area = sum(
            float(getattr(r, "area", 15.0))
            for r in rooms
            if str(getattr(r, "type", "")).lower() not in non_habitable
        )
        if habitable_area == 0.0:
            habitable_area = 60.0   # sensible default

        total_occupants = max(1, int(habitable_area / self.AREA_PER_PERSON_M2))

        # --- Exit positions ---
        if exits:
            exit_positions = [
                (float(getattr(e, "x", bw / 2.0)), float(getattr(e, "y", 0.0)))
                for e in exits
            ]
        else:
            # Default: two exits on opposing walls
            exit_positions = [(bw / 2.0, 0.0), (bw / 2.0, bd)]

        n_exits = len(exit_positions)

        # --- 8x8 egress heatmap ---
        heatmap = self._build_heatmap(bw, bd, exit_positions, total_occupants)

        # --- Peak density ---
        max_density = float(np.max(heatmap))

        # --- Bottlenecks ---
        nonzero = heatmap[heatmap > 0]
        if len(nonzero) > 0:
            threshold = float(np.percentile(nonzero, 75))
            bottleneck_locations = [
                (int(r), int(c))
                for r in range(self.GRID_SIZE)
                for c in range(self.GRID_SIZE)
                if heatmap[r, c] >= threshold
            ]
        else:
            bottleneck_locations = []

        # --- Evacuation time estimate ---
        avg_density = float(np.mean(heatmap[heatmap > 0])) if np.any(heatmap > 0) else 0.5
        avg_speed   = self.weidmann_speed(avg_density)

        # Approximate average travel distance to nearest exit
        cx_grid = np.linspace(0.0, bw, self.GRID_SIZE + 1)[:-1] + bw / (2 * self.GRID_SIZE)
        cy_grid = np.linspace(0.0, bd, self.GRID_SIZE + 1)[:-1] + bd / (2 * self.GRID_SIZE)
        total_dist_m = 0.0
        cell_count   = 0
        for ri, cy in enumerate(cy_grid):
            for ci, cx in enumerate(cx_grid):
                if heatmap[ri, ci] > 0:
                    d = min(
                        math.hypot(cx - ex, cy - ey)
                        for ex, ey in exit_positions
                    )
                    total_dist_m += d
                    cell_count   += 1

        avg_travel_m = total_dist_m / cell_count if cell_count else 15.0
        max_travel_m = math.hypot(bw, bd)        # diagonal as worst-case

        evac_time_s  = (avg_travel_m / avg_speed) if avg_speed > 0 else 999.0
        # Add queue delay at exits
        queue_delay  = total_occupants / (n_exits * 1.5 * avg_speed) if avg_speed > 0 else 0.0
        evac_time_s  = round(evac_time_s + queue_delay, 2)

        # --- NFPA 101 compliance ---
        nfpa_travel_ok = max_travel_m <= self.NFPA_MAX_TRAVEL_M
        nfpa_exits_ok  = (n_exits >= self.NFPA_MIN_EXITS_FOR_50
                          if total_occupants > 50 else True)
        nfpa_compliant = nfpa_travel_ok and nfpa_exits_ok

        # --- Weidmann speeds at integer densities 0-5 ---
        weidmann_speeds = [round(self.weidmann_speed(float(k)), 4) for k in range(6)]

        return EvacuationResult(
            total_occupants=total_occupants,
            evacuation_time_s=evac_time_s,
            max_density=round(max_density, 4),
            bottleneck_locations=bottleneck_locations,
            nfpa_compliant=nfpa_compliant,
            egress_heatmap=np.round(heatmap, 4),
            weidmann_speeds=weidmann_speeds,
        )

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _build_heatmap(
        self,
        bw: float,
        bd: float,
        exit_positions: list,
        total_occupants: int,
    ) -> np.ndarray:
        """
        Build an 8x8 pedestrian density heatmap.

        Density at each cell is modelled as inversely proportional to the
        distance to the nearest exit, then normalised so the total count of
        virtual persons matches total_occupants.

        Returns
        -------
        np.ndarray, shape (8, 8)  -- density values [persons/m2]
        """
        G = self.GRID_SIZE
        # Cell centre coordinates
        xs = np.linspace(0.0, bw, G + 1)[:-1] + bw / (2 * G)
        ys = np.linspace(0.0, bd, G + 1)[:-1] + bd / (2 * G)
        cell_area = (bw / G) * (bd / G)

        grid = np.zeros((G, G), dtype=float)
        for ri, cy in enumerate(ys):
            for ci, cx in enumerate(xs):
                min_dist = min(
                    math.hypot(cx - ex, cy - ey)
                    for ex, ey in exit_positions
                )
                # Inverse-distance weighting: cells far from exits have high density
                # (crowd queues build up furthest from exit)
                grid[ri, ci] = 1.0 / (min_dist + 0.5)

        # Normalise to actual person count
        total_weight = grid.sum() * cell_area
        persons_per_cell = (grid / total_weight) * total_occupants
        density_grid = persons_per_cell / cell_area   # [persons/m2]

        # Cap at jam density
        density_grid = np.clip(density_grid, 0.0, self.K_JAM)
        return density_grid


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from types import SimpleNamespace

    rooms = [
        SimpleNamespace(type="bedroom",  area=22.0),
        SimpleNamespace(type="kitchen",  area=14.0),
        SimpleNamespace(type="living",   area=35.0),
        SimpleNamespace(type="bathroom", area=8.0),
        SimpleNamespace(type="office",   area=12.0),
        SimpleNamespace(type="corridor", area=9.0),
    ]
    exits = [
        SimpleNamespace(x=10.0, y=0.0,  width_m=1.2),
        SimpleNamespace(x=10.0, y=20.0, width_m=1.0),
    ]
    bounds = SimpleNamespace(width=20.0, depth=20.0)
    model  = SimpleNamespace(rooms=rooms, exits=exits, bounds=bounds)

    engine = EvacuationEngine()

    # Weidmann curve
    densities, speeds = engine.get_weidmann_curve()
    print("Weidmann speed at k=1.0 p/m2:", engine.weidmann_speed(1.0), "m/s")

    result = engine.simulate(model)
    print(f"\nOccupants  : {result.total_occupants}")
    print(f"Evac. time : {result.evacuation_time_s:.1f} s")
    print(f"Max density: {result.max_density:.3f} p/m2")
    print(f"NFPA 101   : {'COMPLIANT' if result.nfpa_compliant else 'NON-COMPLIANT'}")
    print(f"Bottlenecks: {result.bottleneck_locations[:5]} ...")
    print(f"Heatmap shape: {result.egress_heatmap.shape}")
    print("Weidmann speeds @k=0..5:", result.weidmann_speeds)
