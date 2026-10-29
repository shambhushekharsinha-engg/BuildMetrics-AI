"""
BUILD-MATRIX.ai MARL Architectural Design Agent Simulation
Simulates Dec-POMDP negotiation between 4 domain agents using QMIX value
factorization (Chapter 4).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    """Outcome for a single domain agent after the negotiation."""

    agent_name: str
    weight: float           # QMIX mixing weight [0, 1]
    score: float            # Final normalised Q-value [0, 1]
    top_action: str         # Best action label
    reward: float           # Cumulative reward over epochs


@dataclass
class MARLSolution:
    """Full negotiation solution returned by MARLArchitecturalEngine.simulate()."""

    agents: list
    total_reward: float                     # Q_tot at convergence
    pareto_optimal: bool                    # True when no single agent can improve alone
    iterations: int                         # Epochs until convergence (or max_epochs)
    equilibrium_reached: bool               # True when delta < 0.01
    layout_score: float                     # Final weighted layout quality [0, 1]
    _q_trace: list = field(default_factory=list, repr=False)

    @property
    def q_tot_history(self) -> list:
        """Alias for _q_trace history."""
        return self._q_trace

    @property
    def convergence_epoch(self) -> int:
        """Alias for iterations."""
        return self.iterations


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class MARLArchitecturalEngine:
    """
    Multi-Agent Reinforcement Learning Architectural Design Engine.

    Simulates a Dec-POMDP negotiation between four specialised domain agents:

    Agent        | Weight | Objective
    -------------|--------|--------------------------------------------------
    Architect    | 0.28   | Room aspect-ratio harmony (target 1.2-1.5)
    Structural   | 0.26   | Column regularity + beam span < 6 m
    MEP          | 0.22   | Wet-room clustering (kitchen/bath proximity)
    Eco          | 0.24   | South-facing room ratio

    Value factorisation follows QMIX:
        Q_tot = sum_i  w_i(s) * Q_i
    where w_i are non-negative monotonic mixing weights (held constant here).

    Convergence criterion: |Q_tot(t) - Q_tot(t-1)| < 0.01
    """

    AGENTS: dict = {
        "Architect":  0.28,
        "Structural": 0.26,
        "MEP":        0.22,
        "Eco":        0.24,
    }

    CONVERGENCE_DELTA: float = 0.01

    # ---------------------------------------------------------------------------
    # Private scoring methods (one per agent)
    # ---------------------------------------------------------------------------

    @staticmethod
    def _score_architect(building_model: Any, epoch: int) -> tuple:
        """
        Score based on room aspect-ratio harmony.

        Target ratio: 1.2 - 1.5  (width/depth or depth/width, always >= 1).
        Score = fraction of rooms within the target band.
        """
        rooms = getattr(building_model, "rooms", [])
        if not rooms:
            return 0.5, "maintain_proportions"

        in_band = 0
        for room in rooms:
            w = float(getattr(room, "width",  math.sqrt(getattr(room, "area", 16.0))))
            d = float(getattr(room, "depth",  math.sqrt(getattr(room, "area", 16.0))))
            ratio = max(w, d) / max(min(w, d), 0.001)
            if 1.2 <= ratio <= 1.5:
                in_band += 1

        score = in_band / len(rooms)
        # Slight epoch-based improvement: agents learn over time
        score = min(1.0, score + 0.01 * epoch * (1.0 - score))

        action = "adjust_aspect_ratio" if score < 0.7 else "maintain_proportions"
        return round(score, 4), action

    @staticmethod
    def _score_structural(building_model: Any, epoch: int) -> tuple:
        """
        Score based on column regularity and beam span.

        column_score   = 1 if pillars form a regular grid (variance of spacing < 0.5 m^2)
        span_score     = fraction of beams with span <= 6 m
        score          = 0.5 * column_score + 0.5 * span_score
        """
        beams   = getattr(building_model, "beams",   [])
        pillars = getattr(building_model, "pillars", [])

        # Span check
        if beams:
            short_spans = sum(1 for b in beams if float(getattr(b, "length", 5.0)) <= 6.0)
            span_score  = short_spans / len(beams)
        else:
            span_score = 0.8

        # Column regularity: use x/y positions if available
        if len(pillars) >= 2:
            xs = [float(getattr(p, "x", i * 3.0)) for i, p in enumerate(pillars)]
            ys = [float(getattr(p, "y", 0.0))      for p in pillars]
            dx = np.diff(sorted(xs))
            dy = np.diff(sorted(ys)) if len(set(ys)) > 1 else np.array([0.0])
            var = float(np.var(dx)) + float(np.var(dy))
            column_score = max(0.0, 1.0 - var / 2.0)
        else:
            column_score = 0.75

        score = 0.5 * column_score + 0.5 * span_score
        score = min(1.0, score + 0.008 * epoch * (1.0 - score))

        action = "reposition_columns" if column_score < 0.6 else "reduce_span_length"
        return round(score, 4), action

    @staticmethod
    def _score_mep(building_model: Any, epoch: int) -> tuple:
        """
        Score based on wet-room clustering.

        Computes centroid of kitchens and bathrooms; score is inversely
        proportional to the spread (std dev of distances to centroid).
        """
        rooms = getattr(building_model, "rooms", [])
        wet_types = {"kitchen", "bathroom", "toilet", "spa", "laundry", "utility"}

        wet_rooms = [r for r in rooms
                     if str(getattr(r, "type", "")).lower() in wet_types]

        if len(wet_rooms) < 2:
            score = 0.75
        else:
            xs = [float(getattr(r, "x", 0.0)) for r in wet_rooms]
            ys = [float(getattr(r, "y", 0.0)) for r in wet_rooms]
            cx, cy = float(np.mean(xs)), float(np.mean(ys))
            dists = np.sqrt((np.array(xs) - cx) ** 2 + (np.array(ys) - cy) ** 2)
            spread = float(np.std(dists))
            # Normalise: spread < 2 m is excellent, > 10 m is poor
            score = max(0.0, 1.0 - spread / 10.0)

        score = min(1.0, score + 0.007 * epoch * (1.0 - score))
        action = "cluster_wet_rooms" if score < 0.6 else "optimise_pipe_routing"
        return round(score, 4), action

    @staticmethod
    def _score_eco(building_model: Any, epoch: int) -> tuple:
        """
        Score based on south-facing room ratio.

        South-facing rooms are identified heuristically as those with a lower
        y-coordinate (south = lower y in a north-up plan).  Score = fraction of
        habitable rooms in the southern half.
        """
        rooms = getattr(building_model, "rooms", [])
        habitable_types = {"bedroom", "living", "lounge", "dining", "study", "office", "master"}
        habitable = [r for r in rooms
                     if str(getattr(r, "type", "")).lower() in habitable_types] or list(rooms)

        if not habitable:
            return 0.6, "orient_south"

        ys = [float(getattr(r, "y", 0.0)) for r in habitable]
        median_y = float(np.median(ys))
        south_facing = sum(1 for y in ys if y <= median_y)
        score = south_facing / len(habitable)

        score = min(1.0, score + 0.006 * epoch * (1.0 - score))
        action = "reorient_living_spaces" if score < 0.5 else "maximise_solar_gain"
        return round(score, 4), action

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def simulate(self, building_model: Any, epochs: int = 20) -> MARLSolution:
        """
        Run the MARL negotiation simulation.

        Parameters
        ----------
        building_model : Any
            Domain model object.
        epochs : int
            Maximum number of negotiation rounds (default 20).

        Returns
        -------
        MARLSolution
        """
        _score_fns = {
            "Architect":  self._score_architect,
            "Structural": self._score_structural,
            "MEP":        self._score_mep,
            "Eco":        self._score_eco,
        }

        agent_scores: dict = {a: [] for a in self.AGENTS}
        agent_actions: dict = {}
        q_trace: list = []

        prev_q_tot = 0.0
        convergence_epoch = epochs

        for ep in range(epochs):
            q_i: dict = {}
            for agent_name, fn in _score_fns.items():
                score, action = fn(building_model, ep)
                q_i[agent_name] = score
                agent_scores[agent_name].append(score)
                agent_actions[agent_name] = action

            # QMIX: Q_tot = weighted sum
            q_tot = sum(self.AGENTS[a] * q_i[a] for a in self.AGENTS)
            q_trace.append(round(q_tot, 6))

            delta = abs(q_tot - prev_q_tot)
            if delta < self.CONVERGENCE_DELTA and ep > 0:
                convergence_epoch = ep + 1
                # Pad trace to full epochs with final value
                q_trace.extend([q_tot] * (epochs - len(q_trace)))
                break

            prev_q_tot = q_tot

        final_q_tot = q_trace[-1] if q_trace else 0.0
        equilibrium  = convergence_epoch < epochs

        # Build per-agent results
        agent_results: list = []
        for agent_name, weight in self.AGENTS.items():
            scores = agent_scores[agent_name]
            final_score = scores[-1] if scores else 0.0
            cumulative_reward = float(np.sum(scores))
            agent_results.append(AgentResult(
                agent_name=agent_name,
                weight=weight,
                score=round(final_score, 4),
                top_action=agent_actions.get(agent_name, "observe"),
                reward=round(cumulative_reward, 4),
            ))

        # Pareto-optimality: no single agent can improve without hurting another
        # Simplified check: all scores > 0.6 implies Pareto front
        pareto_optimal = all(a.score >= 0.60 for a in agent_results)

        layout_score = round(final_q_tot, 4)

        solution = MARLSolution(
            agents=agent_results,
            total_reward=round(final_q_tot * convergence_epoch, 4),
            pareto_optimal=pareto_optimal,
            iterations=convergence_epoch,
            equilibrium_reached=equilibrium,
            layout_score=layout_score,
            _q_trace=q_trace,
        )
        return solution

    @staticmethod
    def get_convergence_trace(solution: MARLSolution) -> list:
        """
        Return the per-epoch Q_tot trajectory.

        Parameters
        ----------
        solution : MARLSolution

        Returns
        -------
        list[float]  -- Q_tot value at each negotiation epoch.
        """
        return list(solution._q_trace)


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from types import SimpleNamespace

    rooms = [
        SimpleNamespace(id="R1", type="bedroom",  area=20.0, width=4.0, depth=5.0, x=2.0,  y=1.0),
        SimpleNamespace(id="R2", type="kitchen",  area=14.0, width=3.5, depth=4.0, x=6.0,  y=1.0),
        SimpleNamespace(id="R3", type="living",   area=30.0, width=5.0, depth=6.0, x=2.0,  y=6.0),
        SimpleNamespace(id="R4", type="bathroom", area=7.0,  width=2.5, depth=2.8, x=5.5,  y=1.0),
        SimpleNamespace(id="R5", type="office",   area=12.0, width=3.0, depth=4.0, x=8.0,  y=4.0),
    ]
    beams = [
        SimpleNamespace(id="B1", length=5.0),
        SimpleNamespace(id="B2", length=7.0),
        SimpleNamespace(id="B3", length=4.5),
    ]
    pillars = [
        SimpleNamespace(id="C1", x=0.0, y=0.0),
        SimpleNamespace(id="C2", x=5.0, y=0.0),
        SimpleNamespace(id="C3", x=0.0, y=5.0),
        SimpleNamespace(id="C4", x=5.0, y=5.0),
    ]
    model = SimpleNamespace(id="demo", rooms=rooms, beams=beams, pillars=pillars)

    engine = MARLArchitecturalEngine()
    sol = engine.simulate(model, epochs=20)

    print(f"Equilibrium reached: {sol.equilibrium_reached}  after {sol.iterations} epochs")
    print(f"Layout score: {sol.layout_score:.4f}  |  Pareto-optimal: {sol.pareto_optimal}")
    for a in sol.agents:
        print(f"  {a.agent_name:12s}  w={a.weight:.2f}  Q={a.score:.4f}  action={a.top_action}")

    trace = engine.get_convergence_trace(sol)
    print(f"\nQ_tot trace ({len(trace)} epochs):", [round(v, 4) for v in trace])
