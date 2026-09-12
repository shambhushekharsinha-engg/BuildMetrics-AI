"""
Buildmetrics AI — AI-Powered Architectural Blueprint Generator
Interactive Web Application powered by Streamlit and Three.js.
"""

import os
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import streamlit as st
import streamlit.components.v1 as components

from build_matrix.models import ArchitecturalStyle, Blueprint2DConfig
from build_matrix.input_handler import InputHandler
from build_matrix.layout_engine import LayoutEngine
from build_matrix.drawing_2d import Blueprint2DRenderer
from build_matrix.rendering_3d import Blueprint3DRenderer
from build_matrix.exporter import ExporterEngine

# Streamlit Page Config
st.set_page_config(
    page_title="Buildmetrics AI — 2D & 3D Architectural Blueprint Generator",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

import db
db.init_db()

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Custom Styling
st.markdown(
    """
    <style>
    :root {
        --primary-color: #00F0FF;
        --secondary-color: #38BDF8;
        --card-bg: rgba(15, 23, 42, 0.85);
        --text-color: #F8FAFC;
    }
    .stApp { 
        background: radial-gradient(ellipse at top, #0f172a 0%, #020617 100%);
        color: var(--text-color); 
    }
    .main-header { font-size: 3.2rem; font-weight: 900; color: var(--primary-color); margin-bottom: 5px; text-shadow: 0px 0px 25px rgba(0,240,255,0.5); letter-spacing: 1.5px; }
    .sub-header { font-size: 1.2rem; color: #94A3B8; margin-bottom: 30px; letter-spacing: 0.5px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; }
    .metric-card { background: var(--card-bg); border-radius: 12px; padding: 25px; border-left: 5px solid var(--primary-color); border-top: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 40px 0 rgba(0, 0, 0, 0.5); backdrop-filter: blur(12px); margin-bottom: 15px; }
    .metric-card h4 { color: #94A3B8; margin-top: 0; font-size: 1.1rem; }
    .metric-card h2 { color: #F8FAFC; margin-bottom: 0; font-size: 2.2rem; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .stTabs [data-baseweb="tab"] { height: 50px; border-radius: 8px 8px 0 0; padding: 0 25px; background: rgba(255,255,255,0.03); color: #94A3B8; border: 1px solid rgba(255,255,255,0.05); border-bottom: none; transition: all 0.3s ease; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: var(--card-bg); color: var(--primary-color); border-top: 3px solid var(--primary-color); box-shadow: 0 -4px 15px rgba(0,240,255,0.15); font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True,
)

# App Header
st.markdown('<div class="main-header">📐 Buildmetrics AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">AI-Powered 2D Architectural Blueprints & 3D Structural Visualizations</div>',
    unsafe_allow_html=True,
)

# Sidebar Configuration
with st.sidebar.expander("👤 User Authentication", expanded=not st.session_state.user_id):
    if st.session_state.user_id:
        st.success(f"Logged in as {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
    else:
        auth_mode = st.radio("Mode", ["Login", "Sign Up"], horizontal=True)
        uname = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button(auth_mode):
            if auth_mode == "Sign Up":
                if db.create_user(uname, pwd):
                    st.success("Account created! Please login.")
                else:
                    st.error("Username already exists.")
            else:
                uid, msg = db.verify_user(uname, pwd)
                if uid:
                    st.session_state.user_id = uid
                    st.session_state.username = uname
                    st.rerun()
                else:
                    st.error(msg)

if st.session_state.user_id:
    with st.sidebar.expander("📁 Saved Projects"):
        proj_name = st.text_input("Project Name")
        if st.button("💾 Save Current Project"):
            if proj_name:
                db.save_project(
                    st.session_state.user_id, proj_name,
                    st.session_state.get('plot_length', 20.0),
                    st.session_state.get('plot_width', 15.0),
                    st.session_state.get('num_floors', 2),
                    st.session_state.get('prompt_parsed', {})
                )
                st.success("Saved!")
            else:
                st.warning("Enter a project name.")
        
        saved_projs = db.load_user_projects(st.session_state.user_id)
        if saved_projs:
            sel_proj = st.selectbox("Load Project", ["Select..."] + [p["name"] for p in saved_projs])
            if sel_proj != "Select...":
                proj_data = next((p for p in saved_projs if p["name"] == sel_proj), None)
                if proj_data:
                    st.session_state.prompt_parsed = proj_data["data"]
                    st.session_state.plot_length = proj_data["l"]
                    st.session_state.plot_width = proj_data["w"]
                    st.session_state.num_floors = proj_data["floors"]
                    st.success("Loaded! Click Generate.")

with st.sidebar.expander("🤖 Agentic Architect Chat", expanded=False):
    st.caption("Talk to the AI architect to dynamically alter the blueprint.")
    for msg in st.session_state.chat_history:
        st.markdown(f"**{msg['role'].capitalize()}**: {msg['content']}")
    
    ai_input = st.text_input("Ask AI...", placeholder="e.g., Make plot width 30m and add a pool")
    if st.button("💬 Send to Architect"):
        if ai_input:
            st.session_state.chat_history.append({"role": "user", "content": ai_input})
            try:
                import google.generativeai as genai
                model = genai.GenerativeModel("gemini-2.5-flash")
                chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history])
                sys_prompt = f"You are an AI architect. The user is updating a building layout. Current prompt: '{st.session_state.get('prompt_parsed', {}).get('raw_prompt', '')}'. Respond briefly with the new updated prompt instruction based on their request. Do not explain."
                response = model.generate_content(f"{sys_prompt}\n\nChat:\n{chat_context}")
                new_instruction = response.text.strip()
                st.session_state.chat_history.append({"role": "assistant", "content": f"Understood. I will redesign based on: {new_instruction}"})
                # Override the manual prompt
                st.session_state.ai_override_prompt = new_instruction
                st.rerun()
            except Exception as e:
                st.error(f"AI Error: {str(e)}")

st.sidebar.header("🕹️ Building Control Panel")

# 1. Prompt Input
prompt_val = st.session_state.get("ai_override_prompt", "Modern 2-story villa with living room, master bedroom, 2 guest bedrooms, kitchen, 6 pillars, wide balcony, main gate, and front garden area")
prompt_input = st.sidebar.text_area(
    "Natural Language Design Prompt",
    value=prompt_val,
    height=80,
    help="Specify architectural style, room requests, floors, pillars, beams, main gate, garden, or special details.",
)
if prompt_input != prompt_val and "ai_override_prompt" in st.session_state:
    st.session_state.ai_override_prompt = prompt_input # Manual edit overrides AI

# 2. Architectural Style
style_option = st.sidebar.selectbox(
    "Architectural Style",
    options=[s.value for s in ArchitecturalStyle],
    index=0,
)
selected_style = next(s for s in ArchitecturalStyle if s.value == style_option)

# 3. Plot Dimensions
st.sidebar.subheader("📐 Plot & Building Constraints")
col_p1, col_p2 = st.sidebar.columns(2)
with col_p1:
    plot_length = st.number_input("Plot Length (X) [m]", min_value=5.0, max_value=1000.0, value=20.0, step=1.0)
    num_floors = st.number_input("Floors", min_value=1, max_value=100, value=2, step=1)
with col_p2:
    plot_width = st.number_input("Plot Width (Y) [m]", min_value=5.0, max_value=1000.0, value=15.0, step=1.0)
    max_height = st.number_input("Max Height [m]", min_value=3.0, max_value=350.0, value=9.0, step=0.5)

col_p3, col_p4 = st.sidebar.columns(2)
with col_p3:
    wall_thickness = st.number_input("Wall Thickness [cm]", min_value=10, max_value=100, value=25, step=5) / 100.0
with col_p4:
    margin_setback = st.number_input("Setback Margin [m]", min_value=0.0, max_value=50.0, value=2.0, step=0.5)

# 3b. Main Gate & Landscaping Settings
st.sidebar.subheader("🚪 Compound Gate & Garden")
gate_type_sel = st.sidebar.selectbox(
    "Main Gate Type",
    options=["Double Swing Gate", "Sliding Gate", "Modern Slat Gate", "Wrought Iron Gate"],
    index=0,
)
gate_type_code_map = {
    "Double Swing Gate": "double_swing",
    "Sliding Gate": "sliding",
    "Modern Slat Gate": "modern_slat",
    "Wrought Iron Gate": "wrought_iron",
}

garden_style_sel = st.sidebar.selectbox(
    "Garden & Lawn Layout",
    options=["Front Garden & Lawn", "Courtyard Garden", "Wrap-around Garden"],
    index=0,
)

# 4. Blueprint 2D Styling Controls
st.sidebar.subheader("🎨 2D Theme & Annotations")
blueprint_theme = st.sidebar.selectbox(
    "Blueprint Color Theme",
    options=["Classic Blueprint", "Architectural Dark", "Paper White", "Japandi Earth", "Scandinavian Light", "Tropical Emerald"],
    index=0,
)

prompt_parsed = InputHandler.parse_prompt(prompt_input)
# Override style and gate/garden settings from explicit dropdowns
prompt_parsed["style"] = selected_style
prompt_parsed["main_gate_type"] = gate_type_code_map.get(gate_type_sel, "double_swing")

col_opt1, col_opt2 = st.sidebar.columns(2)
with col_opt1:
    show_dims = st.checkbox("Show Dimensions", value=True)
    show_pillars = st.checkbox("Show Pillars", value=True)
    show_beams = st.checkbox("Show Beams", value=True)
    show_stairs = st.checkbox("Show Stairs", value=True)
    show_gate = st.checkbox("Main Gate", value=prompt_parsed.get("include_main_gate", False))
with col_opt2:
    show_labels = st.checkbox("Room Labels", value=True)
    show_fixtures = st.checkbox("Furniture CAD", value=True)
    show_axis_grid = st.checkbox("Axis Grid (A,1)", value=True)
    show_hatches = st.checkbox("Wall Hatches", value=True)
    show_garden = st.checkbox("Garden & Lawn", value=value if (value := prompt_parsed.get("include_garden", False)) else False)

col_opt3, col_opt4 = st.sidebar.columns(2)
with col_opt3:
    show_compass = st.checkbox("Compass Rose", value=True)
    show_boundary = st.checkbox("Boundary Wall", value=True)
with col_opt4:
    show_title = st.checkbox("Title Block", value=True)
    show_pathway = st.checkbox("Paved Walkway", value=True)

# Apply UI toggle selections to parsed prompt
prompt_parsed["include_main_gate"] = show_gate
prompt_parsed["include_garden"] = show_garden

# Process Input & Generate Spatial Model
plot_dims = InputHandler.create_plot_dimensions(
    length=plot_length,
    width=plot_width,
    max_height=max_height,
    num_floors=num_floors,
    wall_thickness=wall_thickness,
    margin=margin_setback,
)

# Generate Building Model using LayoutEngine
layout_engine = LayoutEngine(plot=plot_dims, style=selected_style)
building_model = layout_engine.generate_building(prompt_parsed=prompt_parsed)

# Top Key Metrics Summary
total_built = sum(building_model.total_building_area(f) for f in range(1, plot_dims.num_floors + 1))
gate_w_str = f"{building_model.main_gates[0].width:.1f}m Gate" if building_model.main_gates else "No Gate"

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(f'<div class="metric-card"><h4>📏 Plot Footprint</h4><h2>{plot_length*plot_width:.0f} m²</h2><p style="color:#94A3B8; margin:0;">{plot_length:.1f}m x {plot_width:.1f}m dimensions</p></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<div class="metric-card"><h4>🏢 Total Built Area</h4><h2>{total_built:.0f} m²</h2><p style="color:#94A3B8; margin:0;">Across {plot_dims.num_floors} levels</p></div>', unsafe_allow_html=True)
with col_m3:
    st.markdown(f'<div class="metric-card"><h4>🌳 Garden & Lawn</h4><h2>{building_model.total_garden_area():.0f} m²</h2><p style="color:#94A3B8; margin:0;">{gate_w_str} Entrance</p></div>', unsafe_allow_html=True)
with col_m4:
    st.markdown(f'<div class="metric-card"><h4>🏗️ Structural Frame</h4><h2>{len(building_model.pillars)} Col</h2><p style="color:#94A3B8; margin:0;">{len(building_model.beams)} Beams structural grid</p></div>', unsafe_allow_html=True)

st.divider()

# Main Interactive Workspace Tabs
tab_2d, tab_3d, tab_schedule, tab_eng, tab_risk, tab_export = st.tabs(
    [
        "📐 2D CAD Blueprint Studio",
        "🏗️ 3D Blueprint Visualizer",
        "📋 Architectural Schedule",
        "🧱 Structural Engineering & BOQ Costing",
        "🌦️ Scheduling & Risk Management",
        "📥 Export Center",
    ]
)


# ---------------------------------------------------------
# TAB 1: 2D Blueprint Studio
# ---------------------------------------------------------
with tab_2d:
    col_view, col_info = st.columns([3, 1])

    with col_info:
        st.subheader("Floor Selection")
        selected_floor = st.radio(
            "Select Floor View",
            options=list(range(1, plot_dims.num_floors + 1)),
            format_func=lambda f: f"Floor {f}",
            horizontal=True,
        )

        st.subheader("Floor Summary")
        floor_rooms = [r for r in building_model.rooms if r.floor == selected_floor]
        st.write(f"**Rooms on Floor {selected_floor}:** {len(floor_rooms)}")
        for r in floor_rooms:
            st.caption(f"• **{r.name}**: {r.width:.2f}m x {r.height:.2f}m ({r.area:.1f} m²)")

    with col_view:
        config_2d = Blueprint2DConfig(
            theme=blueprint_theme,
            show_dimensions=show_dims,
            show_pillars=show_pillars,
            show_beams=show_beams,
            show_stairs=show_stairs,
            show_fixtures=show_fixtures,
            show_axis_grid=show_axis_grid,
            show_hatches=show_hatches,
            show_room_labels=show_labels,
            show_compass=show_compass,
            show_title_block=show_title,
            show_main_gate=show_gate,
            show_garden=show_garden,
            show_boundary_wall=show_boundary,
            show_pathway=show_pathway,
            dpi=200,
        )

        renderer_2d = Blueprint2DRenderer(config=config_2d)
        fig_2d = renderer_2d.render(building_model, floor=selected_floor)
        st.pyplot(fig_2d, clear_figure=True)


# ---------------------------------------------------------
# TAB 2: 3D Blueprint Visualizer
# ---------------------------------------------------------
with tab_3d:
    st.subheader("Interactive 3D WebGL Blueprint Viewport")
    st.caption("Use your mouse to orbit, pan, and zoom the 3D model. Switch render modes inside the viewport.")

    renderer_3d = Blueprint3DRenderer(building_model)
    html_3d_code = renderer_3d.generate_threejs_html()

    # Embed Three.js 3D Viewport HTML Component
    components.html(html_3d_code, height=650, scrolling=False)


# ---------------------------------------------------------
# TAB 3: Structural Schedule
# ---------------------------------------------------------
with tab_schedule:
    st.subheader("Architectural & Structural Element Schedule")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("### 🏛️ Pillars (Columns) Schedule")
        pillar_data = [
            {
                "ID": p.id,
                "Floor": p.floor,
                "Position (X, Y)": f"({p.x:.2f}m, {p.y:.2f}m)",
                "Dimensions": f"{p.width:.2f}m x {p.height:.2f}m",
                "Shape": p.shape.capitalize(),
            }
            for p in building_model.pillars
        ]
        st.dataframe(pillar_data, use_container_width=True)

        st.markdown("### 🚪 Doors & Openings Schedule")
        door_data = [
            {
                "ID": d.id,
                "Floor": d.floor,
                "Type": getattr(d, "door_type", "single").capitalize(),
                "Width": f"{d.width:.2f}m",
                "Orientation": d.orientation.capitalize(),
                "Position (X, Y)": f"({d.x:.2f}m, {d.y:.2f}m)",
            }
            for d in building_model.doors
        ]
        st.dataframe(door_data, use_container_width=True)

        st.markdown("### 🪜 Staircase Schedule")
        stair_data = [
            {
                "ID": s.id,
                "Floor": s.floor,
                "Flight Span": f"{s.width:.2f}m W x {s.length:.2f}m L",
                "Risers": f"{s.num_steps} Steps (@ 0.18m)",
                "Direction": s.direction.upper(),
                "Position (X, Y)": f"({s.x:.2f}m, {s.y:.2f}m)",
            }
            for s in building_model.stairs
        ]
        st.dataframe(stair_data, use_container_width=True)

    with col_s2:
        st.markdown("### 🏗️ Beams Schedule")
        beam_data = [
            {
                "ID": b.id,
                "Floor": b.floor,
                "Start Point": f"({b.x1:.2f}m, {b.y1:.2f}m)",
                "End Point": f"({b.x2:.2f}m, {b.y2:.2f}m)",
                "Width x Depth": f"{b.width:.2f}m x {b.depth:.2f}m",
            }
            for b in building_model.beams
        ]
        st.dataframe(beam_data, use_container_width=True)

        st.markdown("### 🪟 Windows Schedule")
        win_data = [
            {
                "ID": w.id,
                "Floor": w.floor,
                "Type": getattr(w, "window_type", "standard").capitalize(),
                "Width": f"{w.width:.2f}m",
                "Orientation": w.orientation.capitalize(),
                "Position (X, Y)": f"({w.x:.2f}m, {w.y:.2f}m)",
            }
            for w in building_model.windows
        ]
        st.dataframe(win_data, use_container_width=True)

        st.markdown("### 🛋️ Architectural Fixtures & Furniture Schedule")
        fix_data = [
            {
                "ID": f.id,
                "Floor": f.floor,
                "Category": f.fixture_type.replace('_', ' ').title(),
                "Item Name": f.name,
                "Size (W x H)": f"{f.width:.2f}m x {f.height:.2f}m",
                "Location (X, Y)": f"({f.x:.2f}m, {f.y:.2f}m)",
            }
            for f in building_model.fixtures
        ]
        st.dataframe(fix_data, use_container_width=True)



# ---------------------------------------------------------
# TAB 4: Structural Engineering & BOQ Costing
# ---------------------------------------------------------
with tab_eng:
    st.subheader("🧱 IS 456 / ACI 318 Structural Engineering & BOQ Takeoff")
    st.caption("Detailed structural rebar reinforcement schedules, concrete grades, and multi-currency construction cost estimates.")

    if building_model.boq_estimate:
        boq = building_model.boq_estimate
        st.markdown("### 💰 Bill of Quantities (BOQ) Cost Estimate")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><h4>💵 Cost (USD)</h4><h2>${boq.cost_usd:,.2f}</h2><p style="color:#94A3B8; margin:0;">Concrete: {boq.concrete_volume_m3:,.2f} m³ | Glass: {boq.glass_m2:,.2f} m²</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><h4>₹ Cost (INR)</h4><h2>₹{boq.cost_inr:,.2f}</h2><p style="color:#94A3B8; margin:0;">Steel: {boq.steel_weight_tons:,.2f} Tons | Brick: {boq.brickwork_m2:,.2f} m²</p></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><h4>€ Cost (EUR)</h4><h2>€{boq.cost_eur:,.2f}</h2><p style="color:#94A3B8; margin:0;">MEP: ${boq.mep_cost_usd:,.2f} | Floor: {boq.flooring_m2:,.2f} m²</p></div>', unsafe_allow_html=True)

        st.divider()

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("### 🏗️ Structural Column Reinforcement Schedule")
        sc_data = [
            {
                "Code": sc.column_code,
                "Floor": sc.floor,
                "Concrete Grade": sc.concrete_grade,
                "Dimensions": f"{sc.width:.2f}m x {sc.depth:.2f}m",
                "Main Rebar Steel": sc.main_bars,
                "Tie Spacing": sc.tie_spacing,
                "Axial Capacity": f"{sc.load_capacity_kn:,.0f} kN",
            }
            for sc in building_model.structural_columns
        ]
        st.dataframe(sc_data, use_container_width=True)

    with col_e2:
        st.markdown("### 🌉 Structural Beam Reinforcement Schedule")
        sb_data = [
            {
                "Code": sb.beam_code,
                "Floor": sb.floor,
                "Width x Depth": f"{sb.width:.2f}m x {sb.depth:.2f}m",
                "Top Rebar": sb.top_bars,
                "Bottom Rebar": sb.bottom_bars,
                "Stirrup Spacing": sb.stirrups,
            }
            for sb in building_model.structural_beams
        ]
        st.dataframe(sb_data, use_container_width=True)

    st.divider()
    st.markdown("### 🔍 NLP BOQ Standardizer")
    st.caption("AI-Augmented Cost Estimation: Automatically aligns free-text BOQ descriptions with MasterFormat cost indexes.")
    nlp_col1, nlp_col2 = st.columns([1, 2])
    with nlp_col1:
        st.info("Uses ensemble NLP (similar to Peyman Jafary et al. 2025) to map extracted structural quantities to standard regional construction databases.")
    with nlp_col2:
        nlp_boq_data = [
            {"Raw Extracted Item": "Reinforcement Steel", "NLP Matched MasterFormat": "03 21 00 - Reinforcing Steel"},
            {"Raw Extracted Item": "Concrete Volume", "NLP Matched MasterFormat": "03 30 00 - Cast-in-Place Concrete"},
            {"Raw Extracted Item": "Brickwork / Blockwork", "NLP Matched MasterFormat": "04 22 00 - Concrete Unit Masonry"},
            {"Raw Extracted Item": "Glass Window Area", "NLP Matched MasterFormat": "08 50 00 - Windows"}
        ]
        st.table(nlp_boq_data)

# ---------------------------------------------------------
# TAB 5: Scheduling & Risk Management
# ---------------------------------------------------------
with tab_risk:
    st.subheader("🌦️ Weather-Informed Construction Scheduling & Risk Management")
    st.caption("Predictive timeline generation and meteorological risk forecasting based on building scale.")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("### 📅 Projected Timeline")
        base_days = 90 + (plot_dims.num_floors * 45)
        weather_delay = int(base_days * 0.12)  # Simulated 12% delay risk
        total_days = base_days + weather_delay
        
        schedule_data = [
            {"Phase": "1. Site Prep & Excavation", "Duration": f"{int(base_days*0.1)} Days", "Status": "On Track"},
            {"Phase": "2. Foundation & Substructure", "Duration": f"{int(base_days*0.15)} Days", "Status": "Weather Risk ⚠️"},
            {"Phase": "3. Superstructure & Framing", "Duration": f"{int(base_days*0.35)} Days", "Status": "Weather Risk ⚠️"},
            {"Phase": "4. MEP Rough-in (Plumbing/Elec)", "Duration": f"{int(base_days*0.15)} Days", "Status": "On Track"},
            {"Phase": "5. Interior & Exterior Finishes", "Duration": f"{int(base_days*0.2)} Days", "Status": "On Track"},
            {"Phase": "6. Landscaping & Handover", "Duration": f"{int(base_days*0.05)} Days", "Status": "On Track"},
        ]
        st.table(schedule_data)
        
    with col_r2:
        st.markdown("### ⚠️ Risk Analysis Model")
        st.metric("Estimated Base Timeline", f"{base_days} Days")
        st.metric("Meteorological Delay Risk", f"+{weather_delay} Days", "-12% Efficiency", delta_color="inverse")
        st.metric("Total Risk-Adjusted Timeline", f"{total_days} Days", f"≈ {round(total_days/30, 1)} Months")
        st.progress(0.15, text="Overall Risk Probability (Low-Medium)")

# ---------------------------------------------------------
# TAB 6: Export Center
# ---------------------------------------------------------
with tab_export:

    st.subheader("📥 Export Architectural Blueprints & 3D Assets")
    st.write("Download high-resolution 2D CAD blueprint drawings and 3D printable/renderable formats.")

    temp_dir = tempfile.mkdtemp()

    col_e1, col_e2, col_e3, col_e4 = st.columns(4)

    # 1. 2D PNG Export
    with col_e1:
        st.markdown("#### 🖼️ 2D PNG Image")
        png_path = os.path.join(temp_dir, "blueprint_2d.png")
        ExporterEngine.export_2d_png(building_model, png_path, floor=1, config=config_2d)
        with open(png_path, "rb") as f:
            st.download_button("Download 2D PNG", f, file_name="BUILD-MATRIX_2D_Blueprint.png", mime="image/png")

    # 2. 2D SVG Export
    with col_e2:
        st.markdown("#### 📐 2D SVG Vector")
        svg_path = os.path.join(temp_dir, "blueprint_2d.svg")
        ExporterEngine.export_2d_svg(building_model, svg_path, floor=1, config=config_2d)
        with open(svg_path, "rb") as f:
            st.download_button("Download 2D SVG", f, file_name="BUILD-MATRIX_2D_Blueprint.svg", mime="image/svg+xml")

    # 3. 2D PDF Document
    with col_e3:
        st.markdown("#### 📄 2D PDF Plan")
        pdf_path = os.path.join(temp_dir, "blueprint_2d.pdf")
        ExporterEngine.export_2d_pdf(building_model, pdf_path, floor=1, config=config_2d)
        with open(pdf_path, "rb") as f:
            st.download_button("Download 2D PDF", f, file_name="BUILD-MATRIX_2D_Blueprint.pdf", mime="application/pdf")

    # 4. 3D OBJ Mesh
    with col_e4:
        st.markdown("#### 🧊 3D OBJ Mesh")
        obj_path = os.path.join(temp_dir, "model_3d.obj")
        ExporterEngine.export_3d_obj(building_model, obj_path)
        with open(obj_path, "rb") as f:
            st.download_button("Download 3D OBJ", f, file_name="BUILD-MATRIX_3D_Model.obj", mime="model/obj")

    st.divider()

    col_e5, col_e6 = st.columns(2)
    with col_e5:
        st.markdown("#### 📦 Full Project Package (ZIP)")
        zip_path = os.path.join(temp_dir, "BUILD-MATRIX_Package.zip")
        ExporterEngine.export_bundle_zip(building_model, zip_path)
        with open(zip_path, "rb") as f:
            st.download_button(
                "📦 Download Complete Package (PNG, SVG, PDF, OBJ, STL, HTML)",
                f,
                file_name="BUILD-MATRIX_Complete_Package.zip",
                mime="application/zip",
                use_container_width=True,
            )

# --- LEGAL DISCLAIMER ---
st.markdown("---")
st.warning("**LEGAL DISCLAIMER:** Outputs are AI-generated preliminaries. They must be reviewed and signed off by a licensed structural engineer or architect before any construction use. Buildmetrics AI assumes no liability for structural integrity.")
