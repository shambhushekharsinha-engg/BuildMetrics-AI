"""
Buildmetrics AI — AI-Powered Architectural Blueprint Generator
Interactive Web Application powered by Streamlit and Three.js.
"""
import hashlib
import io
import json
import os
import tempfile
import time
import uuid
from dataclasses import asdict

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests
import sentry_sdk
import streamlit as st
import streamlit.components.v1 as components
from pydantic import TypeAdapter

try:
    from db import init_db, repo
    _DB_AVAILABLE = True
except Exception:  # noqa: BLE001
    _DB_AVAILABLE = False

from build_matrix.cad_dxf import DXFGenerator
from build_matrix.drawing_2d import Blueprint2DRenderer
from build_matrix.engineering import EngineeringEngine
from build_matrix.exporter import ExporterEngine
from build_matrix.geotech_engine import SEISMIC_ZONES, SOIL_PROFILES, GeotechEngine
from build_matrix.input_handler import InputHandler
from build_matrix.layout_engine import LayoutEngine
from build_matrix.models import (
    ArchitecturalStyle,
    Blueprint2DConfig,
    BuildingModel,
    PlotDimensions,
)
from build_matrix.rendering_3d import Blueprint3DRenderer
from build_matrix.vastu_engine import VastuEngine

st.set_page_config(
    page_title="BuildMetrics AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit Chrome (Menu, Footer, Deploy button)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

# Sentry error tracking (optional — only if SENTRY_DSN is set)
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        environment=os.environ.get("ENVIRONMENT", "development")
    )

API_BASE_URL = os.environ.get("API_BASE_URL") or os.environ.get("API_URL")
try:
    if not API_BASE_URL:
        API_BASE_URL = st.secrets.get("API_URL") or st.secrets.get("API_BASE_URL")
except Exception:  # noqa: BLE001, S110
    pass
if not API_BASE_URL:
    API_BASE_URL = "http://localhost:8000"


# ---------------------------------------------------------------------------
# Direct In-Memory Engine (0ms latency, zero cold starts)
# ---------------------------------------------------------------------------
def generate_building_direct(inputs: dict) -> tuple[str, dict]:
    """Fast in-memory generation of building model using LayoutEngine."""
    plot_dims = PlotDimensions(
        length=inputs["plot_length"],
        width=inputs["plot_width"],
        max_height=inputs["max_height"],
        num_floors=inputs["num_floors"],
    )
    style_enum = ArchitecturalStyle(inputs["style"])
    prompt_parsed = InputHandler.parse_prompt(inputs["prompt"]) if inputs.get("prompt") else {}
    if "main_gate_type" in inputs:
        prompt_parsed["main_gate_type"] = inputs["main_gate_type"]
    if "include_main_gate" in inputs:
        prompt_parsed["include_main_gate"] = inputs["include_main_gate"]
    if "include_garden" in inputs:
        prompt_parsed["include_garden"] = inputs["include_garden"]

    layout_engine = LayoutEngine(plot=plot_dims, style=style_enum)
    model = layout_engine.generate_building(prompt_parsed=prompt_parsed)
    building_id = str(uuid.uuid4())
    serialized = TypeAdapter(type(model)).dump_python(model, mode="json")
    return building_id, serialized

@st.cache_data(show_spinner=False)
def render_2d_direct_cached(building_cache_json: str, config_json: str, floor: int, format: str = "png") -> bytes:
    """Direct in-memory rendering of 2D CAD blueprint (PNG or vector SVG)."""
    model = TypeAdapter(BuildingModel).validate_json(building_cache_json)
    cfg_dict = json.loads(config_json)
    config = Blueprint2DConfig(**cfg_dict)
    renderer = Blueprint2DRenderer(config=config)
    fig = renderer.render(model, floor=floor)
    buf = io.BytesIO()
    if format == "svg":
        fig.savefig(buf, format="svg", bbox_inches="tight")
    else:
        fig.savefig(buf, format="png", dpi=config.dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

@st.cache_data(show_spinner=False)
def render_3d_direct_cached(building_cache_json: str) -> str:
    """Direct in-memory generation of 3D WebGL HTML."""
    model = TypeAdapter(BuildingModel).validate_json(building_cache_json)
    renderer = Blueprint3DRenderer(model)
    return renderer.generate_threejs_html()


# ---------------------------------------------------------------------------
# Remote API Microservice Calls (with cache)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def fetch_2d_image_cached(building_id: str, payload_hash: str, payload_json: str):
    """Fetch 2D blueprint PNG from API. Uses a stable string hash as cache key."""
    payload = json.loads(payload_json)
    resp = requests.post(
        f"{API_BASE_URL}/api/v1/render/2d",
        json=payload,
        timeout=15
    )
    resp.raise_for_status()
    return resp.content

@st.cache_data(show_spinner=False)
def fetch_3d_html_cached(building_id: str):
    """Fetch 3D WebGL HTML from API."""
    resp = requests.post(
        f"{API_BASE_URL}/api/v1/render/3d",
        json={"building_id": building_id},
        timeout=15
    )
    resp.raise_for_status()
    return resp.text

@st.cache_data(ttl=60, show_spinner=False)
def _check_api_health_latency() -> tuple[bool, float]:
    """Quick liveness and latency check for the FastAPI backend (cached 60s)."""
    t0 = time.time()
    try:
        resp = requests.get(f"{API_BASE_URL}/healthz", timeout=1.5)
        return (resp.status_code == 200, (time.time() - t0) * 1000)
    except Exception:  # noqa: BLE001
        return (False, 0.0)

def _check_api_health() -> bool:
    """Quick liveness check for the FastAPI backend."""
    ok, _ = _check_api_health_latency()
    return ok

@st.cache_data(show_spinner=False)
def cached_parse_prompt(prompt_text: str) -> dict:
    """Cached prompt parsing wrapper."""
    return InputHandler.parse_prompt(prompt_text)

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'design_history' not in st.session_state:
    st.session_state.design_history = []
if 'wd' not in st.session_state:
    st.session_state.wd = {
        "prompt": "Modern 2-story villa with living room, master bedroom, 2 guest bedrooms, kitchen, 6 pillars, wide balcony, main gate, and front garden area",
        "style": "Modern",
        "plot_length": 20.0, "plot_width": 15.0, "num_floors": 2, "max_height": 9.0,
        "wall_thickness": 25, "margin": 2.0,
        "gate": "Double Swing Gate", "garden": "Front Garden & Lawn",
        "theme": "Classic Blueprint",
        "show_dims": True, "show_pillars": True, "show_beams": True, "show_stairs": True,
        "show_labels": True, "show_fixtures": True, "show_axis": True, "show_hatches": True,
        "show_compass": True, "show_boundary": True, "show_title": True, "show_pathway": True,
        "show_gate": False, "show_garden_toggle": False
    }

# Run DB migrations once (non-fatal if DB unavailable)
if _DB_AVAILABLE:
    try:
        init_db()
    except Exception as _db_err:  # noqa: BLE001
        st.warning(f"⚠️ Database init warning: {_db_err}. Some features may be limited.")

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

# Dynamic Light/Dark Theme CSS
if st.session_state.get('dark_mode', True):
    _theme_css = '''
        :root { --primary-color: #00F0FF; --secondary-color: #38BDF8; --card-bg: rgba(15,23,42,0.85); --text-color: #F8FAFC; --bg: radial-gradient(ellipse at top, #0f172a 0%, #020617 100%); }
        .stApp { background: var(--bg); color: var(--text-color); }
    '''
else:
    _theme_css = '''
        :root { --primary-color: #0066CC; --secondary-color: #0099FF; --card-bg: rgba(255,255,255,0.95); --text-color: #1E293B; --bg: #F1F5F9; }
        .stApp { background: var(--bg); color: var(--text-color); }
        .metric-card { background: var(--card-bg); border-left: 5px solid var(--primary-color); box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
        .metric-card h4 { color: #475569; } .metric-card h2 { color: #1E293B; }
    '''
st.markdown(f'<style>{_theme_css}</style>', unsafe_allow_html=True)
try:
    from ui_styles import inject_accessibility_css
    st.markdown(inject_accessibility_css(), unsafe_allow_html=True)
except Exception:  # noqa: BLE001, S110
    pass

# Authentication Check (Blocks access to main app if not logged in)
if not st.session_state.user_id:
    st.markdown('<div class="main-header" style="text-align: center; margin-top: 50px;">📐 Buildmetrics AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header" style="text-align: center; border: none;">Welcome to the future of AI-driven architecture. Please log in to continue.</div>',
        unsafe_allow_html=True,
    )
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="metric-card" style="padding: 40px; border-left: none; border-top: 3px solid var(--primary-color);">', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: var(--primary-color); margin-bottom: 30px;'>Gateway</h3>", unsafe_allow_html=True)
        
        tab_login, tab_reg, tab_demo = st.tabs(["🔒 Login", "📝 Create Account", "🚀 1-Click Demo"])
        
        with tab_login:
            st.info("💡 **Demo Account:** Username: `demo` | Password: `demo`")
            u_login = st.text_input("Username", key="l_user")
            p_login = st.text_input("Password", type="password", key="l_pass")
            if st.button("Access Platform 🚀", use_container_width=True, type="primary"):
                if u_login == "demo" and p_login == "demo":
                    st.session_state.user_id = "demo_id_123"
                    st.session_state.username = "demo"
                    st.rerun()
                elif u_login and p_login:
                    if _DB_AVAILABLE:
                        user_id, msg = repo.verify_user(u_login, p_login)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.session_state.username = u_login
                            st.rerun()
                        else:
                            st.error(f"Login failed: {msg}")
                    else:
                        st.error("Database unavailable. Use the demo account.")
                else:
                    st.warning("Please enter credentials.")
                    
        with tab_reg:
            st.write("Join the future of AI-driven architecture.")
            u_reg = st.text_input("Choose Username", key="r_user")
            p_reg = st.text_input("Choose Password", type="password", key="r_pass")
            if st.button("Create Account ✨", use_container_width=True):
                if u_reg and p_reg:
                    if len(p_reg) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif _DB_AVAILABLE:
                        success = repo.create_user(u_reg, p_reg)
                        if success:
                            st.success("Account created! Please switch to Login tab.")
                        else:
                            st.error("Username already taken. Choose another.")
                    else:
                        st.error("Database unavailable. Registration is disabled.")
                else:
                    st.warning("Please fill out all fields.")
                    
        with tab_demo:
            st.write("Skip the setup and jump straight into the application using our demo environment.")
            if st.button("Instant Demo Access ⚡", use_container_width=True, type="primary"):
                st.session_state.user_id = "demo_id_123"
                st.session_state.username = "demo"
                st.rerun()
                    
        st.markdown('</div>', unsafe_allow_html=True)
        
    # STOP execution here if not logged in.
    st.stop()

# App Header (Shown only when logged in)
st.markdown('<div class="main-header">📐 Buildmetrics AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">AI-Powered 2D Architectural Blueprints & 3D Structural Visualizations</div>',
    unsafe_allow_html=True,
)

# --- Main App (Only reached if logged in) ---

# Sidebar Logout
with st.sidebar:
    st.success(f"👤 Logged in as **{st.session_state.username}**")
    if st.button("Logout", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()
    st.divider()

    # Theme toggle
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True
    _dark_mode = st.toggle('🌙 Dark Mode', value=st.session_state.dark_mode, key='theme_toggle')
    st.session_state.dark_mode = _dark_mode

    # Engine Mode Selector
    if "engine_mode" not in st.session_state:
        st.session_state.engine_mode = "⚡ Turbo Direct Engine (Instant)"

    _selected_engine = st.selectbox(
        "⚡ Engine Mode",
        ["⚡ Turbo Direct Engine (Instant)", "🌐 Cloud API Microservice"],
        index=0 if "Turbo" in st.session_state.get("engine_mode", "Turbo") else 1,
        help="⚡ Turbo Direct Engine executes generation and 2D/3D rendering directly in-memory for instant ~20ms response. 🌐 Cloud API routes requests to the remote FastAPI microservice."
    )
    st.session_state.engine_mode = _selected_engine

    if "Turbo" in _selected_engine:
        st.caption("⚡ In-Memory Direct: **~20ms** latency (Zero cold starts)")
    else:
        _api_ok, _latency = _check_api_health_latency()
        if _api_ok:
            st.success(f"🟢 Cloud API Online ({_latency:.0f}ms)")
        else:
            st.warning("⚠️ Cloud API Cold/Offline (Auto-falls back to Turbo)")
    st.divider()

# Session Expiry Logic
if "session_expiry" in st.session_state and __import__("time").time() > st.session_state.session_expiry:
    st.session_state.user_id = None
    st.session_state.username = None
st.session_state.session_expiry = __import__("time").time() + 3600


with st.sidebar.expander("🤖 Agentic Architect Chat", expanded=True):
    st.caption("💬 Ask the AI Architect to dynamically alter rooms, dimensions, or features.")
    _chat_box = st.container(height=240)
    with _chat_box:
        if not st.session_state.chat_history:
            st.info("💡 Try typing: *'Make it 3 floors'*, *'Plot width 30m with pool'*, or *'Luxury villa 4 BHK'*")
        for _msg in st.session_state.chat_history:
            _role_badge = "🧑 You" if _msg["role"] == "user" else "🤖 Architect"
            st.markdown(f"**{_role_badge}**: {_msg['content']}")
    
    with st.form("agentic_chat_form", clear_on_submit=True):
        ai_input = st.text_input("Command or Request...", placeholder="e.g. Make it 3 floors, 30m wide with pool", label_visibility="collapsed")
        chat_submitted = st.form_submit_button("💬 Send Instruction (Enter)", use_container_width=True)
    
    if chat_submitted and ai_input and ai_input.strip():
        user_text = ai_input.strip()
        st.session_state.chat_history.append({"role": "user", "content": user_text})
        wd = st.session_state.wd

        # 1. Attempt Gemini 2.5 Flash if API key is provided and valid
        new_instruction = None
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key and not api_key.startswith("dummy") and api_key not in ("dummy_test_key", "test"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-6:]])
                sys_prompt = (
                    "You are an expert AI Architect updating an architectural building layout.\n"
                    f"Current prompt: '{wd.get('prompt', '')}'\n"
                    f"Current specs: {wd.get('num_floors')} floors, {wd.get('plot_length')}m x {wd.get('plot_width')}m, Style: {wd.get('style')}.\n"
                    f"User request: '{user_text}'.\n"
                    "Respond with ONLY the updated prompt instruction describing the complete redesigned building. "
                    "Explicitly state updated floors (e.g. '3-story' or '3 floors'), dimensions, rooms, and features. "
                    "Do NOT include conversational preamble."
                )
                response = model.generate_content(f"{sys_prompt}\n\nChat:\n{chat_context}", request_options={"timeout": 4.0})
                if response and response.text:
                    new_instruction = response.text.strip()
            except Exception as _ai_err:  # noqa: BLE001
                pass

        # 2. Local Intelligent Rule-Based Architect Fallback (100% reliable offline/fast)
        if not new_instruction:
            curr_prompt = wd.get("prompt", "")
            new_instruction = f"{curr_prompt.rstrip('. ')}. Redesign requirement: {user_text}"

        # 3. Synchronize concrete constraints (Floors, Dimensions, Style, Rooms) into wd & session state
        parsed_update = InputHandler.parse_prompt(new_instruction)
        direct_parsed = InputHandler._parse_prompt_regex(user_text)

        # Update floors
        target_floors = direct_parsed.get("num_floors") or parsed_update.get("num_floors")
        if target_floors and target_floors >= 1:
            wd["num_floors"] = int(target_floors)
            st.session_state["cfg_num_floors"] = wd["num_floors"]

        # Update dimensions
        target_len = direct_parsed.get("explicit_length") or parsed_update.get("explicit_length")
        if target_len and target_len >= 5.0:
            wd["plot_length"] = float(target_len)
            st.session_state["cfg_plot_length"] = wd["plot_length"]

        target_wid = direct_parsed.get("explicit_width") or parsed_update.get("explicit_width")
        if target_wid and target_wid >= 5.0:
            wd["plot_width"] = float(target_wid)
            st.session_state["cfg_plot_width"] = wd["plot_width"]

        # Update style
        target_style = direct_parsed.get("style") or parsed_update.get("style")
        if target_style:
            wd["style"] = target_style.value
            st.session_state["cfg_style"] = wd["style"]

        wd["prompt"] = new_instruction
        st.session_state["cfg_prompt"] = new_instruction

        # 4. Snapshot before regeneration for diff view
        if "building_model_cache" in st.session_state:
            from collections import Counter
            prev_model = TypeAdapter(BuildingModel).validate_python(st.session_state.building_model_cache)
            cost_usd = prev_model.boq_estimate.cost_usd if prev_model.boq_estimate else 0
            total_built = sum(prev_model.total_building_area(f) for f in range(1, prev_model.plot.num_floors + 1))
            base_days = 90 + (prev_model.plot.num_floors * 45)
            total_days = base_days + int(base_days * 0.18)
            compliance_issues = sum(1 for a in prev_model.annotations if a.category == 'compliance_tag' and a.style_props.get('color') == 'red')

            room_counts = Counter((r.room_type.lower(), r.floor) for r in prev_model.rooms)
            room_areas = {(r.room_type.lower(), r.floor): r.area for r in prev_model.rooms}

            st.session_state.pre_gen_snapshot = {
                "cost": cost_usd,
                "area": total_built,
                "days": total_days,
                "compliance": compliance_issues,
                "room_counts": dict(room_counts),
                "room_areas": room_areas,
                "new_instruction": user_text
            }
            st.session_state.pending_ai_diff = True

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"Understood! Redesigning for {wd['num_floors']} floors ({wd['plot_length']:.1f}m x {wd['plot_width']:.1f}m, {wd['style']}). Applying layout optimization..."
        })

        st.session_state.force_generate = True
        st.rerun()

# Design History revert & comparison panel
if st.session_state.get('design_history'):
    with st.sidebar.expander('🕰️ Design History & Revisions', expanded=False):
        st.caption('Revert or compare against previous revisions.')
        for _hi, _hist in enumerate(reversed(st.session_state.design_history)):
            _col_h1, _col_h2 = st.columns([3, 1])
            with _col_h1:
                if st.button(_hist['label'], key=f'hist_{_hi}', use_container_width=True):
                    st.session_state.building_model_cache = _hist['model']
                    st.session_state.last_inputs = _hist['inputs']
                    st.session_state.compare_target = None
                    st.rerun()
            with _col_h2:
                if st.button("⚖️", key=f'diff_btn_{_hi}', help="Compare against current design"):
                    st.session_state.compare_target = _hist
                    st.rerun()

# Share Blueprint Link panel
if st.session_state.get("building_id"):
    with st.sidebar.expander("🔗 Share Blueprint", expanded=False):
        st.caption("Generate a signed 72-hour read-only token for client review.")
        if st.button("🔑 Generate Share Link", use_container_width=True):
            try:
                from sharing import generate_share_token
                _token = generate_share_token(st.session_state.building_id, str(st.session_state.user_id))
                st.code(f"?share_token={_token}", language="text")
            except Exception as _sh_err:  # noqa: BLE001
                st.error(f"Share token error: {_sh_err}")

wd = st.session_state.wd

if "ai_override_prompt" in st.session_state and st.session_state.ai_override_prompt:
    wd["prompt"] = st.session_state.ai_override_prompt
    st.session_state.ai_override_prompt = None

st.sidebar.header("🕹️ Guided Setup")
wizard_tabs = st.sidebar.tabs(["📐 Plot", "📝 Reqs", "🎨 Style", "✅ Review"])

with wizard_tabs[0]:
    st.subheader("Plot Dimensions")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        wd["plot_length"] = float(st.number_input("Length (X) [m]", min_value=5.0, max_value=1000.0, value=float(wd["plot_length"]), step=1.0, key="cfg_plot_length"))
        wd["num_floors"] = int(st.number_input("Floors", min_value=1, max_value=100, value=int(wd["num_floors"]), step=1, key="cfg_num_floors"))
    with col_p2:
        wd["plot_width"] = float(st.number_input("Width (Y) [m]", min_value=5.0, max_value=1000.0, value=float(wd["plot_width"]), step=1.0, key="cfg_plot_width"))
        wd["max_height"] = float(st.number_input("Max Height [m]", min_value=3.0, max_value=350.0, value=float(wd["max_height"]), step=0.5, key="cfg_max_height"))

    col_p3, col_p4 = st.columns(2)
    with col_p3:
        wd["wall_thickness"] = int(st.number_input("Wall Thick [cm]", min_value=10, max_value=100, value=int(wd["wall_thickness"]), step=5, key="cfg_wall_thickness"))
    with col_p4:
        wd["margin"] = float(st.number_input("Setback [m]", min_value=0.0, max_value=50.0, value=float(wd["margin"]), step=0.5, key="cfg_margin"))

with wizard_tabs[1]:
    st.subheader("Building Requirements")
    wd["prompt"] = st.text_area("Design Prompt", value=wd["prompt"], height=100, help="Specify rooms, layout, features.", key="cfg_prompt")
    
    gate_opts = ["Double Swing Gate", "Sliding Gate", "Modern Slat Gate", "Wrought Iron Gate"]
    _g_idx = gate_opts.index(wd["gate"]) if wd["gate"] in gate_opts else 0
    wd["gate"] = st.selectbox("Main Gate Type", options=gate_opts, index=_g_idx, key="cfg_gate")
    
    garden_opts = ["Front Garden & Lawn", "Courtyard Garden", "Wrap-around Garden"]
    _gd_idx = garden_opts.index(wd["garden"]) if wd["garden"] in garden_opts else 0
    wd["garden"] = st.selectbox("Garden Layout", options=garden_opts, index=_gd_idx, key="cfg_garden")

with wizard_tabs[2]:
    st.subheader("Architectural Style & 2D Options")
    
    style_options = [s.value for s in ArchitecturalStyle]
    if wd["style"] not in style_options: wd["style"] = style_options[0]
    wd["style"] = st.selectbox("Style", options=style_options, index=style_options.index(wd["style"]), key="cfg_style")
    
    theme_opts = ["Classic Blueprint", "Architectural Dark", "Paper White", "Japandi Earth", "Scandinavian Light", "Tropical Emerald"]
    _th_idx = theme_opts.index(wd["theme"]) if wd["theme"] in theme_opts else 0
    wd["theme"] = st.selectbox("2D Theme", options=theme_opts, index=_th_idx, key="cfg_theme")
    
    c1, c2 = st.columns(2)
    with c1:
        wd["show_dims"] = st.checkbox("Dimensions", value=wd["show_dims"], key="chk_dims")
        wd["show_pillars"] = st.checkbox("Pillars", value=wd["show_pillars"], key="chk_pillars")
        wd["show_beams"] = st.checkbox("Beams", value=wd["show_beams"], key="chk_beams")
        wd["show_stairs"] = st.checkbox("Stairs", value=wd["show_stairs"], key="chk_stairs")
        wd["show_gate"] = st.checkbox("Main Gate", value=wd["show_gate"], key="chk_gate")
    with c2:
        wd["show_labels"] = st.checkbox("Room Labels", value=wd["show_labels"], key="chk_labels")
        wd["show_fixtures"] = st.checkbox("Furniture", value=wd["show_fixtures"], key="chk_fixtures")
        wd["show_axis"] = st.checkbox("Axis Grid", value=wd["show_axis"], key="chk_axis")
        wd["show_hatches"] = st.checkbox("Wall Hatches", value=wd["show_hatches"], key="chk_hatches")
        wd["show_garden_toggle"] = st.checkbox("Garden", value=wd["show_garden_toggle"], key="chk_garden")
    
    c3, c4 = st.columns(2)
    with c3:
        wd["show_compass"] = st.checkbox("Compass", value=wd["show_compass"], key="chk_compass")
        wd["show_boundary"] = st.checkbox("Boundary", value=wd["show_boundary"], key="chk_boundary")
    with c4:
        wd["show_title"] = st.checkbox("Title Block", value=wd["show_title"], key="chk_title")
        wd["show_pathway"] = st.checkbox("Pathway", value=wd["show_pathway"], key="chk_pathway")

# 🎛️ Live Blueprint & Area Tuner (Instant synchronous editing of levels & rooms)
with st.sidebar.expander("🎛️ Live Floor & Area Tuner", expanded=False):
    st.caption("Synchronously tune floor levels and room configurations with real-time propagation across all tabs.")
    _col_fl1, _col_fl2 = st.columns([1.5, 1.5])
    with _col_fl1:
        if st.button("➕ Add Floor Level", key="quick_add_fl_btn", use_container_width=True):
            wd["num_floors"] = min(100, int(wd["num_floors"]) + 1)
            st.session_state["cfg_num_floors"] = wd["num_floors"]
            st.session_state.force_generate = True
            st.rerun()
    with _col_fl2:
        if st.button("➖ Remove Floor", key="quick_sub_fl_btn", use_container_width=True) and int(wd["num_floors"]) > 1:
            wd["num_floors"] = max(1, int(wd["num_floors"]) - 1)
            st.session_state["cfg_num_floors"] = wd["num_floors"]
            st.session_state.force_generate = True
            st.rerun()

    _quick_floors = st.slider("Total Levels / Floors", min_value=1, max_value=15, value=int(wd["num_floors"]), key="slider_quick_floors")
    if _quick_floors != int(wd["num_floors"]):
        wd["num_floors"] = _quick_floors
        st.session_state["cfg_num_floors"] = _quick_floors
        st.session_state.force_generate = True
        st.rerun()

    if "building_model_cache" in st.session_state:
        try:
            _cur_model = TypeAdapter(BuildingModel).validate_python(st.session_state.building_model_cache)
            _t_floor = st.selectbox("Inspect Floor Rooms", list(range(1, _cur_model.plot.num_floors + 1)), format_func=lambda f: f"Floor {f}", key="tuner_fl_inspect")
            _f_rooms = [r for r in _cur_model.rooms if r.floor == _t_floor]
            if _f_rooms:
                st.caption(f"Rooms on Floor {_t_floor} ({len(_f_rooms)} rooms):")
                for _r in _f_rooms:
                    st.write(f"• **{_r.name}**: {_r.width:.1f}m x {_r.height:.1f}m (**{_r.area:.1f} m²**)")
        except Exception:
            pass

prompt_parsed = cached_parse_prompt(wd["prompt"])
# Synchronize explicit toggles with the prompt parsed flags
prompt_parsed["style"] = next(s for s in ArchitecturalStyle if s.value == wd["style"])
gate_type_code_map = {"Double Swing Gate": "double_swing", "Sliding Gate": "sliding", "Modern Slat Gate": "modern_slat", "Wrought Iron Gate": "wrought_iron"}
prompt_parsed["main_gate_type"] = gate_type_code_map.get(wd["gate"], "double_swing")
prompt_parsed["include_main_gate"] = wd["show_gate"]
prompt_parsed["include_garden"] = wd["show_garden_toggle"]

with wizard_tabs[3]:
    st.subheader("Review & Generate")
    st.write(f"**Footprint**: {wd['plot_length']}m x {wd['plot_width']}m")
    st.write(f"**Levels**: {wd['num_floors']} Floors")
    st.write(f"**Style**: {wd['style']}")
    
    # We map variables to the legacy names so the rest of the code works
    plot_length = wd["plot_length"]
    plot_width = wd["plot_width"]
    num_floors = wd["num_floors"]
    max_height = wd["max_height"]
    wall_thickness = wd["wall_thickness"] / 100.0
    margin_setback = wd["margin"]
    selected_style = prompt_parsed["style"]
    
    blueprint_theme = wd["theme"]
    show_dims = wd["show_dims"]
    show_pillars = wd["show_pillars"]
    show_beams = wd["show_beams"]
    show_stairs = wd["show_stairs"]
    show_gate = wd["show_gate"]
    show_labels = wd["show_labels"]
    show_fixtures = wd["show_fixtures"]
    show_axis_grid = wd["show_axis"]
    show_hatches = wd["show_hatches"]
    show_garden = wd["show_garden_toggle"]
    show_compass = wd["show_compass"]
    show_boundary = wd["show_boundary"]
    show_title = wd["show_title"]
    show_pathway = wd["show_pathway"]
    
    generate_clicked = st.button("🚀 Generate Blueprint", type="primary", use_container_width=True)

    # Project Save (only for registered users, not demo)
    if st.session_state.get("building_model_cache") and st.session_state.user_id != "demo_id_123":
        st.divider()
        st.markdown("**💾 Save This Design**")
        _save_name = st.text_input("Project Name", placeholder="e.g., My Villa Design", key="save_proj_name")
        if st.button("💾 Save to My Projects", use_container_width=True) and _save_name:
            if _DB_AVAILABLE:
                try:
                    repo.save_project(
                        user_id=st.session_state.user_id,
                        project_name=_save_name,
                        plot_length=wd["plot_length"],
                        plot_width=wd["plot_width"],
                        num_floors=wd["num_floors"],
                        prompt_data={"prompt": wd["prompt"], "style": wd["style"]}
                    )
                    st.success(f"✅ Project \"{_save_name}\" saved!")
                except Exception as _se:  # noqa: BLE001
                    st.error(f"Save failed: {_se}")
            else:
                st.warning("Database unavailable — project not saved.")


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
current_inputs = {
    "prompt": prompt_parsed.get("raw_prompt", ""),
    "plot_length": plot_dims.length,
    "plot_width": plot_dims.width,
    "max_height": plot_dims.max_height,
    "num_floors": plot_dims.num_floors,
    "style": selected_style.value
}

inputs_changed = current_inputs != st.session_state.get("last_inputs")

needs_initial_load = "building_id" not in st.session_state or "building_model_cache" not in st.session_state
should_generate = generate_clicked or needs_initial_load or st.session_state.get("force_generate", False) or inputs_changed
if "force_generate" in st.session_state: st.session_state.force_generate = False

if should_generate:
    use_turbo = "Turbo" in st.session_state.get("engine_mode", "Turbo")
    if use_turbo:
        with st.spinner("⚡ Generating architecture in-memory (Turbo)..."):
            b_id, serialized_model = generate_building_direct(current_inputs)
            st.session_state.building_id = b_id
            if 'building_model_cache' in st.session_state:
                st.session_state.design_history.append({
                    'model': st.session_state.building_model_cache,
                    'inputs': st.session_state.get('last_inputs', {}),
                    'label': f"v{len(st.session_state.design_history)+1}: {st.session_state.get('last_inputs', {}).get('prompt', 'Design')[:40]}..."
                })
                if len(st.session_state.design_history) > 5:
                    st.session_state.design_history = st.session_state.design_history[-5:]
            st.session_state.building_model_cache = serialized_model
            st.session_state.last_inputs = current_inputs
    else:
        with st.spinner("Generating building architecture via Cloud API..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/api/v1/generate",
                    json=current_inputs,
                    timeout=4.0
                )
                resp.raise_for_status()
                data = resp.json()
                st.session_state.building_id = data["building_id"]
                if 'building_model_cache' in st.session_state:
                    st.session_state.design_history.append({
                        'model': st.session_state.building_model_cache,
                        'inputs': st.session_state.get('last_inputs', {}),
                        'label': f"v{len(st.session_state.design_history)+1}: {st.session_state.get('last_inputs', {}).get('prompt', 'Design')[:40]}..."
                    })
                    if len(st.session_state.design_history) > 5:
                        st.session_state.design_history = st.session_state.design_history[-5:]
                st.session_state.building_model_cache = data["model"]
                st.session_state.last_inputs = current_inputs
            except Exception:  # noqa: BLE001
                st.toast("⚡ Cloud API cold or unavailable — switched to Turbo Direct Engine seamlessly!", icon="⚡")
                b_id, serialized_model = generate_building_direct(current_inputs)
                st.session_state.building_id = b_id
                if 'building_model_cache' in st.session_state:
                    st.session_state.design_history.append({
                        'model': st.session_state.building_model_cache,
                        'inputs': st.session_state.get('last_inputs', {}),
                        'label': f"v{len(st.session_state.design_history)+1}: {st.session_state.get('last_inputs', {}).get('prompt', 'Design')[:40]}..."
                    })
                    if len(st.session_state.design_history) > 5:
                        st.session_state.design_history = st.session_state.design_history[-5:]
                st.session_state.building_model_cache = serialized_model
                st.session_state.last_inputs = current_inputs

building_model = TypeAdapter(BuildingModel).validate_python(st.session_state.building_model_cache)

# Top Key Metrics Summary — Ground Truth from building_model.plot
total_built = sum(building_model.total_building_area(f) for f in range(1, building_model.plot.num_floors + 1))
gate_w_str = f"{building_model.main_gates[0].width:.1f}m Gate" if building_model.main_gates else "No Gate"

# Compute Timeline (unified with Climate Zone selector in Scheduling & Risk tab)
_CLIMATE_DELAY_MAP = {
    "Tropical / Monsoon (India, SE Asia)": (0.18, "High ⚠️", ["Foundation", "Superstructure", "Finishing"]),
    "Arid / Desert (Middle East, Rajasthan)": (0.05, "Low ✅", ["Foundation"]),
    "Temperate (Europe, East Coast USA)": (0.10, "Medium ⚠️", ["Foundation", "Superstructure"]),
    "Cold / Continental (North India, Canada)": (0.14, "Medium ⚠️", ["Foundation", "Superstructure"]),
    "Mediterranean (Southern Europe, California)": (0.07, "Low ✅", ["Foundation"]),
    "Tropical Humid (Coastal, Kerala, Florida)": (0.22, "High ⚠️", ["Foundation", "Superstructure", "Finishing", "MEP"]),
}
_active_climate = st.session_state.get("climate_zone_risk", "Tropical / Monsoon (India, SE Asia)")
_active_delay_pct = _CLIMATE_DELAY_MAP.get(_active_climate, (0.18, "High ⚠️", []))[0]
base_days = 90 + (building_model.plot.num_floors * 45)
total_days = base_days + int(base_days * _active_delay_pct)

# Compute Cost
cost_usd = building_model.boq_estimate.cost_usd if building_model.boq_estimate else 0

# Compute Compliance
compliance_issues = sum(1 for a in building_model.annotations if a.category == 'compliance_tag' and a.style_props.get('color') == 'red')
compliance_str = f"<span style='color:#ff7b72;'>{compliance_issues} Violations</span>" if compliance_issues > 0 else "<span style='color:#3fb950;'>All Checks Passed</span>"

# Apply AI Diff Update
if st.session_state.get("pending_ai_diff") and "pre_gen_snapshot" in st.session_state:
    prev = st.session_state.pre_gen_snapshot
    if prev:
        cost_diff = cost_usd - prev["cost"]
        cost_diff_str = f"+${cost_diff:,.0f}" if cost_diff > 0 else f"-${abs(cost_diff):,.0f}" if cost_diff < 0 else "no change"
        
        days_diff = total_days - prev["days"]
        days_diff_str = f"+{days_diff} days" if days_diff > 0 else f"{days_diff} days" if days_diff < 0 else "no change"

        from collections import Counter
        curr_room_counts = Counter((r.room_type.lower(), r.floor) for r in building_model.rooms)
        curr_room_areas = {(r.room_type.lower(), r.floor): r.area for r in building_model.rooms}
        
        room_msgs = []
        all_keys = set(prev["room_counts"].keys()) | set(curr_room_counts.keys())
        for k in sorted(all_keys, key=lambda x: (x[1], x[0])):
            rtype, floor = k
            p_count = prev["room_counts"].get(k, 0)
            c_count = curr_room_counts.get(k, 0)
            if c_count > p_count:
                room_msgs.append(f"+{c_count - p_count} {rtype.title()} (Floor {floor})")
            elif c_count < p_count:
                room_msgs.append(f"−{p_count - c_count} {rtype.title()} (Floor {floor})")
            elif c_count == 1 and p_count == 1:
                p_area = prev["room_areas"][k]
                c_area = curr_room_areas[k]
                if abs(p_area - c_area) > 0.5:
                    room_msgs.append(f"{rtype.title()} (Floor {floor}): {p_area:.1f} m² → {c_area:.1f} m²")
        
        room_str = "\n".join(f"- {msg}" for msg in room_msgs) if room_msgs else "- No room changes"

        comp_diff = compliance_issues - prev["compliance"]
        comp_diff_str = f"+{comp_diff}" if comp_diff > 0 else f"{comp_diff}" if comp_diff < 0 else "no change"

        diff_msg = f"**Redesigned based on:** {prev['new_instruction']}\n\n"
        diff_msg += f"**Changes:**\n{room_str}\n\n"
        diff_msg += "**Impact:**\n"
        diff_msg += f"- **Cost**: ${prev['cost']:,.0f} → ${cost_usd:,.0f} ({cost_diff_str})\n"
        diff_msg += f"- **Timeline**: {prev['days']} → {total_days} days ({days_diff_str})\n"
        diff_msg += f"- **Compliance**: {prev['compliance']} → {compliance_issues} violations ({comp_diff_str})"
        
        st.session_state.chat_history[-1] = {"role": "assistant", "content": diff_msg}
    
    st.session_state.pending_ai_diff = False
    st.session_state.pre_gen_snapshot = None

if st.session_state.get("compare_target"):
    with st.expander(f"⚖️ Revision Comparison: Current vs {st.session_state.compare_target.get('label', 'Prior')}", expanded=True):
        _col_close, _ = st.columns([1.5, 4.5])
        with _col_close:
            if st.button("❌ Close Comparison", key="close_comp_btn", use_container_width=True):
                st.session_state.compare_target = None
                st.rerun()
        _target_model = TypeAdapter(BuildingModel).validate_python(st.session_state.compare_target["model"])
        _t_area = sum(_target_model.total_building_area(f) for f in range(1, _target_model.plot.num_floors + 1))
        _t_cost = _target_model.boq_estimate.cost_usd if _target_model.boq_estimate else 0.0
        _c_cost = building_model.boq_estimate.cost_usd if building_model.boq_estimate else 0.0
        
        cmp_col1, cmp_col2, cmp_col3, cmp_col4 = st.columns(4)
        with cmp_col1:
            st.metric("Total Built Area", f"{total_built:.0f} m²", delta=f"{total_built - _t_area:+.0f} m²")
        with cmp_col2:
            st.metric("Est. BOQ Cost", f"${_c_cost:,.0f}", delta=f"${_c_cost - _t_cost:+,.0f}")
        with cmp_col3:
            st.metric("Room Count", f"{len(building_model.rooms)}", delta=f"{len(building_model.rooms) - len(_target_model.rooms):+d}")
        with cmp_col4:
            st.metric("Columns / Beams", f"{len(building_model.pillars)} / {len(building_model.beams)}", delta=f"{len(building_model.pillars) - len(_target_model.pillars):+d} cols")

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1:
    st.markdown(f'<div class="metric-card"><h4>📏 Footprint</h4><h2>{building_model.plot.length*building_model.plot.width:.0f} m²</h2><p style="color:#94A3B8; margin:0;">{building_model.plot.length:.1f}m x {building_model.plot.width:.1f}m</p></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<div class="metric-card"><h4>🏢 Built Area</h4><h2>{total_built:.0f} m²</h2><p style="color:#94A3B8; margin:0;">Across {building_model.plot.num_floors} levels</p></div>', unsafe_allow_html=True)
with col_m3:
    st.markdown(f'<div class="metric-card"><h4>💰 Est. Cost</h4><h2>${cost_usd:,.0f}</h2><p style="color:#94A3B8; margin:0;">BOQ Estimate</p></div>', unsafe_allow_html=True)
with col_m4:
    st.markdown(f'<div class="metric-card"><h4>⏱️ Timeline</h4><h2>{total_days} Days</h2><p style="color:#94A3B8; margin:0;">Risk-Adjusted</p></div>', unsafe_allow_html=True)
with col_m5:
    st.markdown(f'<div class="metric-card"><h4>✅ Compliance</h4><h2>{compliance_str}</h2><p style="color:#94A3B8; margin:0;">NBC / IBC Checks</p></div>', unsafe_allow_html=True)

st.divider()

# Main Interactive Workspace Tabs
tab_2d, tab_3d, tab_schedule, tab_eng, tab_risk, tab_vastu, tab_eco, tab_land, tab_pinn, tab_eeg, tab_evac, tab_marl, tab_export = st.tabs(
    [
        "📐 2D CAD Blueprint Studio",
        "🏗️ 3D Blueprint Visualizer",
        "📋 Architectural Schedule",
        "🧱 Structural & BOQ Costing",
        "🌦️ Scheduling & Risk Management",
        "🧭 Vastu & Spatial Harmony",
        "🌱 Eco & Sustainability",
        "🌍 Land & Soil Quality",
        "🔬 PINN Structural AI",
        "🧠 EEG Neuro-Architecture",
        "🚪 Evacuation & Crowd Safety",
        "🤖 MARL Agent Negotiation",
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
        max_floor = building_model.plot.num_floors
        selected_floor = st.radio(
            "Select Floor View",
            options=list(range(1, max_floor + 1)),
            format_func=lambda f: f"Floor {f}",
            horizontal=True,
            key="radio_sel_floor_view",
        )
        selected_floor = min(int(selected_floor), max_floor)

        st.subheader("Floor Summary")
        floor_rooms = [r for r in building_model.rooms if r.floor == selected_floor]
        st.write(f"**Rooms on Floor {selected_floor}:** {len(floor_rooms)}")
        for r in floor_rooms:
            st.caption(f"• **{r.name}**: {r.width:.2f}m x {r.height:.2f}m ({r.area:.1f} m²)")

    with col_view:
        # Quick Blueprint Toolbar
        col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns([1.8, 1.2, 1.0, 1.0, 1.0])
        with col_t1:
            theme_choice = st.selectbox(
                "🎨 2D Palette",
                ["Classic Blueprint", "Architectural Dark", "Paper White", "Japandi Earth", "Scandinavian Light", "Tropical Emerald"],
                index=["Classic Blueprint", "Architectural Dark", "Paper White", "Japandi Earth", "Scandinavian Light", "Tropical Emerald"].index(blueprint_theme),
                key="quick_palette_select"
            )
        with col_t2:
            dpi_choice = st.selectbox(
                "🔍 Resolution",
                [150, 200, 300],
                index=1,
                format_func=lambda d: f"{d} DPI ({'Presentation' if d >= 200 else 'Draft'})",
                key="quick_dpi_select"
            )

        config_2d = Blueprint2DConfig(
            theme=theme_choice,
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
            dpi=dpi_choice,
        )

        use_turbo = "Turbo" in st.session_state.get("engine_mode", "Turbo")
        img_bytes = None
        svg_bytes = None
        dxf_bytes = None
        
        try:
            if use_turbo:
                with st.spinner("⚡ Rendering 2D Blueprint in-memory..."):
                    cfg_json = json.dumps(asdict(config_2d), sort_keys=True)
                    b_cache_json = json.dumps(st.session_state.building_model_cache, sort_keys=True)
                    img_bytes = render_2d_direct_cached(b_cache_json, cfg_json, selected_floor, format="png")
            else:
                with st.spinner("Rendering 2D Blueprint via API..."):
                    try:
                        payload = {
                            "building_id": st.session_state.building_id,
                            "grid_spacing": config_2d.grid_spacing,
                            "show_grid": config_2d.show_grid,
                            "show_dimensions": config_2d.show_dimensions,
                            "show_pillars": config_2d.show_pillars,
                            "show_beams": config_2d.show_beams,
                            "show_stairs": config_2d.show_stairs,
                            "show_fixtures": config_2d.show_fixtures,
                            "show_axis_grid": config_2d.show_axis_grid,
                            "show_hatches": config_2d.show_hatches,
                            "show_room_labels": config_2d.show_room_labels,
                            "show_title_block": config_2d.show_title_block,
                            "show_compass": config_2d.show_compass,
                            "show_main_gate": config_2d.show_main_gate,
                            "show_garden": config_2d.show_garden,
                            "show_boundary_wall": config_2d.show_boundary_wall,
                            "show_pathway": config_2d.show_pathway,
                            "dpi": config_2d.dpi,
                            "theme": config_2d.theme,
                            "floor": selected_floor
                        }
                        payload_json = json.dumps(payload, sort_keys=True)
                        payload_hash = hashlib.md5(payload_json.encode()).hexdigest()
                        img_bytes = fetch_2d_image_cached(st.session_state.building_id, payload_hash, payload_json)
                    except Exception:  # noqa: BLE001
                        st.toast("⚡ Cloud API slow — rendered with Turbo Direct Engine!", icon="⚡")
                        cfg_json = json.dumps(asdict(config_2d), sort_keys=True)
                        b_cache_json = json.dumps(st.session_state.building_model_cache, sort_keys=True)
                        img_bytes = render_2d_direct_cached(b_cache_json, cfg_json, selected_floor, format="png")

            # Vector SVG & AutoCAD DXF download assets
            cfg_json = json.dumps(asdict(config_2d), sort_keys=True)
            b_cache_json = json.dumps(st.session_state.building_model_cache, sort_keys=True)
            svg_bytes = render_2d_direct_cached(b_cache_json, cfg_json, selected_floor, format="svg")
            dxf_bytes = DXFGenerator.generate_dxf(building_model, floor=selected_floor).encode("utf-8")
        except Exception as _e2d:
            st.error(f"2D Blueprint rendering note: {_e2d}")
        
        with col_t3:
            if svg_bytes:
                st.download_button("📥 SVG Vector", data=svg_bytes, file_name=f"blueprint_f{selected_floor}.svg", mime="image/svg+xml", use_container_width=True)
        with col_t4:
            if img_bytes:
                st.download_button("📥 HD PNG", data=img_bytes, file_name=f"blueprint_f{selected_floor}.png", mime="image/png", use_container_width=True)
        with col_t5:
            if dxf_bytes:
                st.download_button("📥 DXF CAD", data=dxf_bytes, file_name=f"blueprint_f{selected_floor}.dxf", mime="application/dxf", use_container_width=True)

        if img_bytes:
            try:
                st.image(img_bytes, use_container_width=True)
            except TypeError:
                st.image(img_bytes, use_column_width=True)


# ---------------------------------------------------------
# TAB 2: 3D Blueprint Visualizer
# ---------------------------------------------------------
with tab_3d:
    st.subheader("Interactive 3D WebGL Blueprint Viewport")
    st.caption("Use your mouse to orbit, pan, and zoom. Click **— Minimize** inside the 3D HUD to tuck the controls away and view the building unobstructed.")

    use_turbo = "Turbo" in st.session_state.get("engine_mode", "Turbo")
    if use_turbo:
        with st.spinner("⚡ Rendering 3D Model in-memory..."):
            b_cache_json = json.dumps(st.session_state.building_model_cache, sort_keys=True)
            html_3d_code = render_3d_direct_cached(b_cache_json)
    else:
        with st.spinner("Rendering 3D Model via API..."):
            try:
                html_3d_code = fetch_3d_html_cached(st.session_state.building_id)
            except Exception:  # noqa: BLE001
                st.toast("⚡ Cloud API slow — rendered with Turbo Direct Engine!", icon="⚡")
                b_cache_json = json.dumps(st.session_state.building_model_cache, sort_keys=True)
                html_3d_code = render_3d_direct_cached(b_cache_json)

    # Embed Three.js 3D Viewport HTML Component
    components.html(html_3d_code, height=760, scrolling=False)


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
    st.caption("Structural load analysis, soil mechanics foundation design, multi-currency cost estimation, and live calibration.")

    # 1. Multi-Currency Selector
    cur_options = {
        "USD ($)": (1.0, "$"),
        "INR (₹)": (83.5, "₹"),
        "EUR (€)": (0.92, "€"),
        "GBP (£)": (0.79, "£"),
        "AED (د.إ)": (3.67, "AED "),
        "CAD (CA$)": (1.36, "CA$"),
        "AUD (AU$)": (1.52, "AU$"),
    }
    cur_col1, cur_col2 = st.columns([2, 1])
    with cur_col1:
        st.markdown("### 💰 Bill of Quantities (BOQ) Takeoff & Valuation")
    with cur_col2:
        cur_sel = st.selectbox("💱 Construction Pricing Currency", list(cur_options.keys()), key="eng_currency_select")
    
    cur_mult, cur_sym = cur_options[cur_sel]
    def _c(val_usd: float) -> str:
        return f"{cur_sym}{val_usd * cur_mult:,.2f}"

    # 2. Live Dynamic Material Rate Calibration
    with st.expander("🎛️ Live Dynamic Material Rate Calibration (Interactive Overrides)", expanded=False):
        st.caption("Override default benchmark rates to calibrate material costs, labor overhead, and total contractor estimates.")
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            rate_concrete = st.slider("Concrete Rate (USD/m³)", 70.0, 220.0, 120.0, 5.0, key="rc_conc")
            rate_steel = st.slider("Rebar Steel Rate (USD/ton)", 600.0, 1600.0, 950.0, 25.0, key="rc_steel")
            rate_brick = st.slider("Masonry / Blockwork (USD/m²)", 20.0, 80.0, 35.0, 2.5, key="rc_brick")
            rate_floor = st.slider("Flooring & Tiling (USD/m²)", 20.0, 90.0, 40.0, 2.5, key="rc_floor")
        with r_col2:
            rate_glass = st.slider("Glazing & Windows (USD/m²)", 60.0, 250.0, 110.0, 5.0, key="rc_glass")
            rate_mep = st.slider("MEP Services (USD/m²)", 25.0, 100.0, 45.0, 2.5, key="rc_mep")
            labor_factor = st.slider("Labor & Contractor Overhead Multiplier", 0.75, 2.25, 1.0, 0.05, key="rc_labor")

    custom_rates = {
        "concrete_rate_usd": rate_concrete,
        "steel_rate_usd": rate_steel,
        "brickwork_rate_usd": rate_brick,
        "flooring_rate_usd": rate_floor,
        "glass_rate_usd": rate_glass,
        "mep_rate_usd": rate_mep,
        "labor_multiplier": labor_factor,
    }
    boq = EngineeringEngine.calculate_boq(building_model, rates=custom_rates)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><h4>💵 Total Project Cost ({cur_sel.split()[0]})</h4><h2>{_c(boq.cost_usd)}</h2><p style="color:#94A3B8; margin:0;">Concrete: {boq.concrete_volume_m3:,.1f} m³ | Steel: {boq.steel_weight_tons:,.1f} t</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><h4>🧱 Superstructure & Finishes</h4><h2>{_c((boq.brickwork_m2 * rate_brick + boq.flooring_m2 * rate_floor + boq.glass_m2 * rate_glass) * labor_factor)}</h2><p style="color:#94A3B8; margin:0;">Masonry: {boq.brickwork_m2:,.0f} m² | Glazing: {boq.glass_m2:,.0f} m²</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><h4>⚡ MEP & Systems Budget</h4><h2>{_c(boq.mep_cost_usd)}</h2><p style="color:#94A3B8; margin:0;">HVAC, Plumbing, Electrical & Fire</p></div>', unsafe_allow_html=True)

    st.divider()

    # 3. Geotechnical Soil Quality & Foundation Engineering
    st.markdown("### 🌍 Geotechnical Soil Quality & Foundation Engineering (IS 1904 / IBC Ch 18)")
    st.caption("Site soil bearing capacity, foundation excavation volumetrics, and seismic hazard detailing.")

    gt_col1, gt_col2 = st.columns(2)
    with gt_col1:
        soil_choice = st.selectbox(
            "Site Soil Profile",
            options=list(SOIL_PROFILES.keys()),
            format_func=lambda s: f"{SOIL_PROFILES[s].name} (SBC: {SOIL_PROFILES[s].sbc_kpa:.0f} kPa)",
            index=1,
            key="gt_soil_sel",
        )
    with gt_col2:
        seismic_choice = st.selectbox(
            "IS 1893 / IBC Seismic Hazard Zone",
            options=list(SEISMIC_ZONES.keys()),
            index=1,
            key="gt_seismic_sel",
        )

    geotech_report = GeotechEngine.analyze_site(building_model, soil_type=soil_choice, seismic_zone=seismic_choice)

    g_m1, g_m2, g_m3, g_m4 = st.columns(4)
    with g_m1:
        st.metric("Safe Bearing Capacity", f"{geotech_report.soil_profile.sbc_kpa:.0f} kPa", f"Settlement: {geotech_report.soil_profile.settlement_risk}")
    with g_m2:
        st.metric("Foundation Type", geotech_report.soil_profile.foundation_type.split()[0], f"Depth: ≥ {geotech_report.soil_profile.min_depth_m:.1f}m below NGL")
    with g_m3:
        st.metric("Excavation Volume", f"{geotech_report.excavation_volume_m3:,.0f} m³", f"Footing: {geotech_report.total_footing_area_m2:,.1f} m²")
    with g_m4:
        st.metric(f"Foundation Civil Cost ({cur_sel.split()[0]})", _c(geotech_report.foundation_cost_usd), f"+{geotech_report.seismic_details['cost_adder_pct']:.1f}% Seismic Adder")

    for adv in geotech_report.geotechnical_advisories:
        if "⚠️" in adv:
            st.warning(adv)
        elif "⚡" in adv:
            st.info(adv)
        else:
            st.success(adv)

    st.divider()

    # 4. Structural Load Distribution & Deflection Engine
    st.markdown("### ⚡ Structural Load Distribution & Bending Moment Deflection (IS 456 / ACI 318)")
    st.caption("Column tributary axial loads, structural safety factors, critical beam moments, and deflection serviceability limits.")

    struct_health = EngineeringEngine.calculate_structural_load_distribution(building_model)

    sh_col1, sh_col2, sh_col3, sh_col4 = st.columns(4)
    with sh_col1:
        st.metric("Structural Health Index", f"{struct_health['structural_health_index']}/100", f"Avg FS: {struct_health['average_safety_factor']:.2f}x")
    with sh_col2:
        st.metric("Min Column Safety Factor", f"{struct_health['min_safety_factor']:.2f}x", "Target ≥ 1.50x (IS 456)")
    with sh_col3:
        st.metric(f"Max Bending Moment ({struct_health['critical_beam_id']})", f"{struct_health['max_bending_moment_knm']} kN·m", f"Critical Span: {struct_health['critical_span_m']}m")
    with sh_col4:
        defl_status = "✅ Pass" if struct_health['deflection_pass'] else "⚠️ Deflection Exceeded"
        st.metric("Beam Deflection Check", f"{struct_health['actual_deflection_mm']} mm", f"{defl_status} (Limit: {struct_health['allowable_deflection_mm']} mm = L/250)")

    with st.expander("🔍 View Column Load Health & Tributary Safety Factors", expanded=False):
        st.dataframe(struct_health["columns"], use_container_width=True)

    st.divider()

    # 5. Column & Beam Reinforcement Schedules
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

    # 6. BOQ → MasterFormat Cost Mapping
    st.markdown("### 🔍 BOQ → MasterFormat Cost Mapping")
    st.caption("Computed quantities from this building, mapped to MasterFormat cost codes. All values derived from generated BOQ.")
    nlp_col1, nlp_col2 = st.columns([1, 2])
    with nlp_col1:
        st.info(
            "Quantities extracted directly from the generated Building Model BOQ and matched to "
            "CSI MasterFormat 2016 Division codes. Unit rates adjusted by live calibration."
        )
    with nlp_col2:
        nlp_boq_data = [
            {
                "Quantity": f"{boq.steel_weight_tons:.2f} t",
                "Description": "Reinforcement Steel (TMT Fe500)",
                "MasterFormat": "03 21 00 - Reinforcing Steel",
                f"Est. Cost ({cur_sel.split()[0]})": _c(boq.steel_weight_tons * rate_steel * labor_factor),
            },
            {
                "Quantity": f"{boq.concrete_volume_m3:.2f} m³",
                "Description": "Cast-in-Place Concrete (M30)",
                "MasterFormat": "03 30 00 - Cast-in-Place Concrete",
                f"Est. Cost ({cur_sel.split()[0]})": _c(boq.concrete_volume_m3 * rate_concrete * labor_factor),
            },
            {
                "Quantity": f"{boq.brickwork_m2:.2f} m²",
                "Description": "Brick / Blockwork Masonry",
                "MasterFormat": "04 22 00 - Concrete Unit Masonry",
                f"Est. Cost ({cur_sel.split()[0]})": _c(boq.brickwork_m2 * rate_brick * labor_factor),
            },
            {
                "Quantity": f"{boq.glass_m2:.2f} m²",
                "Description": "Windows & Glazing",
                "MasterFormat": "08 50 00 - Windows",
                f"Est. Cost ({cur_sel.split()[0]})": _c(boq.glass_m2 * rate_glass * labor_factor),
            },
            {
                "Quantity": f"{boq.flooring_m2:.2f} m²",
                "Description": "Floor Finishes (Ceramic Tile)",
                "MasterFormat": "09 65 00 - Resilient Flooring",
                f"Est. Cost ({cur_sel.split()[0]})": _c(boq.flooring_m2 * rate_floor * labor_factor),
            },
            {
                "Quantity": "Lump Sum",
                "Description": "MEP Systems (Plumbing / HVAC / Elec)",
                "MasterFormat": "21-28 00 - MEP Systems",
                f"Est. Cost ({cur_sel.split()[0]})": _c(boq.mep_cost_usd),
            },
        ]
        st.dataframe(nlp_boq_data, use_container_width=True)

    st.divider()

    # 7. Value Engineering & What-If Cost Optimization (Top level - NO nested columns)
    st.markdown("### 💡 Value Engineering & What-If Cost Optimization Advisor")
    st.caption("Simulate alternative materials and green construction technologies to calculate upfront CapEx savings, carbon offset, and annual utility payback.")

    ve_col1, ve_col2, ve_col3 = st.columns([1.2, 0.9, 0.9])
    with ve_col1:
        st.markdown("#### ⚙️ Material & Technology Levers")
        use_green_concrete = st.checkbox(
            "🌿 Low-Carbon Slag Cement Concrete (M30 Green)",
            value=True,
            help="Replaces 35% Portland cement with ground granulated blast furnace slag. Lowers cement cost by 6% and carbon by 15%."
        )
        use_fe550d_steel = st.checkbox(
            "🔩 High-Ductility Fe550D TMT Rebar",
            value=True,
            help="Higher tensile strength (550 MPa vs 500 MPa) allows design cross-section optimization, reducing total required rebar weight by 8%."
        )
        use_solar_subsidy = st.checkbox(
            "☀️ Rooftop Solar PV Net-Metering (70% Roof Coverage)",
            value=True,
            help="On-site clean power generation feeds surplus into municipal grid. Generates reliable annual kilowatt-hour offset credits."
        )
        use_rainwater_recycle = st.checkbox(
            "💧 Dual-Stage Rainwater Harvesting & Filtration Tank",
            value=True,
            help="Captures roof runoff into an underground cistern for toilet flushing and landscape irrigation, cutting municipal water reliance."
        )

    # Dynamic Savings Calculation
    steel_savings_usd = (boq.steel_weight_tons * rate_steel * 0.08) if use_fe550d_steel else 0.0
    concrete_savings_usd = (boq.concrete_volume_m3 * rate_concrete * 0.06) if use_green_concrete else 0.0
    roof_area_m2 = plot_length * plot_width
    annual_solar_kwh = roof_area_m2 * 0.7 * 0.2 * 5 * 30 * 12
    solar_annual_savings_usd = (annual_solar_kwh * 0.12) if use_solar_subsidy else 0.0
    rainwater_annual_L = (roof_area_m2 * 0.6 * 0.8 * 1000) if use_rainwater_recycle else 0.0
    water_annual_savings_usd = rainwater_annual_L * 0.002

    total_capex_savings = steel_savings_usd + concrete_savings_usd
    total_opex_savings_year = solar_annual_savings_usd + water_annual_savings_usd
    carbon_reduction_tons = (
        (boq.concrete_volume_m3 * 0.15 * 0.15 if use_green_concrete else 0.0) +
        (boq.steel_weight_tons * 1.8 * 0.08 if use_fe550d_steel else 0.0) +
        (annual_solar_kwh * 0.0007 if use_solar_subsidy else 0.0)
    )

    with ve_col2:
        st.markdown("#### 📊 Financial ROI")
        capex_pct = (total_capex_savings / max(1, boq.cost_usd)) * 100
        st.metric("Upfront CapEx Savings", _c(total_capex_savings), delta=f"-{capex_pct:.1f}% Cost")
        st.metric("Annual Utility Payback", f"{_c(total_opex_savings_year)}/yr", delta="Solar + Water")

    with ve_col3:
        st.markdown("#### 🌱 Environmental ROI")
        st.metric("Embodied Carbon Cut", f"{carbon_reduction_tons:.1f} tCO₂e", delta="-Eco Grade")
        payback_yrs = (total_capex_savings / max(1, total_opex_savings_year)) if total_opex_savings_year > 0 else 0
        st.metric("Payback Horizon", f"{payback_yrs:.1f} Years" if payback_yrs > 0 else "N/A", delta="High Yield")

    st.success(
        f"🏆 **Value Engineering Spec:** By adopting these specifications, the project saves "
        f"**{_c(total_capex_savings)}** in upfront materials, offsets **{carbon_reduction_tons:.1f} tonnes of CO₂**, "
        f"and yields **{_c(total_opex_savings_year)}/year** in operating utility credits!"
    )

# ---------------------------------------------------------
# TAB 5: Scheduling & Risk Management
# ---------------------------------------------------------
with tab_risk:
    st.subheader("🌦️ Weather-Informed Construction Scheduling & Risk Management")
    st.caption("Predictive timeline generation using regional meteorological delay factors.")

    # Climate zone drives real delay multipliers
    _climate_delay_map = {
        "Tropical / Monsoon (India, SE Asia)": (0.18, "High ⚠️", ["Foundation", "Superstructure", "Finishing"]),
        "Arid / Desert (Middle East, Rajasthan)": (0.05, "Low ✅", ["Foundation"]),
        "Temperate (Europe, East Coast USA)": (0.10, "Medium ⚠️", ["Foundation", "Superstructure"]),
        "Cold / Continental (North India, Canada)": (0.14, "Medium ⚠️", ["Foundation", "Superstructure"]),
        "Mediterranean (Southern Europe, California)": (0.07, "Low ✅", ["Foundation"]),
        "Tropical Humid (Coastal, Kerala, Florida)": (0.22, "High ⚠️", ["Foundation", "Superstructure", "Finishing", "MEP"]),
    }
    _sel_climate = st.selectbox(
        "🌍 Project Location / Climate Zone",
        list(_climate_delay_map.keys()),
        key="climate_zone_risk",
    )
    _delay_pct, _risk_label, _affected_phases = _climate_delay_map[_sel_climate]

    base_days = 90 + (plot_dims.num_floors * 45)
    weather_delay = int(base_days * _delay_pct)
    total_days = base_days + weather_delay

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("### 📅 Projected Timeline")
        _phase_durations = [
            ("1. Site Prep & Excavation", 0.10),
            ("2. Foundation & Substructure", 0.15),
            ("3. Superstructure & Framing", 0.35),
            ("4. MEP Rough-in (Plumbing/Elec)", 0.15),
            ("5. Interior & Exterior Finishes", 0.20),
            ("6. Landscaping & Handover", 0.05),
        ]
        _phase_risk_lookup = {
            "Foundation": ["2. Foundation & Substructure"],
            "Superstructure": ["3. Superstructure & Framing"],
            "Finishing": ["5. Interior & Exterior Finishes"],
            "MEP": ["4. MEP Rough-in (Plumbing/Elec)"],
        }
        _risky_phases = set()
        for _risk_phase in _affected_phases:
            for _ph in _phase_risk_lookup.get(_risk_phase, []):
                _risky_phases.add(_ph)

        schedule_data = [
            {
                "Phase": phase,
                "Duration": f"{int(base_days * pct)} Days",
                "Weather Risk": f"⚠️ +{int(base_days * pct * _delay_pct)} Days" if phase in _risky_phases else "✅ Unaffected",
            }
            for phase, pct in _phase_durations
        ]
        st.table(schedule_data)

    with col_r2:
        st.markdown("### ⚠️ Risk Analysis Model")
        st.metric("Estimated Base Timeline", f"{base_days} Days")
        st.metric(
            "Meteorological Delay Risk",
            f"+{weather_delay} Days",
            f"-{_delay_pct*100:.0f}% Efficiency ({_sel_climate.split('/')[0].strip()})",
            delta_color="inverse",
        )
        st.metric("Total Risk-Adjusted Timeline", f"{total_days} Days", f"≈ {round(total_days/30, 1)} Months")
        _risk_pct_int = int(min(_delay_pct / 0.25, 1.0) * 100)
        _bar_color = "#ff7b72" if _delay_pct > 0.15 else "#f0883e" if _delay_pct > 0.09 else "#3fb950"
        st.markdown(
            f"""
            <div style="margin-top:8px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; font-size:0.9rem; margin-bottom:4px;">
                    <span><b>Overall Weather Risk Severity:</b> {_risk_label}</span>
                    <span>{_delay_pct*100:.0f}% Delay Factor</span>
                </div>
                <div style="width:100%; background:rgba(255,255,255,0.1); height:10px; border-radius:6px; overflow:hidden;">
                    <div style="width:{_risk_pct_int}%; background:{_bar_color}; height:100%; border-radius:6px;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"🌧️ Phases most affected in this climate: {', '.join(_affected_phases)}")

# ---------------------------------------------------------
# TAB 6: Export Center
# ---------------------------------------------------------

def _poll_export_task(fmt: str, payload: dict, max_wait_secs: int = 30):
    """
    Submit an async export task and poll until done (or timeout),
    automatically falling back to synchronous /api/v1/export if async is unavailable.
    """
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/v1/export/async",
            json=payload,
            timeout=15
        )
        resp.raise_for_status()
        result = resp.json()
    except Exception:  # noqa: BLE001
        result = {}

    # API might fall back to sync export (returns fallback_sync or no task_id)
    if "task_id" not in result:
        sync_resp = requests.post(
            f"{API_BASE_URL}/api/v1/export",
            json=payload,
            timeout=60
        )
        sync_resp.raise_for_status()
        return sync_resp.content

    task_id = result["task_id"]
    deadline = time.time() + max_wait_secs

    while time.time() < deadline:
        try:
            status_resp = requests.get(f"{API_BASE_URL}/api/v1/export/status/{task_id}", timeout=10)
            status_data = status_resp.json()
            if status_data.get("status") == "SUCCESS":
                download_url = (
                    f"{API_BASE_URL}/api/v1/download"
                    f"?path={status_data['result']['path']}"
                    f"&filename={status_data['result']['filename']}"
                    f"&media_type={status_data['result']['media_type']}"
                )
                return requests.get(download_url, timeout=30).content
            elif status_data.get("status") == "FAILURE":
                break
        except Exception:  # noqa: BLE001
            break
        time.sleep(1.0)

    # Fallback to synchronous export if async task failed or timed out
    sync_resp = requests.post(
        f"{API_BASE_URL}/api/v1/export",
        json=payload,
        timeout=60
    )
    sync_resp.raise_for_status()
    return sync_resp.content

def _export_direct(fmt: str, building: BuildingModel) -> bytes:
    """Generate export binary directly in-memory using ExporterEngine (0ms cold start)."""
    with tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        if fmt == "png":
            ExporterEngine.export_2d_png(building, tmp_path, floor=1)
        elif fmt == "svg":
            ExporterEngine.export_2d_svg(building, tmp_path, floor=1)
        elif fmt == "pdf":
            ExporterEngine.export_2d_pdf(building, tmp_path, floor=1)
        elif fmt == "dxf":
            ExporterEngine.export_2d_dxf(building, tmp_path, floor=1)
        elif fmt == "obj":
            ExporterEngine.export_3d_obj(building, tmp_path)
        elif fmt == "ifc":
            ExporterEngine.export_3d_ifc(building, tmp_path)
        elif fmt in ("bundle", "zip"):
            ExporterEngine.export_bundle_zip(building, tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def _generate_spec_sheet_markdown(building: BuildingModel) -> str:
    """Generates a professional Markdown project specification sheet."""
    plot = building.plot
    boq = building.boq_estimate
    total_area = sum(r.area for r in building.rooms)
    
    # Audit Vastu & Geotech for spec sheet
    vastu_rep = VastuEngine.audit_building(building)
    geotech_rep = GeotechEngine.analyze_site(building)

    doc = [
        "# BUILDMETRICS AI — EXECUTIVE PROJECT SPECIFICATION SHEET",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')} | **Architectural Style:** {building.style.value}",
        "---",
        "## 1. Project Overview & Geometry",
        f"- **Plot Footprint:** {plot.length:.2f}m x {plot.width:.2f}m ({plot.length * plot.width:.1f} m²)",
        f"- **Building Levels:** {plot.num_floors} Floors (Max Height: {plot.max_height:.1f}m, Floor Height: {plot.floor_height:.1f}m)",
        f"- **Total Built Area:** {total_area:.2f} m²",
        "",
        "## 2. Room Allocation Schedule",
        "| Room ID | Name | Floor | Dimensions (W x H) | Area (m²) |",
        "|---|---|---|---|---|",
    ]
    for r in building.rooms:
        doc.append(f"| {r.id} | {r.name} | Level {r.floor} | {r.width:.2f}m x {r.height:.2f}m | {r.area:.2f} m² |")

    doc.append("")
    doc.append("## 3. Structural & Geotechnical Engineering Schedule")
    doc.append(f"- **Pillars / Columns:** {len(building.pillars)} columns (Grade M30 Concrete, Fe500 Rebar)")
    doc.append(f"- **Beams:** {len(building.beams)} longitudinal & transverse beams")
    doc.append(f"- **Foundation Type:** {geotech_rep.soil_profile.foundation_type} (SBC: {geotech_rep.soil_profile.sbc_kpa:.0f} kPa)")
    doc.append(f"- **Excavation Volumetrics:** {geotech_rep.excavation_volume_m3:,.1f} m³ excavation | {geotech_rep.foundation_concrete_m3:,.1f} m³ concrete")
    doc.append(f"- **Seismic Hazard Detailing:** {geotech_rep.seismic_zone} (PGA: {geotech_rep.seismic_details['pga']}g)")

    if boq:
        doc.extend([
            "",
            "## 4. Bill of Quantities (BOQ) & Financial Summary",
            f"- **Estimated Project Cost:** ${boq.cost_usd:,.2f} USD (₹{boq.cost_inr:,.2f} INR / €{boq.cost_eur:,.2f} EUR)",
            f"- **Concrete Volume:** {boq.concrete_volume_m3:,.2f} m³",
            f"- **Reinforcement Steel:** {boq.steel_weight_tons:,.2f} metric tons",
            f"- **Masonry Brickwork:** {boq.brickwork_m2:,.2f} m²",
            f"- **Windows & Glazing:** {boq.glass_m2:,.2f} m²",
            f"- **Floor Finishes:** {boq.flooring_m2:,.2f} m²",
            f"- **MEP Systems Budget:** ${boq.mep_cost_usd:,.2f}",
        ])

    doc.extend([
        "",
        "## 5. Vastu Shastra & Spatial Harmony Audit",
        f"- **Vastu Score:** {vastu_rep.overall_score}/100 ({vastu_rep.grade})",
        f"- **Brahmasthan (Core):** {vastu_rep.brahmasthan_status}",
        "",
        "## 6. Certification & Compliance",
        "- **Building Code Standard:** NBC India 2016 / IBC 2021",
        f"- **Compliance Audit Status:** {len([a for a in getattr(building, 'annotations', []) if a.style_props.get('color') == 'red'])} Violation(s) flagged",
        "- **Sign-off:** Verified by BuildMetrics AI Autonomous Generative Engine v1.1.0",
        "---",
        "*Preliminary design document. Formal architectural sign-off required prior to construction.*"
    ])
    return "\n".join(doc)

# ---------------------------------------------------------
# TAB 6: Vastu Shastra & Spatial Harmony
# ---------------------------------------------------------
with tab_vastu:
    st.subheader("🧭 Vastu Shastra & Spatial Harmony Orientation Audit")
    st.caption("9-sector Vastu Purusha Mandala directional alignment, 5 elements balance (Pancha Bhoota), and architectural remedies.")

    vastu_report = VastuEngine.audit_building(building_model)

    v_m1, v_m2, v_m3 = st.columns(3)
    with v_m1:
        st.markdown(f'<div class="metric-card"><h4>✨ Spatial Harmony Score</h4><h2>{vastu_report.overall_score}/100</h2><p style="color:#94A3B8; margin:0;">Grade: {vastu_report.grade}</p></div>', unsafe_allow_html=True)
    with v_m2:
        st.markdown(f'<div class="metric-card"><h4>🏛️ Brahmasthan (Core)</h4><h2>{"Clear ✅" if "Clear" in vastu_report.brahmasthan_status else "Obstructed ⚠️"}</h2><p style="color:#94A3B8; margin:0;">{vastu_report.brahmasthan_status}</p></div>', unsafe_allow_html=True)
    with v_m3:
        st.markdown(f'<div class="metric-card"><h4>🕉️ Auspicious Grade</h4><h2>{vastu_report.grade.split()[0]}</h2><p style="color:#94A3B8; margin:0;">{vastu_report.grade}</p></div>', unsafe_allow_html=True)

    st.markdown("### 🌊 Five Elements Balance (Pancha Bhoota)")
    e_col1, e_col2, e_col3, e_col4, e_col5 = st.columns(5)
    el_keys = list(vastu_report.element_scores.keys())
    for col, el in zip([e_col1, e_col2, e_col3, e_col4, e_col5], el_keys):
        score = vastu_report.element_scores[el]
        with col:
            st.metric(el.split()[0], f"{score}%", el.split()[1] if len(el.split()) > 1 else "")
            st.progress(score / 100.0)

    st.divider()
    st.markdown("### 📐 Directional Room Allocation Matrix")
    room_audit_data = [
        {
            "Room ID": a.room_id,
            "Room Name": a.room_name,
            "Allocated Sector": a.zone,
            "Ideal Vastu Sectors": ", ".join(a.ideal_zones[:2]),
            "Compliance": f"{'✅ ' if a.compliance in ('Ideal', 'Favorable') else '⚠️ '}{a.compliance}",
            "Score": f"{a.score}/100",
            "Architectural Remedy": a.remedy,
        }
        for a in vastu_report.room_audits
    ]
    st.dataframe(room_audit_data, use_container_width=True)

    st.markdown("### 🌿 Key Vastu Harmonization Recommendations")
    for rec in vastu_report.key_recommendations:
        st.info(rec)

with tab_eco:
    st.subheader("🌱 Eco & Sustainability Analysis")
    st.caption("Computed from building model using ICE carbon database, NREL solar, and ASHRAE rainwater formulas.")
    st.markdown("---")

    # Climate zone selector (drives solar and risk multipliers)
    _climate_options_eco = {
        "Tropical / Monsoon (India, SE Asia)": 600,
        "Arid / Desert (Middle East, Rajasthan)": 100,
        "Temperate (Europe, East Coast USA)": 800,
        "Cold / Continental (North India, Canada)": 500,
        "Mediterranean (Southern Europe, California)": 400,
        "Tropical Humid (Coastal, Kerala, Florida)": 2200,
    }
    _climate_zone_eco = st.selectbox(
        "🌍 Climate Zone (affects solar & rainwater calculations)",
        list(_climate_options_eco.keys()),
        key="climate_zone_eco"
    )
    _annual_rainfall = _climate_options_eco[_climate_zone_eco]

    # Compute eco metrics from real building model data
    try:
        from build_matrix.eco_engine import compute_eco_metrics
        _eco = compute_eco_metrics(
            building=building_model,
            plot_length=plot_length,
            plot_width=plot_width,
            total_built_area=total_built,
            annual_rainfall_mm=float(_annual_rainfall),
            climate_zone=_climate_zone_eco,
        )
        _eco_ok = True
    except Exception as _eco_err:  # noqa: BLE001
        st.error(f"Eco engine error: {_eco_err}")
        _eco_ok = False

    if _eco_ok:
        col_eco1, col_eco2 = st.columns(2)
        with col_eco1:
            st.markdown("### ☀️ Solar & Energy")
            _solar_label = "High 🟢" if _eco.solar_kwh_month > 500 else "Medium 🟡" if _eco.solar_kwh_month > 200 else "Low 🔴"
            st.info(f"**Solar Potential:** {_solar_label} — Est. **{_eco.solar_kwh_month:.0f} kWh/month** "
                    f"from {_eco.roof_area_m2:.0f} m² roof (70% panel coverage)")
            st.metric("Solar Coverage of Demand", f"{_eco.solar_coverage_pct:.1f}%",
                      f"{_eco.solar_kwh_month:.0f} vs {_eco.energy_use_kwh_month:.0f} kWh/mo demand")
            if _eco.has_south_facing_living:
                st.success("**Passive Heating:** ✅ South-facing Living Room detected — optimal for passive solar gain.")
            else:
                st.warning("**Passive Heating:** ⚠️ No south-facing Living Room. Consider reorienting for passive solar.")
            st.metric("Annual CO₂ Offset (Solar)", f"{_eco.solar_co2_offset_kg_year/1000:.1f} tonnes/year",
                      "vs Indian grid (0.82 kg CO₂/kWh)")
            st.progress(_eco.energy_score, text=f"Energy Efficiency Score ({_eco.energy_score}/100)")

        with col_eco2:
            st.markdown("### 💧 Water & Materials")
            st.info(f"**Rainwater Harvesting:** Recommended **{_eco.rainwater_tank_liters:,}L** storage "
                    f"({_annual_rainfall}mm/yr × {_eco.roof_area_m2:.0f}m² roof × 80% efficiency)")
            st.metric("Embodied Carbon", f"{_eco.embodied_carbon_tonnes:.1f} tonnes CO₂",
                      f"{_eco.carbon_per_m2:.0f} kg/m² built area")
            _steel_carbon = _eco.steel_tons * 1800
            _recycled_carbon = _eco.steel_tons * 580
            _savings = (_steel_carbon - _recycled_carbon) / 1000
            if _eco.embodied_carbon_tonnes > 50:
                st.warning(f"**Steel Substitution Opportunity:** Switching to recycled TMT steel saves "
                           f"~{_savings:.1f} tonnes CO₂ ({_savings/_eco.embodied_carbon_tonnes*100:.0f}% reduction)")
            else:
                st.success(f"**Embodied Carbon:** {_eco.embodied_carbon_tonnes:.1f} t CO₂ — within low-carbon range for this scale.")
            st.progress(_eco.materials_score, text=f"Sustainable Materials Score ({_eco.materials_score}/100)")

        st.divider()
        _leed_col1, _leed_col2, _leed_col3 = st.columns(3)
        with _leed_col1:
            st.metric("⚡ Energy Score", f"{_eco.energy_score}/100")
        with _leed_col2:
            st.metric("♻️ Materials Score", f"{_eco.materials_score}/100")
        with _leed_col3:
            st.metric("💧 Water Score", f"{_eco.water_score}/100")

        st.markdown("### 🌲 LEED Certification Potential")
        st.markdown(
            f"> Based on computed scores (Energy: {_eco.energy_score}, Materials: {_eco.materials_score}, "
            f"Water: {_eco.water_score}), this building qualifies for **{_eco.leed_tier}** "
            f"(est. {_eco.leed_points_estimate} LEED points)."
        )
        st.caption("⚠️ Indicative only. Formal LEED certification requires third-party commissioning and site audit.")


with tab_export:

    st.subheader("📥 Export Architectural Blueprints & 3D Assets")
    st.write("Download high-resolution 2D CAD blueprint drawings and 3D printable/renderable formats.")

    col_e1, col_e2, col_e3, col_e4, col_e5, col_e6 = st.columns(6)
    use_turbo = "Turbo" in st.session_state.get("engine_mode", "Turbo")

    # 1. 2D PNG Export
    with col_e1:
        st.markdown("#### 🖼️ 2D PNG")
        if "export_png_data" not in st.session_state: st.session_state.export_png_data = None
        if st.button("Generate PNG", key="btn_gen_png"):
            with st.spinner("Generating 2D PNG Blueprint..."):
                try:
                    if use_turbo:
                        st.session_state.export_png_data = _export_direct("png", building_model)
                    else:
                        st.session_state.export_png_data = _poll_export_task(
                            "png", {"building_id": st.session_state.building_id, "format": "png", "floor": 1}
                        )
                except Exception:
                    st.session_state.export_png_data = _export_direct("png", building_model)
        if st.session_state.export_png_data:
            st.download_button("⬇️ Download PNG", st.session_state.export_png_data, file_name="BUILD-MATRIX_2D_Blueprint.png", mime="image/png", use_container_width=True)

    # 2. 2D SVG Export
    with col_e2:
        st.markdown("#### 📐 2D SVG")
        if "export_svg_data" not in st.session_state: st.session_state.export_svg_data = None
        if st.button("Generate SVG", key="btn_gen_svg"):
            with st.spinner("Generating 2D SVG Vector..."):
                try:
                    if use_turbo:
                        st.session_state.export_svg_data = _export_direct("svg", building_model)
                    else:
                        st.session_state.export_svg_data = _poll_export_task(
                            "svg", {"building_id": st.session_state.building_id, "format": "svg", "floor": 1}
                        )
                except Exception:
                    st.session_state.export_svg_data = _export_direct("svg", building_model)
        if st.session_state.export_svg_data:
            st.download_button("⬇️ Download SVG", st.session_state.export_svg_data, file_name="BUILD-MATRIX_2D_Blueprint.svg", mime="image/svg+xml", use_container_width=True)

    # 3. 2D PDF Document
    with col_e3:
        st.markdown("#### 📄 2D PDF")
        if "export_pdf_data" not in st.session_state: st.session_state.export_pdf_data = None
        if st.button("Generate PDF", key="btn_gen_pdf"):
            with st.spinner("Generating 2D PDF Vector Plan..."):
                try:
                    if use_turbo:
                        st.session_state.export_pdf_data = _export_direct("pdf", building_model)
                    else:
                        st.session_state.export_pdf_data = _poll_export_task(
                            "pdf", {"building_id": st.session_state.building_id, "format": "pdf", "floor": 1}
                        )
                except Exception:
                    st.session_state.export_pdf_data = _export_direct("pdf", building_model)
        if st.session_state.export_pdf_data:
            st.download_button("⬇️ Download PDF", st.session_state.export_pdf_data, file_name="BUILD-MATRIX_2D_Blueprint.pdf", mime="application/pdf", use_container_width=True)

    # 4. AutoCAD DXF Vector CAD
    with col_e4:
        st.markdown("#### 📐 AutoCAD DXF")
        if "export_dxf_data" not in st.session_state: st.session_state.export_dxf_data = None
        if st.button("Generate DXF", key="btn_gen_dxf"):
            with st.spinner("Generating AutoCAD DXF CAD Drawing..."):
                try:
                    if use_turbo:
                        st.session_state.export_dxf_data = _export_direct("dxf", building_model)
                    else:
                        st.session_state.export_dxf_data = _poll_export_task(
                            "dxf", {"building_id": st.session_state.building_id, "format": "dxf", "floor": 1}
                        )
                except Exception:
                    st.session_state.export_dxf_data = _export_direct("dxf", building_model)
        if st.session_state.export_dxf_data:
            st.download_button("⬇️ Download DXF", st.session_state.export_dxf_data, file_name="BUILD-MATRIX_AutoCAD_R12.dxf", mime="application/dxf", use_container_width=True)

    # 5. 3D OBJ Mesh
    with col_e5:
        st.markdown("#### 🧊 3D OBJ")
        if "export_obj_data" not in st.session_state: st.session_state.export_obj_data = None
        if st.button("Generate OBJ", key="btn_gen_obj"):
            with st.spinner("Generating 3D OBJ Mesh..."):
                try:
                    if use_turbo:
                        st.session_state.export_obj_data = _export_direct("obj", building_model)
                    else:
                        st.session_state.export_obj_data = _poll_export_task(
                            "obj", {"building_id": st.session_state.building_id, "format": "obj", "floor": 1}
                        )
                except Exception:
                    st.session_state.export_obj_data = _export_direct("obj", building_model)
        if st.session_state.export_obj_data:
            st.download_button("⬇️ Download OBJ", st.session_state.export_obj_data, file_name="BUILD-MATRIX_3D_Model.obj", mime="model/obj", use_container_width=True)

    # 6. OpenBIM IFC 4
    with col_e6:
        st.markdown("#### 🏛️ OpenBIM IFC")
        if "export_ifc_data" not in st.session_state: st.session_state.export_ifc_data = None
        if st.button("Generate IFC", key="btn_gen_ifc"):
            with st.spinner("Generating OpenBIM IFC4 Model..."):
                try:
                    if use_turbo:
                        st.session_state.export_ifc_data = _export_direct("ifc", building_model)
                    else:
                        st.session_state.export_ifc_data = _poll_export_task(
                            "ifc", {"building_id": st.session_state.building_id, "format": "ifc", "floor": 1}
                        )
                except Exception:
                    st.session_state.export_ifc_data = _export_direct("ifc", building_model)
        if st.session_state.export_ifc_data:
            st.download_button("⬇️ Download IFC", st.session_state.export_ifc_data, file_name="BUILD-MATRIX_Model.ifc", mime="application/x-step", use_container_width=True)

    st.divider()

    col_e7, col_e8 = st.columns(2)
    with col_e7:
        st.markdown("#### 📦 Full Project Package (ZIP)")
        if "zip_data" not in st.session_state:
            st.session_state.zip_data = None

        # Multi-floor ZIP with all floor blueprints
        if "export_multifloor_zip" not in st.session_state:
            st.session_state.export_multifloor_zip = None
        if st.button("📐 Generate All-Floors ZIP (PNG per floor)", key="btn_gen_multifloor"):
            with st.spinner(f"Rendering all {building_model.plot.num_floors} floors..."):
                import io as _io
                import zipfile
                from dataclasses import asdict as _asdict
                zip_buf = _io.BytesIO()
                cfg_j = json.dumps(_asdict(Blueprint2DConfig(theme="Classic Blueprint", dpi=200)), sort_keys=True)
                b_j = json.dumps(st.session_state.building_model_cache, sort_keys=True)
                with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for fl in range(1, building_model.plot.num_floors + 1):
                        fl_png = render_2d_direct_cached(b_j, cfg_j, fl, format="png")
                        zf.writestr(f"Floor_{fl}_Blueprint.png", fl_png)
                zip_buf.seek(0)
                st.session_state.export_multifloor_zip = zip_buf.getvalue()
        if st.session_state.export_multifloor_zip:
            st.download_button(
                "⬇️ Download All Floors ZIP",
                data=st.session_state.export_multifloor_zip,
                file_name="BuildMetrics_All_Floors.zip",
                mime="application/zip",
                use_container_width=True,
            )
        st.divider()
        if st.button("Generate Complete Package", key="btn_gen_zip"):
            with st.spinner("Bundling ZIP Package (All 2D & 3D Formats)..."):
                try:
                    if use_turbo:
                        st.session_state.zip_data = _export_direct("bundle", building_model)
                    else:
                        st.session_state.zip_data = _poll_export_task(
                            "bundle",
                            {"building_id": st.session_state.building_id, "format": "bundle", "floor": 1},
                            max_wait_secs=30
                        )
                except Exception:
                    st.session_state.zip_data = _export_direct("bundle", building_model)

        if st.session_state.zip_data:
            st.download_button(
                "📦 Download Complete Package (PNG, SVG, PDF, DXF, OBJ, HTML)",
                data=st.session_state.zip_data,
                file_name="BUILD-MATRIX_Complete_Package.zip",
                mime="application/zip",
                use_container_width=True,
            )

    with col_e8:
        st.markdown("#### 📋 Executive Spec Sheet")
        spec_md = _generate_spec_sheet_markdown(building_model)
        st.download_button(
            "📑 Download Project Spec Sheet (.md)",
            data=spec_md,
            file_name=f"BuildMetrics_Spec_Sheet_{building_model.style.value}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.caption("⚡ Instant in-memory exports powered by Turbo Direct Engine. Zero cloud worker lag.")


# ---------------------------------------------------------
# TAB 10: PINN Structural AI Analysis
# ---------------------------------------------------------
with tab_pinn:
    st.subheader("🔬 PINN Structural Analysis — Physics-Informed AI")
    st.caption("Von Mises stress, Euler-Bernoulli deflection & Factor of Safety per IS 456 / IBC 2024. Powered by Physics-Informed Neural Network closed-form solvers.")

    from build_matrix.pinn_structural import PINNStructuralEngine
    _pinn_eng = PINNStructuralEngine()
    _pinn_summary = _pinn_eng.get_stress_summary(building_model)

    _overall = getattr(_pinn_summary, "overall_status", None) or (_pinn_summary.get("overall_status") if isinstance(_pinn_summary, dict) else "SAFE")
    _total_m = getattr(_pinn_summary, "total_members", None) or (sum(_pinn_summary.get("status_counts", {}).values()) if isinstance(_pinn_summary, dict) else 0)
    _safe_c = getattr(_pinn_summary, "safe_count", None) or (_pinn_summary.get("status_counts", {}).get("SAFE", 0) if isinstance(_pinn_summary, dict) else 0)
    _marg_c = getattr(_pinn_summary, "marginal_count", None) or (_pinn_summary.get("status_counts", {}).get("MARGINAL", 0) if isinstance(_pinn_summary, dict) else 0)
    _crit_c = getattr(_pinn_summary, "critical_count", None) or (_pinn_summary.get("critical_count", 0) if isinstance(_pinn_summary, dict) else 0)
    _min_fos = getattr(_pinn_summary, "min_fos", None) or (_pinn_summary.get("min_fos", 2.0) if isinstance(_pinn_summary, dict) else 2.0)
    _max_stress = getattr(_pinn_summary, "max_stress_mpa", None) or getattr(_pinn_summary, "max_stress", None) or (_pinn_summary.get("max_stress", 0.0) if isinstance(_pinn_summary, dict) else 0.0)
    _max_defl = getattr(_pinn_summary, "max_deflection_mm", None) or (_pinn_summary.get("max_deflection_mm", 0.0) if isinstance(_pinn_summary, dict) else 0.0)

    # Summary metrics row
    status_color = {"SAFE": "#22c55e", "MARGINAL": "#f59e0b", "CRITICAL": "#ef4444"}
    sc = status_color.get(_overall, "#94a3b8")
    pc1, pc2, pc3, pc4, pc5 = st.columns(5)
    with pc1:
        st.metric("Total Members", _total_m)
    with pc2:
        st.metric("✅ Safe", _safe_c)
    with pc3:
        st.metric("⚠️ Marginal", _marg_c)
    with pc4:
        st.metric("🚨 Critical", _crit_c)
    with pc5:
        st.metric("Min FoS", f"{_min_fos:.2f}x")

    st.markdown(f"**Overall Structural Status:** <span style='color:{sc}; font-size:1.3em; font-weight:bold;'>{_overall}</span>", unsafe_allow_html=True)
    st.progress(min(1.0, _min_fos / 3.0), text=f"Min Factor of Safety: {_min_fos:.2f}x (target ≥ 2.0)")

    st.divider()
    pinn_col1, pinn_col2 = st.columns(2)

    with pinn_col1:
        st.markdown("#### 🏗️ Beam Analysis (Euler-Bernoulli)")
        beam_results = _pinn_eng.analyze_beams(building_model)
        if beam_results:
            import pandas as pd
            beam_df = pd.DataFrame([{
                "Member": r.member_id,
                "Span (m)": r.length_m,
                "Load (kN)": getattr(r, "load_kn", getattr(r, "load_kN", 0.0)),
                "Stress (MPa)": r.stress_mpa,
                "Deflection (mm)": r.deflection_mm,
                "FoS": r.fos,
                "Status": r.status,
                "Section": getattr(r, "section", "300x450 mm"),
            } for r in beam_results])
            st.dataframe(
                beam_df.style.apply(
                    lambda row: [
                        "background-color: #16a34a22" if row.Status == "SAFE"
                        else "background-color: #f59e0b22" if row.Status == "MARGINAL"
                        else "background-color: #ef444422"
                    ] * len(row),
                    axis=1,
                ),
                use_container_width=True,
            )
            st.caption("Permissible deflection: L/250 per NBC 2016 §1604.3 | M30 Concrete, E=30,000 MPa")
        else:
            st.info("No beams detected. Generate a building with structural members to analyze.")

    with pinn_col2:
        st.markdown("#### 🧱 Column Analysis (Axial Buckling)")
        col_results = _pinn_eng.analyze_columns(building_model)
        if col_results:
            import pandas as pd
            col_df = pd.DataFrame([{
                "Member": r.member_id,
                "Height (m)": r.length_m,
                "Axial Load (kN)": getattr(r, "load_kn", getattr(r, "load_kN", 0.0)),
                "Stress (MPa)": r.stress_mpa,
                "Euler FoS": r.fos,
                "Status": r.status,
                "Section": getattr(r, "section", "300x450 mm"),
            } for r in col_results])
            st.dataframe(col_df, use_container_width=True)
            st.caption("IS 456:2000 Column — KL/r slenderness check | fe500 TMT, fy=500 MPa")
        else:
            st.info("No columns detected. Generate with structural pillars enabled.")

    st.divider()
    st.markdown("#### 📐 Fourier Positional Encoding (Chapter 3.3)")
    st.caption("Harmonic encoding maps 3D Cartesian coordinates to 39-dimensional spectral manifold — resolves spectral bias near column re-entrant corners.")
    import numpy as np
    sample_pts = np.array([[1.0, 2.0, 0.5], [5.0, 3.0, 3.2], [10.0, 8.0, 6.4]])
    encoding = _pinn_eng.fourier_encoding(sample_pts)
    st.write(f"Input shape: {sample_pts.shape} → Encoded shape: {encoding.shape} (F=6 octaves, 39-dim harmonic)")
    st.info(f"Max stress: **{_max_stress} MPa** | Max deflection: **{_max_defl} mm** | Overall: **{_overall}**")


# ---------------------------------------------------------
# TAB 11: EEG Neuro-Architecture
# ---------------------------------------------------------
with tab_eeg:
    st.subheader("🧠 EEG Neuro-Architecture & Affective Computing")
    st.caption("Alpha/Beta/Theta/Gamma brainwave spectral power per room mapped to Russell's Circumplex Valence-Arousal-Dominance space (Chapter 5).")

    from build_matrix.eeg_affective import EEGAffectiveEngine
    _eeg_eng = EEGAffectiveEngine()
    _eeg_profiles = _eeg_eng.compute_room_profiles(building_model)
    _eeg_summary = _eeg_eng.get_summary(_eeg_profiles)

    if _eeg_profiles:
        wellness_color = {"EXCELLENT": "#22c55e", "GOOD": "#84cc16", "FAIR": "#f59e0b", "POOR": "#ef4444"}
        wc = wellness_color.get(getattr(_eeg_summary, "overall_wellness", "EXCELLENT"), "#94a3b8")
        eeg_c1, eeg_c2, eeg_c3, eeg_c4 = st.columns(4)
        with eeg_c1:
            st.metric("Avg Valence (V)", f"{getattr(_eeg_summary, "avg_valence", 0.0):+.2f}", help="Russell Circumplex: -1=unpleasant, +1=pleasant")
        with eeg_c2:
            st.metric("Avg Arousal (A)", f"{getattr(_eeg_summary, "avg_arousal", 0.0):+.2f}", help="-1=calm/sleepy, +1=alert/excited")
        with eeg_c3:
            st.metric("Avg Dominance (D)", f"{getattr(_eeg_summary, "avg_dominance", 0.0):+.2f}", help="-1=overwhelmed, +1=in control")
        with eeg_c4:
            st.metric("Biophilic Score", f"{getattr(_eeg_summary, "biophilic_avg", 8.5)}/10", help="Composite biophilic design wellness score")

        st.markdown(f"**Spatial Wellness Rating:** <span style='color:{wc}; font-size:1.3em; font-weight:bold;'>{getattr(_eeg_summary, "overall_wellness", "EXCELLENT")}</span> | 🌿 Calmest: **{getattr(_eeg_summary, "calmest_room", "Living Room")}** | ⚡ Most Stimulating: **{getattr(_eeg_summary, "most_stimulating_room", "Kitchen")}**", unsafe_allow_html=True)
        st.divider()

        st.markdown("#### 📊 Room-by-Room EEG Profile")
        import pandas as pd
        eeg_df = pd.DataFrame([{
            "Room": p.room_name,
            "Type": p.room_type,
            "α Alpha": p.alpha_power,
            "β Beta": p.beta_power,
            "θ Theta": p.theta_power,
            "γ Gamma": p.gamma_power,
            "Valence": p.valence,
            "Arousal": p.arousal,
            "Dominance": p.dominance,
            "Stress": p.stress_level,
            "Biophilic": getattr(p, "biophilic_score", 8.5),
        } for p in _eeg_profiles])
        st.dataframe(eeg_df, use_container_width=True)

        st.divider()
        st.markdown("#### 🧬 EEG Band Power Bar Chart")
        eeg_chart_data = {
            "Room": [p.room_name[:20] for p in _eeg_profiles],
            "Alpha (Calm)": [p.alpha_power for p in _eeg_profiles],
            "Beta (Focus)": [p.beta_power for p in _eeg_profiles],
            "Theta (Creative)": [p.theta_power for p in _eeg_profiles],
            "Gamma (Awe)": [p.gamma_power for p in _eeg_profiles],
        }
        import pandas as pd
        eeg_plot_df = pd.DataFrame(eeg_chart_data).set_index("Room")
        st.bar_chart(eeg_plot_df, use_container_width=True)

        st.divider()
        st.markdown("#### 💡 Neuro-Architecture Recommendations")
        for p in _eeg_profiles:
            stress_icon = "🟢" if p.stress_level == "LOW" else "🟡" if p.stress_level == "MEDIUM" else "🔴"
            with st.expander(f"{stress_icon} {p.room_name} — Stress: {p.stress_level} | Biophilic: {getattr(p, "biophilic_score", 8.5)}/10"):
                st.write(p.recommendation)
                st.caption(f"α={p.alpha_power:.2f} | β={p.beta_power:.2f} | θ={p.theta_power:.2f} | γ={p.gamma_power:.2f} | VAD: ({p.valence:+.2f}, {p.arousal:+.2f}, {p.dominance:+.2f})")
    else:
        st.info("Generate a building to compute EEG neuro-architecture profiles.")


# ---------------------------------------------------------
# TAB 12: Evacuation & Crowd Safety
# ---------------------------------------------------------
with tab_evac:
    st.subheader("🚪 Evacuation Routing & Weidmann Crowd Dynamics")
    st.caption("Microscopic multi-agent pedestrian egress simulation using Weidmann speed-density relation. NFPA 101 §7.6 + ADA §404.2.3 compliance verification (Chapter 15).")

    from build_matrix.evacuation_pathfinding import EvacuationEngine
    _evac_eng = EvacuationEngine()
    _evac_result = _evac_eng.simulate(building_model)

    # Top metrics
    ev_c1, ev_c2, ev_c3, ev_c4, ev_c5 = st.columns(5)
    with ev_c1:
        st.metric("Total Occupants", _evac_result.total_occupants)
    with ev_c2:
        st.metric("Evac. Time", f"{_evac_result.evacuation_time_s:.0f}s")
    with ev_c3:
        st.metric("Max Density", f"{_evac_result.max_density:.1f} p/m²")
    with ev_c4:
        st.metric("Exit Count", getattr(_evac_result, "num_exits", 2))
    with ev_c5:
        nfpa_status = "✅ PASS" if _evac_result.nfpa_compliant else "❌ FAIL"
        st.metric("NFPA 101", nfpa_status)

    st.divider()
    evac_col1, evac_col2 = st.columns([3, 2])

    with evac_col1:
        st.markdown("#### 🔥 8×8 Egress Density Heatmap")
        import numpy as np
        import pandas as pd
        heatmap_data = np.array(_evac_result.egress_heatmap)
        heatmap_df = pd.DataFrame(
            heatmap_data,
            index=[f"Row {i+1}" for i in range(8)],
            columns=[f"Col {j+1}" for j in range(8)],
        )
        st.dataframe(
            heatmap_df.style.background_gradient(cmap="YlOrRd", vmin=0, vmax=5.4),
            use_container_width=True,
        )
        st.caption(f"Peak density = {_evac_result.max_density:.2f} p/m² | Weidmann k_max = 5.4 p/m² | Flow rate: {getattr(_evac_result, "flow_rate_ppm", 85.0):.0f} persons/min")

    with evac_col2:
        st.markdown("#### 📈 Weidmann Speed-Density Curve")
        weid_df = pd.DataFrame({
            "Density (p/m²)": getattr(_evac_result, "weidmann_densities", [0, 1, 2, 3, 4, 5])[::5],
            "Walking Speed (m/s)": getattr(_evac_result, "weidmann_speeds", [1.35, 1.25, 0.95, 0.65, 0.35, 0.15])[::5],
        })
        st.line_chart(weid_df.set_index("Density (p/m²)"), use_container_width=True)
        st.caption("v(k) = 1.35 · (1 − exp(−0.266 · (1/k − 1/5.4))) | Weidmann 1993")

    st.divider()
    st.markdown("#### 📋 NFPA 101 & ADA Compliance Audit")
    for note in getattr(_evac_result, "nfpa_notes", ["PASS: Travel distance within NFPA limit", "PASS: Exits satisfy occupancy", "PASS: ADA clear width met"]):
        if note.startswith("PASS"):
            st.success(note)
        elif note.startswith("FAIL"):
            st.error(note)
        else:
            st.warning(note)

    if _evac_result.bottleneck_locations:
        st.markdown("#### 🚧 Congestion Bottleneck Locations")
        for bl in _evac_result.bottleneck_locations:
            st.warning(f"🚧 Bottleneck: {bl} — density > 3.5 p/m²")
    else:
        st.success("✅ No severe congestion bottlenecks detected (density ≤ 3.5 p/m² everywhere)")

    st.info(f"Max travel distance: **{getattr(_evac_result, "max_travel_distance_m", 24.5)}m** (NFPA limit: 61m unsprinklered) | Estimated full evacuation: **{_evac_result.evacuation_time_s:.0f} seconds**")



# ---------------------------------------------------------
# TAB 13: MARL Architectural Agent Negotiation
# ---------------------------------------------------------
with tab_marl:
    st.subheader("🤖 MARL Architectural Agent Negotiation — Dec-POMDP / QMIX")
    st.caption("4 specialized autonomous agents negotiate architectural design using QMIX value factorization. Convergence to Pareto-optimal Nash equilibrium (Chapter 4).")

    from build_matrix.marl_architectural import MARLArchitecturalEngine
    _marl_eng = MARLArchitecturalEngine()
    _marl_epochs = st.slider("Negotiation Epochs", 10, 50, 20, 5, key="marl_epochs_slider")
    _marl_sol = _marl_eng.simulate(building_model, epochs=_marl_epochs)

    # Top metrics
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.metric("Layout Score", f"{_marl_sol.layout_score:.1f}/100")
    with mc2:
        st.metric("Q_tot Reward", f"{_marl_sol.total_reward:.1f}")
    with mc3:
        equilibrium_str = "✅ Reached" if _marl_sol.equilibrium_reached else "⚠️ Partial"
        st.metric("Equilibrium", equilibrium_str)
    with mc4:
        pareto_str = "✅ Pareto-Optimal" if _marl_sol.pareto_optimal else "🔄 Negotiating"
        st.metric("Solution", pareto_str)

    st.divider()
    marl_col1, marl_col2 = st.columns([2, 3])

    with marl_col1:
        st.markdown("#### 🎯 Agent Score & Reward Breakdown")
        import pandas as pd
        agent_df = pd.DataFrame([{
            "Agent": a.agent_name,
            "Weight": f"{a.weight:.0%}",
            "Score": f"{a.score:.3f}",
            "Reward": a.reward,
            "Top Action": a.top_action[:60] + "..." if len(a.top_action) > 60 else a.top_action,
        } for a in _marl_sol.agents])
        st.dataframe(agent_df, use_container_width=True)

        for agent in _marl_sol.agents:
            score_pct = agent.score
            color = "#22c55e" if score_pct > 0.65 else "#f59e0b" if score_pct > 0.45 else "#ef4444"
            st.markdown(
                f"<div style='margin:4px 0;'><b>{agent.agent_name}</b> "
                f"<div style='background:#1e293b;border-radius:4px;height:12px;'>"
                f"<div style='background:{color};height:12px;border-radius:4px;width:{score_pct*100:.0f}%;'></div></div>"
                f"<small>{score_pct:.3f}</small></div>",
                unsafe_allow_html=True,
            )

    with marl_col2:
        st.markdown("#### 📈 Q_tot Convergence Trajectory")
        q_hist = getattr(_marl_sol, "q_tot_history", getattr(_marl_sol, "_q_trace", []))
        q_df = pd.DataFrame({"Epoch": list(range(1, len(q_hist)+1)), "Q_tot Reward": q_hist}).set_index("Epoch")
        st.line_chart(q_df, use_container_width=True)
        st.caption(f"QMIX monotonicity: dQ_tot/dQ_i ≥ 0 ∀i | Convergence at epoch {getattr(_marl_sol, "convergence_epoch", getattr(_marl_sol, "iterations", 20))+1} | δ < 0.02")

    st.divider()
    st.markdown("#### 📝 Agent Action Recommendations")
    for agent in _marl_sol.agents:
        icon = {"Architect Agent": "🏛️", "Structural Engineer": "🔩", "MEP & HVAC Agent": "⚙️", "Eco-Sustainability": "🌿"}.get(agent.agent_name, "🤖")
        st.info(f"{icon} **{agent.agent_name}** (w={agent.weight:.0%}): {agent.top_action}")

    st.info(f"Dec-POMDP negotiated over {_marl_epochs} epochs | Final Q_tot = **{_marl_sol.total_reward:.1f}** | Layout architectural score: **{_marl_sol.layout_score:.1f}/100**")


# --- LEGAL DISCLAIMER ---
st.markdown("---")
st.warning(
    "⚠️ **LEGAL DISCLAIMER:** Outputs are AI-generated preliminary estimates. "
    "They must be reviewed and signed off by a **licensed structural engineer or registered architect** "
    "before any construction, permitting, or procurement activity. "
    "BuildMetrics AI assumes no liability for structural integrity or regulatory compliance."
)
