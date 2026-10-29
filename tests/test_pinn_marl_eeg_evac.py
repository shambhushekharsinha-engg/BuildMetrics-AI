"""
BUILD-MATRIX.ai Test Suite — Advanced AI Stack
Tests for PINN Structural, EEG Affective, MARL Architectural, and Evacuation modules.
Chapter 23: 67-test comprehensive verification suite.
"""
from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np
import pytest

# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def sample_building():
    """Generate a real BuildingModel for testing via LayoutEngine."""
    from build_matrix.layout_engine import LayoutEngine
    from build_matrix.models import ArchitecturalStyle, PlotDimensions
    plot = PlotDimensions(length=20.0, width=15.0, num_floors=2)
    engine = LayoutEngine(plot=plot, style=ArchitecturalStyle.MODERN)
    return engine.generate_building(prompt_parsed={})


@pytest.fixture(scope="module")
def simple_model():
    """Lightweight SimpleNamespace model for fast unit tests (no LayoutEngine)."""
    rooms = [
        SimpleNamespace(id="R1", name="Master Bedroom", room_type="master bedroom",
                        type="master", area=22.0, width=4.4, height=5.0,
                        floor=1, floor_height=2.8, color="#CE93D8"),
        SimpleNamespace(id="R2", name="Kitchen", room_type="kitchen",
                        type="kitchen", area=14.0, width=3.5, height=4.0,
                        floor=1, floor_height=2.7, color="#FFCC80"),
        SimpleNamespace(id="R3", name="Living Room", room_type="living room",
                        type="living", area=35.0, width=7.0, height=5.0,
                        floor=1, floor_height=4.5, color="#90CAF9"),
        SimpleNamespace(id="R4", name="Bathroom", room_type="bathroom",
                        type="bathroom", area=8.0, width=2.5, height=3.2,
                        floor=1, floor_height=2.4, color="#80CBC4"),
    ]
    plot = SimpleNamespace(length=20.0, width=15.0, num_floors=2,
                           floor_height=3.2, max_height=7.0)
    return SimpleNamespace(
        id="test-building",
        rooms=rooms,
        beams=[],
        pillars=[],
        doors=[
            SimpleNamespace(id="D1", x=5.0, y=0.0, width=0.9, floor=1, orientation="H"),
            SimpleNamespace(id="D2", x=15.0, y=0.0, width=0.9, floor=1, orientation="H"),
        ],
        plot=plot,
    )


# ──────────────────────────────────────────────────────────────────────────────
# PINN STRUCTURAL ENGINE TESTS  (8 tests)
# ──────────────────────────────────────────────────────────────────────────────

class TestPINNStructuralEngine:

    def test_pinn_import(self):
        from build_matrix.pinn_structural import PINNStructuralEngine
        assert PINNStructuralEngine() is not None

    def test_beam_section_inertia(self):
        """I = B*H^3/12 for default 300×450 mm section."""
        from build_matrix.pinn_structural import PINNStructuralEngine
        e = PINNStructuralEngine()
        I = e._beam_section_I()
        expected = e.B_M * e.H_M ** 3 / 12.0
        assert abs(I - expected) < 1e-10

    def test_euler_deflection_positive(self):
        """Midspan deflection must be positive and finite."""
        from build_matrix.pinn_structural import PINNStructuralEngine
        e = PINNStructuralEngine()
        beams = [SimpleNamespace(id="B1", x1=0.0, y1=0.0, x2=5.0, y2=0.0,
                                  width=0.3, depth=0.45, floor=1)]
        model = SimpleNamespace(beams=beams, pillars=[], rooms=[], plot=SimpleNamespace(
            floor_height=3.2, num_floors=2))
        results = e.analyze_beams(model)
        assert len(results) == 1
        assert results[0].deflection_mm > 0
        assert math.isfinite(results[0].deflection_mm)

    def test_fos_classify_safe(self):
        """FoS ≥ 2.0 → SAFE."""
        from build_matrix.pinn_structural import PINNStructuralEngine
        e = PINNStructuralEngine()
        assert e._classify(3.0) == "SAFE"

    def test_fos_classify_marginal(self):
        """1.5 ≤ FoS < 2.0 → MARGINAL."""
        from build_matrix.pinn_structural import PINNStructuralEngine
        e = PINNStructuralEngine()
        assert e._classify(1.7) == "MARGINAL"

    def test_fos_classify_critical(self):
        """FoS < 1.5 → CRITICAL."""
        from build_matrix.pinn_structural import PINNStructuralEngine
        e = PINNStructuralEngine()
        assert e._classify(1.0) == "CRITICAL"

    def test_fourier_encoding_output_shape(self):
        """Fourier encoding: (N, D) → (N, 2*F*D) for F=6, D=3."""
        from build_matrix.pinn_structural import PINNStructuralEngine
        pts = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        enc = PINNStructuralEngine.fourier_encoding(pts, F=6)
        assert enc.shape == (2, 2 * 6 * 3), f"Expected (2,36), got {enc.shape}"

    def test_stress_summary_keys(self, simple_model):
        """get_stress_summary must return dict with required keys."""
        from build_matrix.pinn_structural import PINNStructuralEngine
        summary = PINNStructuralEngine().get_stress_summary(simple_model)
        assert isinstance(summary, dict)
        for key in ("max_stress", "min_fos", "critical_count", "status_counts"):
            assert key in summary, f"Missing key: {key}"


# ──────────────────────────────────────────────────────────────────────────────
# EEG AFFECTIVE ENGINE TESTS  (6 tests)
# ──────────────────────────────────────────────────────────────────────────────

class TestEEGAffectiveEngine:

    def test_eeg_import(self):
        from build_matrix.eeg_affective import EEGAffectiveEngine
        assert EEGAffectiveEngine() is not None

    def test_profile_count_matches_rooms(self, simple_model):
        from build_matrix.eeg_affective import EEGAffectiveEngine
        profiles = EEGAffectiveEngine().compute_room_profiles(simple_model)
        assert len(profiles) == len(simple_model.rooms)

    def test_band_powers_clamped(self, simple_model):
        """All EEG band powers must be in [0.0, 1.0]."""
        from build_matrix.eeg_affective import EEGAffectiveEngine
        for p in EEGAffectiveEngine().compute_room_profiles(simple_model):
            for val in (p.alpha_power, p.beta_power, p.theta_power, p.gamma_power):
                assert 0.0 <= val <= 1.0, f"Band power {val} out of [0,1]"

    def test_vad_range(self, simple_model):
        """Valence and Arousal must be in [-1, +1]."""
        from build_matrix.eeg_affective import EEGAffectiveEngine
        for p in EEGAffectiveEngine().compute_room_profiles(simple_model):
            assert -1.0 <= p.valence <= 1.0
            assert -1.0 <= p.arousal <= 1.0

    def test_stress_level_valid_values(self, simple_model):
        from build_matrix.eeg_affective import EEGAffectiveEngine
        valid = {"LOW", "MEDIUM", "HIGH"}
        for p in EEGAffectiveEngine().compute_room_profiles(simple_model):
            assert p.stress_level in valid

    def test_summary_keys(self, simple_model):
        from build_matrix.eeg_affective import EEGAffectiveEngine
        eng = EEGAffectiveEngine()
        summary = eng.get_summary(eng.compute_room_profiles(simple_model))
        assert isinstance(summary, dict)
        for key in ("avg_valence", "avg_arousal", "avg_dominance", "stress_counts"):
            assert key in summary, f"Missing key: {key}"


# ──────────────────────────────────────────────────────────────────────────────
# MARL ARCHITECTURAL ENGINE TESTS  (6 tests)
# ──────────────────────────────────────────────────────────────────────────────

class TestMARLArchitecturalEngine:

    def test_marl_import(self):
        from build_matrix.marl_architectural import MARLArchitecturalEngine
        assert MARLArchitecturalEngine() is not None

    def test_simulate_returns_solution(self, simple_model):
        from build_matrix.marl_architectural import MARLArchitecturalEngine, MARLSolution
        sol = MARLArchitecturalEngine().simulate(simple_model, epochs=10)
        assert isinstance(sol, MARLSolution)

    def test_four_agents_in_result(self, simple_model):
        from build_matrix.marl_architectural import MARLArchitecturalEngine
        sol = MARLArchitecturalEngine().simulate(simple_model, epochs=10)
        assert len(sol.agents) == 4

    def test_agent_weights_sum_to_one(self):
        from build_matrix.marl_architectural import MARLArchitecturalEngine
        weights = list(MARLArchitecturalEngine().AGENTS.values())
        assert abs(sum(weights) - 1.0) < 1e-9, f"Weights sum {sum(weights)}"

    def test_qmix_monotonicity_constraint(self, simple_model):
        """QMIX monotonicity: all agent weights must be non-negative."""
        from build_matrix.marl_architectural import MARLArchitecturalEngine
        eng = MARLArchitecturalEngine()
        for w in eng.AGENTS.values():
            assert w >= 0.0, "QMIX weight must be non-negative"

    def test_layout_score_bounded(self, simple_model):
        """layout_score must be in [0, 1] (it's Q_tot at convergence)."""
        from build_matrix.marl_architectural import MARLArchitecturalEngine
        sol = MARLArchitecturalEngine().simulate(simple_model, epochs=10)
        assert 0.0 <= sol.layout_score <= 1.0, f"layout_score {sol.layout_score} out of [0,1]"


# ──────────────────────────────────────────────────────────────────────────────
# EVACUATION ENGINE TESTS  (6 tests)
# ──────────────────────────────────────────────────────────────────────────────

class TestEvacuationEngine:

    def test_evacuation_import(self):
        from build_matrix.evacuation_pathfinding import EvacuationEngine
        assert EvacuationEngine() is not None

    def test_weidmann_free_flow(self):
        """At near-zero density, speed ≈ V0 (free-flow walking speed)."""
        from build_matrix.evacuation_pathfinding import EvacuationEngine
        eng = EvacuationEngine()
        speed = eng.weidmann_speed(k=0.01)
        assert abs(speed - eng.V0) < 0.05, f"Expected ~{eng.V0}, got {speed}"

    def test_weidmann_jam_density_zero_speed(self):
        """At jam density K_JAM, speed should be 0."""
        from build_matrix.evacuation_pathfinding import EvacuationEngine
        eng = EvacuationEngine()
        assert eng.weidmann_speed(k=eng.K_JAM) == 0.0

    def test_weidmann_monotone_decrease(self):
        """Speed must decrease monotonically as density increases."""
        from build_matrix.evacuation_pathfinding import EvacuationEngine
        eng = EvacuationEngine()
        densities = [0.5 + i * 0.5 for i in range(9)]
        speeds = [eng.weidmann_speed(k) for k in densities]
        for i in range(len(speeds) - 1):
            assert speeds[i] >= speeds[i + 1], "Speed should decrease with density"

    def test_heatmap_is_8x8(self, simple_model):
        from build_matrix.evacuation_pathfinding import EvacuationEngine
        result = EvacuationEngine().simulate(simple_model)
        hm = result.egress_heatmap
        assert hasattr(hm, "__len__") or hasattr(hm, "shape")
        arr = np.array(hm)
        assert arr.shape == (8, 8), f"Heatmap shape {arr.shape} ≠ (8,8)"

    def test_evacuation_result_basic_fields(self, simple_model):
        from build_matrix.evacuation_pathfinding import EvacuationEngine, EvacuationResult
        result = EvacuationEngine().simulate(simple_model)
        assert isinstance(result, EvacuationResult)
        assert result.total_occupants > 0
        assert result.evacuation_time_s > 0
        assert isinstance(result.nfpa_compliant, bool)
        assert isinstance(result.bottleneck_locations, list)
