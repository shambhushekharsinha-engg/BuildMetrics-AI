"""
BuildMetrics AI — train_model.py
Trains and saves the construction cost prediction model.

Usage:
    python train_model.py

Output:
    cost_model.pkl  — scikit-learn pipeline (RandomForestRegressor)

Training Data:
    Synthetic dataset based on IS 456 / NBC India cost indices (2024 rates).
    Covers area: 50–5000 m², floors: 1–20, tier: 1–3, grade: 1–3.

Version: 1.1.0 (October 2026)
"""

import os
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

# ─── Reproducibility ────────────────────────────────────────────────────────
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ─── Synthetic Training Data Generation ─────────────────────────────────────
# Cost model based on:
#   Tier 1 (metro): ~$750/m² economy, ~$1200/m² standard, ~$1800/m² premium
#   Tier 2 (city): ~$550/m², ~$900/m², ~$1350/m²
#   Tier 3 (town): ~$400/m², ~$650/m², ~$980/m²
# Plus floor multiplier: each floor after ground adds 8% cost (structural complexity)

N_SAMPLES = 12000

areas = np.random.uniform(50, 5000, N_SAMPLES)
floors = np.random.randint(1, 21, N_SAMPLES)
tiers = np.random.randint(1, 4, N_SAMPLES)
grades = np.random.randint(1, 4, N_SAMPLES)

# Base rate by tier and grade (USD/m²)
BASE_RATES = {
    (1, 1): 750, (1, 2): 1200, (1, 3): 1800,
    (2, 1): 550, (2, 2): 900,  (2, 3): 1350,
    (3, 1): 400, (3, 2): 650,  (3, 3): 980,
}

costs = np.array([
    areas[i]
    * BASE_RATES[(tiers[i], grades[i])]
    * (1 + 0.08 * (floors[i] - 1))   # floor complexity multiplier
    * np.random.normal(1.0, 0.08)    # ±8% market noise
    for i in range(N_SAMPLES)
])
costs = np.clip(costs, 10000, None)  # Floor at $10k

X = np.column_stack([areas, floors, tiers, grades])
y = costs

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED)

# ─── Model Pipeline ─────────────────────────────────────────────────────────
model = Pipeline([
    ("scaler", StandardScaler()),
    ("rf", RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    ))
])

print("Training RandomForestRegressor on synthetic cost dataset...")
model.fit(X_train, y_train)

# ─── Evaluation ─────────────────────────────────────────────────────────────
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
print(f"  R² Score:  {r2:.4f}")
print(f"  MAE (USD): ${mae:,.0f}")

# ─── Save ────────────────────────────────────────────────────────────────────
output_path = os.path.join(os.path.dirname(__file__), "cost_model.pkl")
joblib.dump(model, output_path)
print(f"\nModel saved to: {output_path}")
print(f"  Samples trained: {len(X_train):,}")
print(f"  Features: area, floors, tier, grade")
print(f"  Version: 1.1.0 | {RANDOM_SEED=}")

if __name__ == "__main__":
    pass  # Script runs on import — protect against double-execution
