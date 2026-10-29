"""
BUILD-MATRIX.ai PINN Structural Analysis Engine
Computes Von Mises stress, Euler-Bernoulli deflections, and Factor of Safety
using closed-form structural mechanics formulas (Chapter 3).
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
class PINNResult:
    """Stores the structural analysis result for a single member."""

    member_id: str
    length_m: float
    load_kN: float
    stress_mpa: float
    deflection_mm: float
    fos: float
    status: str  # "SAFE" | "MARGINAL" | "CRITICAL"
    section: str = "300x450 mm"

    @property
    def load_kn(self) -> float:
        """Alias for load_kN."""
        return self.load_kN


class PINNSummary(dict):
    """Dictionary subclass providing attribute access for structural summary metrics."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    @property
    def overall_status(self) -> str:
        crit = self.get("critical_count", 0)
        marg = self.get("status_counts", {}).get("MARGINAL", 0)
        if crit > 0:
            return "CRITICAL"
        if marg > 0:
            return "MARGINAL"
        return "SAFE"

    @property
    def safe_count(self) -> int:
        return self.get("status_counts", {}).get("SAFE", 0)

    @property
    def marginal_count(self) -> int:
        return self.get("status_counts", {}).get("MARGINAL", 0)

    @property
    def critical_count(self) -> int:
        return self.get("critical_count", 0)

    @property
    def total_members(self) -> int:
        sc = self.get("status_counts", {})
        return sum(sc.values())

    @property
    def min_fos(self) -> float:
        return self.get("min_fos", 2.0)

    @property
    def max_stress_mpa(self) -> float:
        return self.get("max_stress", 0.0)

    @property
    def max_deflection_mm(self) -> float:
        return self.get("max_deflection_mm", 0.0)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PINNStructuralEngine:
    """
    Physics-Informed Structural Analysis Engine.

    Uses closed-form Euler-Bernoulli beam theory and Euler column buckling
    equations to evaluate structural performance without neural-network
    training. Encoding helpers follow the harmonic positional-encoding scheme
    described in Chapter 3.3.

    Material / section defaults
    ---------------------------
    Concrete grade : M30  (f'c = 30 MPa, E = 30 000 MPa, nu = 0.20)
    Beam section   : 300 mm x 450 mm
    Dead load      : 25 kN/m
    Live load      : 2.5 kN/m2 x tributary width
    """

    # Material
    E_MPA: float = 30_000.0   # Elastic modulus, MPa
    NU: float = 0.20           # Poisson ratio
    FC_MPA: float = 30.0       # Compressive strength, MPa

    # Section (beam)
    B_M: float = 0.30          # Width,  m
    H_M: float = 0.45          # Depth,  m

    # Loads
    WD_KNM: float = 25.0       # Dead load per unit length, kN/m
    WL_KNM2: float = 2.5       # Live load per unit area,  kN/m2

    # FoS thresholds
    FOS_SAFE: float = 2.0
    FOS_MARGINAL: float = 1.5

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _beam_section_I(self) -> float:
        """Second moment of area I = b*h^3/12  [m^4]."""
        return self.B_M * self.H_M ** 3 / 12.0

    def _classify(self, fos: float) -> str:
        if fos >= self.FOS_SAFE:
            return "SAFE"
        if fos >= self.FOS_MARGINAL:
            return "MARGINAL"
        return "CRITICAL"

    def _beam_analysis(
        self,
        member_id: str,
        length_m: float,
        trib_width_m: float,
    ) -> PINNResult:
        """
        Analyse a single simply-supported beam.

        Parameters
        ----------
        member_id   : Unique identifier string.
        length_m    : Span length [m].
        trib_width_m: Tributary width for live-load calculation [m].

        Returns
        -------
        PINNResult
        """
        # Distributed load [kN/m]
        q = self.WD_KNM + self.WL_KNM2 * trib_width_m

        # Section properties
        I = self._beam_section_I()          # m^4
        c = self.H_M / 2.0                  # Distance neutral axis to extreme fibre [m]

        # E in consistent units (kN/m2)
        E_kNm2 = self.E_MPA * 1_000.0      # 1 MPa = 1 kN/m2 * 1000

        # Mid-span deflection (Euler-Bernoulli, UDL)
        # delta = 5*q*L^4 / (384*E*I)  [m] -> convert to mm
        delta_m = 5.0 * q * length_m ** 4 / (384.0 * E_kNm2 * I)
        deflection_mm = delta_m * 1_000.0

        # Bending moment at mid-span
        M = q * length_m ** 2 / 8.0        # kN*m

        # Bending stress sigma = M*c/I  [kN/m2 -> MPa  (/1000)]
        sigma_bend_kNm2 = M * c / I
        sigma_bend_mpa = sigma_bend_kNm2 / 1_000.0

        # Von Mises (simplified: sigma_VM approx sigma_bend for pure bending)
        sigma_VM = sigma_bend_mpa

        # Factor of Safety
        fos = self.FC_MPA / sigma_VM if sigma_VM > 0 else float("inf")

        return PINNResult(
            member_id=member_id,
            length_m=length_m,
            load_kN=q * length_m,       # Total load on beam [kN]
            stress_mpa=round(sigma_VM, 4),
            deflection_mm=round(deflection_mm, 4),
            fos=round(fos, 4),
            status=self._classify(fos),
        )

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def analyze_beams(self, building_model: Any) -> list[PINNResult]:
        """
        Analyse all beams in building_model.

        The method iterates over building_model.beams.  Each beam is
        expected to expose (at minimum):

        beam.id         -- unique identifier
        beam.length     -- span [m]
        beam.trib_width -- tributary width [m]  (optional, defaults to B_M)

        Parameters
        ----------
        building_model : Any
            Domain model object (see BuildingModel in core).

        Returns
        -------
        list[PINNResult]
        """
        results: list[PINNResult] = []
        beams = getattr(building_model, "beams", [])

        for beam in beams:
            bid = getattr(beam, "id", f"beam_{len(results)}")
            length = float(getattr(beam, "length", 5.0))
            trib = float(getattr(beam, "trib_width", self.B_M))
            results.append(self._beam_analysis(bid, length, trib))

        return results

    def analyze_columns(self, building_model: Any) -> list[PINNResult]:
        """
        Analyse all columns (pillars) in building_model.

        Each column is expected to expose:

        pillar.id       -- unique identifier
        pillar.height   -- storey height [m]
        pillar.floors   -- number of floors supported
        pillar.area     -- tributary floor area [m2]
        pillar.b        -- section width [m]  (square section assumed)

        Euler buckling with effective-length factor K=1 (pin-pin).

        Parameters
        ----------
        building_model : Any

        Returns
        -------
        list[PINNResult]
        """
        results: list[PINNResult] = []
        pillars = getattr(building_model, "pillars", [])

        E_kNm2 = self.E_MPA * 1_000.0

        for pillar in pillars:
            pid = getattr(pillar, "id", f"col_{len(results)}")
            height = float(getattr(pillar, "height", 3.0))
            floors = float(getattr(pillar, "floors", 1))
            area = float(getattr(pillar, "area", 20.0))
            b = float(getattr(pillar, "b", 0.30))

            # Axial load: floors * area * (dead+live) intensity
            P = floors * area * (self.WD_KNM + self.WL_KNM2)  # kN

            # Square section: I = b^4/12
            I = b ** 4 / 12.0                  # m^4
            A_sec = b ** 2                      # m^2
            r = math.sqrt(I / A_sec)            # radius of gyration [m]

            # Effective length (K=1 pin-pin)
            KL = 1.0 * height                  # m

            # Slenderness
            slenderness = KL / r

            # Euler critical load [kN]
            Pcr = (math.pi ** 2 * E_kNm2 * I) / (KL ** 2)

            # FoS
            fos = Pcr / P if P > 0 else float("inf")

            # Axial stress for reporting [MPa]
            sigma_axial = (P / A_sec) / 1_000.0  # kN/m2 -> MPa

            results.append(PINNResult(
                member_id=pid,
                length_m=height,
                load_kN=round(P, 3),
                stress_mpa=round(sigma_axial, 4),
                deflection_mm=round(slenderness, 2),  # repurposed field: slenderness ratio
                fos=round(fos, 4),
                status=self._classify(fos),
                section=f"{int(b * 1000)}x{int(b * 1000)} mm",
            ))

        return results

    def get_stress_summary(self, building_model: Any) -> PINNSummary:
        """
        Return a high-level stress summary for the whole building.

        Parameters
        ----------
        building_model : Any

        Returns
        -------
        dict with keys:
            max_stress      -- highest Von Mises stress across all members [MPa]
            min_fos         -- lowest factor of safety
            critical_count  -- number of CRITICAL members
            status_counts   -- {'SAFE': n, 'MARGINAL': n, 'CRITICAL': n}
        """
        beams = self.analyze_beams(building_model)
        cols = self.analyze_columns(building_model)
        all_results = beams + cols

        if not all_results:
            return PINNSummary({
                "max_stress": 0.0,
                "max_deflection_mm": 0.0,
                "min_fos": float("inf"),
                "critical_count": 0,
                "status_counts": {"SAFE": 0, "MARGINAL": 0, "CRITICAL": 0},
            })

        max_stress = max(r.stress_mpa for r in all_results)
        max_defl = max(r.deflection_mm for r in all_results)
        min_fos = min(r.fos for r in all_results)
        status_counts = {"SAFE": 0, "MARGINAL": 0, "CRITICAL": 0}
        for r in all_results:
            status_counts[r.status] += 1

        return PINNSummary({
            "max_stress": round(max_stress, 4),
            "max_deflection_mm": round(max_defl, 2),
            "min_fos": round(min_fos, 4),
            "critical_count": status_counts["CRITICAL"],
            "status_counts": status_counts,
        })

    @staticmethod
    def fourier_encoding(coords: np.ndarray, F: int = 6) -> np.ndarray:
        """
        Harmonic positional encoding gamma(p) -- Chapter 3.3.

        For each coordinate dimension d and frequency index j=1...F:
            gamma_j,d(p) = [sin(2^j * pi * p_d), cos(2^j * pi * p_d)]

        Parameters
        ----------
        coords : np.ndarray, shape (N, D)
            Raw coordinate values (normalised to [0, 1] recommended).
        F : int
            Number of frequency bands (default 6 -> 2*F*D output features).

        Returns
        -------
        np.ndarray, shape (N, 2*F*D)
            Concatenated sine / cosine features.
        """
        coords = np.asarray(coords, dtype=float)
        if coords.ndim == 1:
            coords = coords[np.newaxis, :]   # (1, D)

        N, D = coords.shape
        features = []
        for j in range(1, F + 1):
            scale = (2 ** j) * math.pi
            features.append(np.sin(scale * coords))  # (N, D)
            features.append(np.cos(scale * coords))  # (N, D)

        return np.concatenate(features, axis=1)       # (N, 2*F*D)


# ---------------------------------------------------------------------------
# Quick self-test (not executed on import)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from types import SimpleNamespace

    # Minimal mock building model
    beams = [
        SimpleNamespace(id="B1", length=5.0, trib_width=3.0),
        SimpleNamespace(id="B2", length=7.5, trib_width=3.5),
        SimpleNamespace(id="B3", length=4.0, trib_width=2.5),
    ]
    pillars = [
        SimpleNamespace(id="C1", height=3.5, floors=3, area=25.0, b=0.35),
        SimpleNamespace(id="C2", height=3.5, floors=5, area=30.0, b=0.40),
    ]
    model = SimpleNamespace(beams=beams, pillars=pillars)

    engine = PINNStructuralEngine()
    print("=== Beams ===")
    for r in engine.analyze_beams(model):
        print(r)
    print("\n=== Columns ===")
    for r in engine.analyze_columns(model):
        print(r)
    print("\n=== Summary ===")
    print(engine.get_stress_summary(model))

    # Fourier encoding demo
    pts = np.array([[0.1, 0.5], [0.9, 0.2]])
    enc = PINNStructuralEngine.fourier_encoding(pts, F=3)
    print(f"\nFourier encoding shape: {enc.shape}")  # (2, 12)
