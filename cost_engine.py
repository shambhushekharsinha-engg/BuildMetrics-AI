"""
BuildMetrics AI — Cost Engine
Scikit-learn ML-based construction cost prediction.
No Streamlit dependency: can be imported by API, worker, or Streamlit safely.
"""
import os
from functools import lru_cache

import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "cost_model.pkl")


@lru_cache(maxsize=1)
def load_model():
    """Load the trained cost prediction model (cached in-process)."""
    return joblib.load(MODEL_PATH)


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
    import pandas as pd  # Lazy import — not needed at module load time

    model = load_model()
    input_data = pd.DataFrame({
        "area": [area],
        "floors": [floors],
        "tier": [tier],
        "grade": [grade],
    })
    prediction = model.predict(input_data)
    return float(prediction[0])
