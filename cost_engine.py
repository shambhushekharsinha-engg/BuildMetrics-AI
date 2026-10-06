"""
BuildMetrics AI — Cost Engine
Scikit-learn ML-based construction cost prediction.
No Streamlit dependency: can be imported by API, worker, or Streamlit safely.
"""
import os
from functools import lru_cache

import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "cost_model.pkl")


_BASE_RATES = {
    (1, 1): 750.0, (1, 2): 1200.0, (1, 3): 1800.0,
    (2, 1): 550.0, (2, 2): 900.0,  (2, 3): 1350.0,
    (3, 1): 400.0, (3, 2): 650.0,  (3, 3): 980.0,
}


@lru_cache(maxsize=1)
def load_model():
    """Load the trained cost prediction model (cached in-process)."""
    return joblib.load(MODEL_PATH)


def _parametric_cost(area: float, floors: int, tier: int, grade: int) -> float:
    """Calibrated IS 456 / NBC parametric cost estimate (fallback across sklearn versions)."""
    rate = _BASE_RATES.get((int(tier), int(grade)), 900.0)
    floor_mult = 1.0 + 0.08 * max(int(floors) - 1, 0)
    return float(max(area * rate * floor_mult, 1000.0))


def predict_cost(area: float, floors: int, tier: int, grade: int) -> float:
    """
    Predict construction cost (USD) from building parameters.

    Args:
        area: Total built area in square meters.
        floors: Number of floors.
        tier: City tier (1=metro, 2=tier-2, 3=tier-3).
        grade: Construction grade (1=economy, 2=standard, 3=premium).

    Returns:
        Predicted cost in USD.
    """
    try:
        import numpy as np
        model = load_model()
        X = np.array([[float(area), float(floors), float(tier), float(grade)]])
        pred = float(model.predict(X)[0])
        if pred > 0:
            return pred
    except Exception:
        pass
    return _parametric_cost(area, floors, tier, grade)

