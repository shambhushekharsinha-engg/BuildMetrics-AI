"""
BUILD-MATRIX.ai EEG Affective Computing & Neuro-Architecture Engine
Maps room geometry to EEG frequency band power and Russell VAD coordinates (Chapter 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class RoomEEGProfile:
    """EEG frequency band power and affective state for a single room."""

    room_id: str
    room_name: str
    room_type: str          # e.g. "bedroom", "kitchen", "office", "bathroom"
    alpha_power: float      # 8-12 Hz band power [0, 1]
    beta_power: float       # 13-30 Hz band power [0, 1]
    theta_power: float      # 4-8 Hz band power [0, 1]
    gamma_power: float      # 30-100 Hz band power [0, 1]
    valence: float          # Russell VAD - Valence   [-1, 1]
    arousal: float          # Russell VAD - Arousal   [-1, 1]
    dominance: float        # Russell VAD - Dominance (typically [-1, 1])
    stress_level: str       # "LOW" | "MEDIUM" | "HIGH"
    recommendation: str     # Actionable neuro-architecture tip


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class EEGAffectiveEngine:
    """
    EEG Affective Computing & Neuro-Architecture Engine.

    Maps room geometry attributes (area, ceiling height, room type) to
    EEG-inspired frequency band powers, then projects these onto the
    Russell Valence-Arousal-Dominance (VAD) affective space.

    Band mapping rationale (Chapter 5)
    ------------------------------------
    Alpha (8-12 Hz) : relaxation, creativity, spatial openness
    Beta  (13-30 Hz): alertness, cognitive load, task engagement
    Theta (4-8 Hz)  : drowsiness, meditation, water/spa associations
    Gamma (30-100 Hz): sensory binding, high ceilings boost gamma
    """

    # Type-specific baseline band powers
    # Format: {room_type: (alpha_mid, beta_mid, theta_mid)}
    _TYPE_BANDS: dict = {
        "bedroom":    (0.80, 0.25, 0.50),
        "master":     (0.80, 0.25, 0.50),
        "living":     (0.60, 0.45, 0.40),
        "lounge":     (0.60, 0.45, 0.40),
        "kitchen":    (0.40, 0.60, 0.30),
        "dining":     (0.50, 0.55, 0.35),
        "office":     (0.35, 0.75, 0.30),
        "study":      (0.35, 0.75, 0.30),
        "bathroom":   (0.55, 0.30, 0.70),
        "toilet":     (0.50, 0.35, 0.65),
        "spa":        (0.60, 0.25, 0.80),
        "gym":        (0.30, 0.80, 0.25),
        "corridor":   (0.50, 0.50, 0.40),
        "staircase":  (0.45, 0.55, 0.35),
        "garage":     (0.35, 0.50, 0.30),
        "balcony":    (0.65, 0.40, 0.35),
    }
    _DEFAULT_BANDS: tuple = (0.50, 0.50, 0.40)

    _GAMMA_BASE: float = 0.30
    _GAMMA_CEILING_BOOST: float = 0.30   # added when floor_height > 4 m

    # Stress classification thresholds
    _ALPHA_LOW_THRESHOLD: float = 0.60
    _BETA_HIGH_THRESHOLD: float = 0.70
    _ALPHA_VERY_LOW: float = 0.40

    # Recommendation templates
    _RECS: dict = {
        "LOW": (
            "Room exhibits healthy alpha dominance. Maintain current proportions "
            "and natural lighting to preserve restorative ambience."
        ),
        "MEDIUM": (
            "Moderate beta activity detected. Consider introducing biophilic elements "
            "(plants, water features) or warm colour temperatures (2700-3000 K) to "
            "shift balance toward alpha relaxation."
        ),
        "HIGH": (
            "Elevated beta and suppressed alpha suggest a stressful environment. "
            "Recommendations: increase ceiling height, add acoustic dampening, "
            "introduce indirect natural light, and reduce visual clutter."
        ),
    }

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _get_type_key(self, room_type: str) -> str:
        """Normalise room_type string to a known key."""
        return room_type.lower().strip()

    def _band_powers(
        self,
        room_type: str,
        area_ratio: float,
        floor_height: float,
        rng: np.random.Generator,
    ) -> tuple:
        """
        Compute (alpha, beta, theta, gamma) band powers for a room.

        A small deterministic jitter (+-0.05) based on area_ratio is added to
        each mid-point value to make outputs feel realistic across similar rooms.

        Parameters
        ----------
        room_type    : Normalised room type string.
        area_ratio   : room_area / avg_room_area
        floor_height : Ceiling height [m]
        rng          : Seeded random generator for reproducible jitter.

        Returns
        -------
        (alpha, beta, theta, gamma) each in [0, 1]
        """
        key = self._get_type_key(room_type)
        alpha_mid, beta_mid, theta_mid = self._TYPE_BANDS.get(key, self._DEFAULT_BANDS)

        # Area-ratio modulates alpha slightly (larger rooms -> more relaxing)
        alpha = float(np.clip(alpha_mid + 0.05 * (area_ratio - 1.0) + rng.uniform(-0.03, 0.03), 0.0, 1.0))
        beta  = float(np.clip(beta_mid  - 0.03 * (area_ratio - 1.0) + rng.uniform(-0.03, 0.03), 0.0, 1.0))
        theta = float(np.clip(theta_mid + rng.uniform(-0.03, 0.03), 0.0, 1.0))

        # Gamma: base + ceiling boost
        gamma = self._GAMMA_BASE
        if floor_height > 4.0:
            gamma += self._GAMMA_CEILING_BOOST
        gamma = float(np.clip(gamma + rng.uniform(-0.02, 0.02), 0.0, 1.0))

        return alpha, beta, theta, gamma

    def _classify_stress(self, alpha: float, beta: float) -> str:
        if alpha > self._ALPHA_LOW_THRESHOLD:
            return "LOW"
        if beta > self._BETA_HIGH_THRESHOLD and alpha < self._ALPHA_VERY_LOW:
            return "HIGH"
        return "MEDIUM"

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def compute_room_profiles(self, building_model: Any) -> list:
        """
        Compute EEG-affective profiles for all rooms in building_model.

        The model is expected to expose building_model.rooms as an iterable
        of objects with at minimum:

        room.id           -- unique room identifier
        room.name         -- display name
        room.type         -- room type string (e.g. "bedroom")
        room.area         -- floor area [m2]
        room.floor_height -- ceiling height [m]  (optional, default 2.7 m)

        Parameters
        ----------
        building_model : Any

        Returns
        -------
        list[RoomEEGProfile]
        """
        rooms = getattr(building_model, "rooms", [])

        # Compute average room area for ratio normalisation
        areas = [float(getattr(r, "area", 15.0)) for r in rooms]
        avg_area = float(np.mean(areas)) if areas else 15.0

        # Seed RNG from building hash for reproducibility
        seed = abs(hash(str(getattr(building_model, "id", "default")))) % (2 ** 32)
        rng = np.random.default_rng(seed)

        profiles: list = []
        for room in rooms:
            rid = str(getattr(room, "id", f"room_{len(profiles)}"))
            rname = str(getattr(room, "name", rid))
            rtype = str(getattr(room, "type", "living"))
            area = float(getattr(room, "area", 15.0))
            floor_height = float(getattr(room, "floor_height", 2.7))

            area_ratio = area / avg_area if avg_area > 0 else 1.0

            alpha, beta, theta, gamma = self._band_powers(rtype, area_ratio, floor_height, rng)

            # Russell VAD mapping
            valence = float(np.clip((alpha - 0.5) * 2.0, -1.0, 1.0))
            arousal = float(np.clip((beta  - 0.5) * 2.0, -1.0, 1.0))
            dominance = float(area_ratio - 0.5)   # larger rooms -> more dominance

            stress = self._classify_stress(alpha, beta)

            profiles.append(RoomEEGProfile(
                room_id=rid,
                room_name=rname,
                room_type=rtype,
                alpha_power=round(alpha, 4),
                beta_power=round(beta, 4),
                theta_power=round(theta, 4),
                gamma_power=round(gamma, 4),
                valence=round(valence, 4),
                arousal=round(arousal, 4),
                dominance=round(dominance, 4),
                stress_level=stress,
                recommendation=self._RECS[stress],
            ))

        return profiles

    def get_summary(self, profiles: list) -> dict:
        """
        Aggregate summary across all room EEG profiles.

        Parameters
        ----------
        profiles : list[RoomEEGProfile]

        Returns
        -------
        dict with keys:
            avg_valence    -- mean valence score
            avg_arousal    -- mean arousal score
            avg_dominance  -- mean dominance score
            most_stressed  -- room_name of the most stressed room
            calmest        -- room_name of the calmest room
            stress_counts  -- {'LOW': n, 'MEDIUM': n, 'HIGH': n}
        """
        if not profiles:
            return {
                "avg_valence": 0.0,
                "avg_arousal": 0.0,
                "avg_dominance": 0.0,
                "most_stressed": None,
                "calmest": None,
                "stress_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
            }

        avg_valence   = float(np.mean([p.valence   for p in profiles]))
        avg_arousal   = float(np.mean([p.arousal   for p in profiles]))
        avg_dominance = float(np.mean([p.dominance for p in profiles]))

        # Most stressed: highest beta, lowest alpha -> highest (beta - alpha)
        most_stressed = max(profiles, key=lambda p: p.beta_power - p.alpha_power)
        calmest       = max(profiles, key=lambda p: p.alpha_power - p.beta_power)

        stress_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        for p in profiles:
            stress_counts[p.stress_level] += 1

        return {
            "avg_valence":    round(avg_valence,   4),
            "avg_arousal":    round(avg_arousal,   4),
            "avg_dominance":  round(avg_dominance, 4),
            "most_stressed":  most_stressed.room_name,
            "calmest":        calmest.room_name,
            "stress_counts":  stress_counts,
        }


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from types import SimpleNamespace

    rooms = [
        SimpleNamespace(id="R1", name="Master Bedroom", type="bedroom",   area=22.0, floor_height=2.8),
        SimpleNamespace(id="R2", name="Kitchen",        type="kitchen",   area=14.0, floor_height=2.7),
        SimpleNamespace(id="R3", name="Home Office",    type="office",    area=12.0, floor_height=2.7),
        SimpleNamespace(id="R4", name="Living Room",    type="living",    area=35.0, floor_height=4.5),
        SimpleNamespace(id="R5", name="Bathroom",       type="bathroom",  area=8.0,  floor_height=2.4),
    ]
    model = SimpleNamespace(id="test-building", rooms=rooms)

    engine = EEGAffectiveEngine()
    profiles = engine.compute_room_profiles(model)
    for p in profiles:
        print(f"{p.room_name:20s} alpha={p.alpha_power:.2f} beta={p.beta_power:.2f} "
              f"stress={p.stress_level:6s} V={p.valence:+.2f} A={p.arousal:+.2f}")

    print("\n=== Summary ===")
    print(engine.get_summary(profiles))
