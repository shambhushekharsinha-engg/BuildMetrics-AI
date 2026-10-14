# 🏗️ `build_matrix` — Core Generative Architecture Engine

`build_matrix` is the algorithmic foundation of BuildMetrics AI. It houses all computational modules for procedural spatial partitioning, civil engineering mechanics, soil geotechnical assessment, Vastu Shastra spatial harmony, 2D vector CAD drawing, 3D WebGL generation, and multi-format OpenBIM/CAD export.

---

## 📦 Package Module Architecture

```
build_matrix/
├── models.py           # Domain models: BuildingModel, RoomSpec, PlotDimensions, etc.
├── schemas.py          # FastAPI Pydantic request & response contracts
├── layout_engine.py    # Recursive Binary Space Partitioning (BSP) floor plan generator
├── engineering.py      # IS 456 / ACI 318 structural mechanics, loads & deflection
├── geotech_engine.py   # Soil mechanics, Safe Bearing Capacity (SBC) & seismic detailing
├── vastu_engine.py     # 9-sector Vastu Purusha Mandala & Pancha Bhoota balance audit
├── eco_engine.py       # LEED scoring, solar PV offset & embodied carbon calculations
├── cad_dxf.py          # Layered AutoCAD ASCII DXF (AC1009/R12) vector generator
├── cad_ifc.py          # OpenBIM IFC4 (ISO 10303-21 STEP) BIM model generator
├── drawing_2d.py       # Matplotlib 2D architectural blueprint renderer (6 themes)
├── rendering_3d.py     # Three.js WebGL 3D scene builder with first-person HUD
├── exporter.py         # Multi-format synchronous & bundle export pipeline
├── input_handler.py    # Google Gemini prompt parser & NLP constraint extractor
├── comparison.py       # Differential design comparison & revision analysis
└── labeling.py         # Dynamic dimensioning, room tags & scale annotations
```

---

## 🔍 Deep-Dive: Module Breakdown

### 1. `models.py` — Core Spatial Data Structures
Defines domain dataclasses and Pydantic validation entities:
- `PlotDimensions`: Footprint length, width, floor height, max height, setback margins, wall thickness.
- `RoomSpec`: Position ($x, y$), width, length, floor level, target area, room type.
- `PillarSpec` & `BeamSpec`: Structural column and beam spatial geometry.
- `StructuralColumnSpec` & `StructuralBeamSpec`: Rebar schedules, concrete grades (M25–M50), tie spacing, and axial capacities ($kN$).
- `BOQEstimate`: Concrete volumetrics ($m^3$), rebar steel tonnage, brickwork area ($m^2$), glazing area ($m^2$), and multi-currency cost breakdowns.
- `BuildingModel`: The root aggregate holding all geometry, structural members, doors, windows, stairs, boundary walls, main gates, gardens, and compliance tags.

### 2. `layout_engine.py` — Procedural Space Synthesis
- Uses recursive Binary Space Partitioning (BSP) with architectural aspect-ratio constraints ($1:1$ to $1:2$).
- Organizes spatial hierarchies: Public zones (Living/Dining), Private zones (Bedrooms/Baths), Service zones (Kitchen/Utility/Stairwells).
- Automatic setback clearance: Allocates perimeter setback margins, exterior boundary walls, driveway pathways, and landscaping turf.

### 3. `engineering.py` — Structural Mechanics & Code Compliance
- **IS 456:2000 / ACI 318-19 Standard Rules**:
  - Minimum column cross-section ($300\text{mm} \times 300\text{mm}$ standard, $450\text{mm} \times 450\text{mm}$ heavy).
  - Main reinforcement: 4x16mm + 4x12mm Fe500 TMT rebars; lateral ties: 8mm @ 150mm c/c.
  - Beam sizing: Span/depth ratio ($L/12$ to $L/15$); 2x12mm top + 3x16mm bottom rebars.
- **Tributary Axial Load & Structural Safety Factor**:
  $$P_u = A_{\text{tributary}} \times w_{\text{service}} \times n_{\text{floors}}$$
  $$FS = \frac{P_{uz}}{P_u} \quad (\text{Target } FS \ge 1.50)$$
- **Critical Beam Span & Deflection Limits**:
  $$M_u = \frac{w_u L^2}{8}, \quad \delta_{\text{actual}} \le \frac{L}{250} \quad (\text{Serviceability Limit})$$

### 4. `geotech_engine.py` — Geotechnical Soil Mechanics
Evaluates site conditions according to IS 1904, IS 2911, and IBC Chapter 18:
- **5 Soil Profiles**: Hard Rock (600 kPa), Medium Sand (250 kPa), Stiff Clay (175 kPa), Black Cotton Expansive Soil (100 kPa), Soft Marine Clay (65 kPa).
- **Required Footing Contact Area**:
  $$A_{\text{footing}} = \frac{P_{\text{total}}}{SBC}$$
- **Excavation & Substructure Volumetrics**: Excavation volume with bulkage factor ($1.35x$), foundation slab concrete volume, and rebar tonnage.
- **IS 1893 Seismic Detailing**: Zone II ($PGA = 0.10g$) through Zone V ($PGA = 0.36g$) with mandatory ductile detailing, 135° hook ties, and shear core walls.

### 5. `vastu_engine.py` — Spatial Harmony Orientation
- Implements the traditional 9-zone **Vastu Purusha Mandala**:
  - *Ishanya* (North-East / Water): Pooja, meditation, living.
  - *Agni* (South-East / Fire): Kitchen, electrical load center.
  - *Nairutya* (South-West / Earth): Master bedroom, heavy structural mass.
  - *Vayavya* (North-West / Air): Guest rooms, ventilation outlets.
  - *Brahmasthan* (Central Core / Space): Unobstructed open energy core.
- Computes overall harmony score ($0\text{–}100$), auspicious grade ($A+, A, B, C$), 5-element (*Pancha Bhoota*) balance index, and non-structural remedial advice.

### 6. `cad_dxf.py` — Native AutoCAD Vector DXF Generator
- Produces clean ASCII DXF conforming to AutoCAD R12/2000 (`AC1009`) without external C-libraries.
- Generates 9 standard architectural layers:
  - `A-WALL-EXT`, `A-WALL-INT`, `A-COLS`, `A-BEAM`, `A-DOOR`, `A-WIND`, `A-ROMS`, `A-DIMS`, `A-SITE`.
- Natively compatible with AutoCAD, Revit, LibreCAD, Vectorworks, and SketchUp.

### 7. `cad_ifc.py` — OpenBIM IFC4 Generator
- Conforms to **ISO 10303-21 STEP physical file format** and the **buildingSMART IFC4 schema**.
- Semantic entities: `IfcProject`, `IfcSite`, `IfcBuilding`, `IfcBuildingStorey`, `IfcWallStandardCase`, `IfcColumn`, `IfcBeam`, `IfcSlab`, `IfcSpace`, and `IfcExtrudedAreaSolid`.
- Directly importable into Autodesk Revit, ArchiCAD, Solibri, BlenderBIM, and FreeCAD.

### 8. `drawing_2d.py` — 2D Architectural CAD Studio
- High-resolution Matplotlib engine configured with headless backend (`Agg`).
- 6 presentation palettes: *Classic Blueprint*, *Architectural Dark*, *Paper White*, *Japandi Earth*, *Scandinavian Light*, *Tropical Emerald*.
- Dynamic toggles for dimensions, column grids, axis bubbles, wall hatch patterns, door swings, plumbing fixtures, compass rose, scale ruler, and title block.

### 9. `rendering_3d.py` — 3D WebGL Visualizer
- Generates standalone Three.js HTML/JavaScript viewport.
- Floating Quick-Action Bar:
  - `🔄 3D Orbit`: Free camera rotation and pan.
  - `📐 2D Top`: Orthographic top-down plan view.
  - `🏢 Front Elevation`: True orthogonal facade projection.
  - `🚶 Walkthrough`: First-person WASD + mouse look camera.
  - `🏠 Roof Toggle`: Transparent or removed roof to inspect internal layout.
  - `☀️ Daylight Cycle`: Dynamic sun orientation and shadow projection.
  - `📸 HD Snapshot`: In-browser high-resolution PNG canvas capture.

### 10. `eco_engine.py` — Sustainability & LEED Sizing
- Formulas:
  - Solar generation: $\text{Area}_{\text{roof}} \times 0.70 \times 0.20 \text{ kW/m}^2 \times 5 \text{ hrs/day} \times 30 \text{ days}$.
  - Rainwater harvesting: $\text{Area}_{\text{roof}} \times \text{Rainfall}_{\text{annual}} \times 0.80 \text{ runoff efficiency}$.
  - Embodied carbon: $\text{Steel tons} \times 1.8 \text{ tCO}_2 + \text{Concrete m}^3 \times 0.15 \text{ tCO}_2$.
  - LEED potential scoring based on ASHRAE 90.1 energy baseline and low-carbon material substitution.

---

## 🧪 Unit Testing Core Engines

```bash
# Test all engines in build_matrix
pytest tests/test_layout.py tests/test_engineering.py tests/test_dxf_geotech_vastu.py tests/test_ifc.py -v
```
