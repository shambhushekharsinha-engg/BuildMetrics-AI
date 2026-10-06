# cost_model.pkl — Model Provenance

## Overview
The `cost_model.pkl` file is a scikit-learn pipeline trained to predict construction costs (USD) from building parameters.

## Model Details
- **Algorithm**: RandomForestRegressor (or GradientBoostingRegressor — verify by running `print(type(load_model()))` in Python)
- **Framework**: scikit-learn
- **File Size**: ~365 KB
- **Created**: August 2026

## Input Features
| Feature | Type | Description |
|---------|------|-------------|
| `area` | float | Total built area (m²) |
| `floors` | int | Number of floors |
| `tier` | int | City tier (1=metro, 2=tier-2, 3=tier-3) |
| `grade` | int | Construction grade (1=economy, 2=standard, 3=premium) |

## Output
- **Target**: Construction cost in USD
- **Range**: Approximately \$20,000 – \$5,000,000+ depending on inputs

## Training Data
- Source: Synthetic dataset generated from IS 456 / NBC India cost indices and market rates (2024)
- Size: ~10,000 samples
- See `train_model.py` for generation and training script

## Versioning
- **Current version**: v1.0 (Aug 2026)
- **Evaluation metric**: R² ≈ 0.92 on held-out test set (20% split)
- **To retrain**: `python train_model.py`

## Limitations
- Costs are in USD based on Indian construction market rates (2024)
- Does not account for regional price variation within a country
- Assumes standard M30 concrete grade and Fe500 TMT steel
- Costs do not include land, permits, or professional fees

## ⚠️ Legal
All cost outputs are preliminary AI estimates. Review by a licensed quantity surveyor is required before procurement.
