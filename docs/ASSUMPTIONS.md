# Engineering Assumptions & Safety Factors

This document outlines the hardcoded assumptions, load cases, material grades, and safety factors embedded in the `civil_math.py` and `cost_engine.py` logic. These heuristics are primarily for conceptual estimation and **must** be validated by a licensed structural engineer for actual construction.

### 1. Structural Materials & Volumes (`civil_math.py`)
- **Concrete Grade**: Assumes M20 / M25 equivalent for general residential slab and beam construction.
- **Slab Thickness**: Default is `0.5 ft (150 mm)` standard slab thickness for residential loads.
- **Steel Reinforcement Ratio**: Assumes `1.5%` of the wet concrete volume (approx. 115-120 kg/m³) based on IS 456 typical range for slabs/beams.
- **Steel Density**: Standard `7850 kg/m³` is used for mass conversion.
- **Brickwork / Blockwork**:
  - Wall Thickness: Assumes standard 200mm / 9-inch outer wall width.
  - Brick Factor: Assumes `50 bricks per square meter` of wall area (standard metric brick sizing with mortar joints).
- **Mortar Conversion**:
  - Dry to Wet Volume Conversion: `1.54` multiplier.
  - Mortar Volume Ratio: Assumes `30%` of the raw brick volume constitutes mortar joints.

### 2. Loading & Safety Factors (Implicit)
- **Dead Loads**: Factored into the 1.5% steel heuristic implicitly, assuming self-weight of a 150mm concrete slab and 200mm masonry walls.
- **Live Loads**: Assumes standard residential loading (~2 kN/m² or 40 psf).
- **Wind/Seismic**: Currently **NOT** factored into the volume/steel heuristics. High-rise projects (>4 floors) using these formulas will drastically underestimate shear wall and core reinforcement requirements.

### 3. Labor & Scheduling
- **Labor Productivity**: Assumes a baseline crew of 3 (1 skilled, 2 unskilled) can complete `100 sqft` of rough-in structure per day.
- **Weather Delay Risk**: Implicitly pads 12% delay risk for standard weather disruptions (rain/snow).

### 4. Cost Modeling (`cost_engine.py`)
- **Base Rates**: Reflects normalized 2025/2026 Q1 material indices for a standard tier-2 urban environment (USD).
- **Currency Conversions**: Uses static peg rates (`1 USD = 83 INR`, `1 USD = 0.92 EUR`).
- **Inflation**: Currently static; does not automatically poll live commodity prices.
