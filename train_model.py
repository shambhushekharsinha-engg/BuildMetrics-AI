import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

# Generate synthetic dataset
np.random.seed(42)
n_samples = 1000

area = np.random.uniform(500, 5000, n_samples)
floors = np.random.randint(1, 10, n_samples)
tiers = np.random.choice(['Tier 1', 'Tier 2', 'Tier 3'], n_samples)
grades = np.random.choice(['Standard', 'Premium', 'Luxury'], n_samples)

# Base cost per sqft
base_cost = area * 1500

# Adjustments
tier_multiplier = {'Tier 1': 1.2, 'Tier 2': 1.0, 'Tier 3': 0.8}
grade_multiplier = {'Standard': 1.0, 'Premium': 1.3, 'Luxury': 1.6}

cost = base_cost * np.vectorize(tier_multiplier.get)(tiers) * np.vectorize(grade_multiplier.get)(grades)
# add some noise
cost += np.random.normal(0, cost * 0.05)

df = pd.DataFrame({
    'area': area,
    'floors': floors,
    'tier': tiers,
    'grade': grades,
    'total_cost': cost
})

# Preprocessing
numeric_features = ['area', 'floors']
categorical_features = ['tier', 'grade']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# Pipeline with XGBoost
pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', XGBRegressor(n_estimators=100, random_state=42))
])

X = df.drop('total_cost', axis=1)
y = df['total_cost']

print('Training model...')
pipeline.fit(X, y)

print('Saving model...')
joblib.dump(pipeline, 'cost_model.pkl')
print('Model saved to cost_model.pkl')

import json
from datetime import datetime, timezone

mae = 0.0
r2 = 0.0

metrics = {
    "version": "1.0.0",
    "mae": mae,
    "r2": r2,
    "algorithm": "RandomForestRegressor",
    "date": datetime.now(timezone.utc).isoformat()
}
with open('cost_model_meta.json', 'w') as f:
    json.dump(metrics, f, indent=2)
print('Model metadata saved to cost_model_meta.json')
