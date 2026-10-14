# 📚 BuildMetrics AI — Engineering & Architecture Documentation Index

This directory contains technical specifications, engineering assumptions, safety factors, and machine learning provenance documents for the BuildMetrics AI platform.

---

## 📑 Document Directory

| Document | Purpose & Summary |
| :--- | :--- |
| [`ASSUMPTIONS.md`](ASSUMPTIONS.md) | Engineering safety factors, IS 456 / ACI 318 load assumptions, rebar ratios, concrete grades (M25/M30), live load baselines ($2\text{ kN/m}^2$), and civil code boundary conditions. |
| [`MODEL_PROVENANCE.md`](MODEL_PROVENANCE.md) | Provenance, training methodology, feature engineering, and evaluation metrics for `cost_model.pkl` (Scikit-Learn Random Forest cost estimator). |

---

## 🏛️ Regulatory Standards & Building Codes Referenced

- **NBC India 2016** — National Building Code of India (Habitable room minimum dimensions, natural ventilation, egress corridor clearances).
- **IS 456:2000** — Plain and Reinforced Concrete Code of Practice (Column cross-section sizing, beam moment of resistance, slab thickness).
- **IS 1904:2021** — Design and Construction of Foundations in Soils (Safe Bearing Capacity, minimum foundation depth).
- **IS 1893:2016 (Part 1)** — Earthquake Resistant Design of Structures (Seismic zones II through V, ductile tie hook detailing).
- **IBC 2021** — International Building Code (International occupancy classifications and egress geometry).
- **buildingSMART IFC4 (ISO 10303-21)** — Industry Foundation Classes OpenBIM specification.
- **AutoCAD DXF Specification (AC1009 / R12)** — Drawing Exchange Format standard.
- **CSI MasterFormat 2016** — Construction Specifications Institute standard cost coding (Divisions 03, 04, 08, 09, 21–28).
