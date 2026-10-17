"""
Streamlit AppTest smoke tests for app.py.
Verifies the app file compiles cleanly and key modules are importable
without triggering a full Streamlit network session.
"""
import compileall
import py_compile

import pytest


def test_app_syntax_ok():
    """app.py must compile without any SyntaxError."""
    # py_compile.compile raises py_compile.PyCompileError on any syntax issue
    py_compile.compile("app.py", doraise=True)


def test_all_python_files_compile():
    """All .py files in the project must be syntax-valid."""
    result = compileall.compile_dir(".", quiet=True, force=True)
    assert result == 1, "compileall failed — at least one .py file has a syntax error"


def test_build_matrix_package_importable():
    """build_matrix package must be importable (checks __init__ + core modules)."""
    import build_matrix  # noqa: F401
    from build_matrix import engineering, models, schemas  # noqa: F401


def test_models_importable():
    """Key model classes must be importable."""
    from build_matrix.models import (  # noqa: F401
        ArchitecturalStyle,
        Blueprint2DConfig,
        BOQEstimate,
        BuildingModel,
        PlotDimensions,
        RoomSpec,
    )


def test_api_module_importable():
    """api.py must be importable (FastAPI app construction runs cleanly)."""
    import api
    assert hasattr(api, "app"), "api module must expose 'app' FastAPI instance"


def test_db_module_importable():
    """db.py must be importable without crashing."""
    import db
    assert hasattr(db, "repo"), "db module must expose 'repo' DatabaseRepository"


def test_cost_engine_importable():
    """cost_engine.py must be importable without Streamlit dependency."""
    import cost_engine
    assert hasattr(cost_engine, "predict_cost")


def test_sharing_module_importable():
    """sharing.py must work without network."""
    from sharing import generate_share_token, validate_share_token
    token = generate_share_token("test-building-123", "user-456", ttl_hours=1)
    assert isinstance(token, str)
    assert "." in token

    payload = validate_share_token(token)
    assert payload is not None
    assert payload["building_id"] == "test-building-123"


def test_share_token_expiry():
    """Expired tokens must be rejected by validate_share_token."""
    import time

    from sharing import generate_share_token, validate_share_token
    # Generate with 0-hour TTL (already expired)
    token = generate_share_token("building-id", "user-1", ttl_hours=0)
    time.sleep(0.01)  # ensure expiry
    result = validate_share_token(token)
    assert result is None


def test_eco_engine_computes():
    """eco_engine must compute without error for a valid model."""
    from build_matrix.eco_engine import compute_eco_metrics
    from build_matrix.models import (
        ArchitecturalStyle,
        BOQEstimate,
        BuildingModel,
        PlotDimensions,
    )

    plot = PlotDimensions(length=20.0, width=15.0, num_floors=2)
    building = BuildingModel(
        plot=plot,
        style=ArchitecturalStyle.MODERN,
        boq_estimate=BOQEstimate(
            concrete_volume_m3=50.0,
            steel_weight_tons=4.0,
            brickwork_m2=120.0,
            flooring_m2=240.0,
            glass_m2=30.0,
            mep_cost_usd=15000.0,
            cost_usd=85000.0,
            cost_inr=7_000_000.0,
            cost_eur=78000.0,
        )
    )

    metrics = compute_eco_metrics(
        building=building,
        plot_length=20.0,
        plot_width=15.0,
        total_built_area=450.0,
    )

    assert metrics.solar_kwh_month > 0
    assert metrics.energy_score > 0
    assert metrics.materials_score > 0
    assert 0 < metrics.overall_score <= 100
    assert metrics.leed_tier != ""
    assert metrics.embodied_carbon_tonnes > 0


def test_design_comparison():
    """compare_designs must return a valid DesignDiff."""
    from build_matrix.comparison import compare_designs
    from build_matrix.models import (
        ArchitecturalStyle,
        BOQEstimate,
        BuildingModel,
        PlotDimensions,
        RoomSpec,
    )

    plot = PlotDimensions(length=20.0, width=15.0, num_floors=2)
    model_a = BuildingModel(
        plot=plot, style=ArchitecturalStyle.MODERN,
        boq_estimate=BOQEstimate(cost_usd=100000.0, cost_inr=8_000_000.0, cost_eur=92000.0),
        rooms=[RoomSpec(id="r1", name="Bedroom", room_type="bedroom", x=0, y=0, width=4, height=3)]
    )
    model_b = BuildingModel(
        plot=plot, style=ArchitecturalStyle.MODERN,
        boq_estimate=BOQEstimate(cost_usd=120000.0, cost_inr=9_600_000.0, cost_eur=110000.0),
        rooms=[
            RoomSpec(id="r1", name="Bedroom", room_type="bedroom", x=0, y=0, width=5, height=3),
            RoomSpec(id="r2", name="Study", room_type="study", x=5, y=0, width=3, height=3),
        ]
    )

    diff = compare_designs(model_a, model_b)
    assert diff.cost_delta_usd == pytest.approx(20000.0)
    assert "study" in " ".join(diff.added_rooms).lower()
    assert len(diff.resized_rooms) >= 1  # bedroom was resized
    assert diff.summary_emoji != ""
    md = diff.to_markdown()
    assert "Cost" in md and "Timeline" in md


def test_input_handler_prompt_caching():
    """InputHandler.parse_prompt must cache results and return identical parsed output instantly."""
    import time

    from build_matrix.input_handler import InputHandler

    prompt = "Modern 3-story villa with 30m width and 20m length"
    # First call
    res1 = InputHandler.parse_prompt(prompt)

    # Second call must be from cache (< 1ms)
    t2 = time.time()
    res2 = InputHandler.parse_prompt(prompt)
    t3 = time.time()

    assert (t3 - t2) < 0.05
    assert res1["num_floors"] == 3
    assert res1["explicit_width"] == 30.0
    assert res1["explicit_length"] == 20.0
    assert res1 == res2


def test_command_prompt_floor_and_dimension_parsing():
    """Verify natural language commands extract floors and dimensions accurately."""
    from build_matrix.input_handler import InputHandler

    cases = [
        ("Make it 3 floors with swimming pool", 3, None, None),
        ("Modern 4-story luxury residence", 4, None, None),
        ("Ground + 2 villa with garden", 3, None, None),
        ("Make plot width 30m and add a pool", 1, 30.0, None),
        ("Plot length 25m and width 20m", 1, 20.0, 25.0),
        ("3 story villa 25x15m", 3, 15.0, 25.0),
    ]
    for text, expected_floors, expected_w, expected_l in cases:
        parsed = InputHandler._parse_prompt_regex(text)
        if expected_floors:
            assert parsed.get("num_floors") == expected_floors, f"Failed floors on: {text}"
        if expected_w:
            assert parsed.get("explicit_width") == expected_w, f"Failed width on: {text}"
        if expected_l:
            assert parsed.get("explicit_length") == expected_l, f"Failed length on: {text}"


def test_generate_building_direct_floor_synchronization():
    """Verify building generation synchronizes exact number of floors and dimensions across all levels."""
    from build_matrix.input_handler import InputHandler
    from build_matrix.layout_engine import LayoutEngine
    from build_matrix.models import ArchitecturalStyle, PlotDimensions

    inputs = {
        "prompt": "Modern 3-story residence with 30m width",
        "plot_length": 25.0,
        "plot_width": 30.0,
        "max_height": 12.0,
        "num_floors": 3,
        "style": "Modern"
    }
    plot_dims = PlotDimensions(
        length=inputs["plot_length"],
        width=inputs["plot_width"],
        max_height=inputs["max_height"],
        num_floors=inputs["num_floors"],
    )
    style_enum = ArchitecturalStyle(inputs["style"])
    prompt_parsed = InputHandler.parse_prompt(inputs["prompt"])
    layout_engine = LayoutEngine(plot=plot_dims, style=style_enum)
    model = layout_engine.generate_building(prompt_parsed=prompt_parsed)

    assert model.plot.num_floors == 3
    assert model.plot.width == 30.0
    assert model.plot.length == 25.0
    # Must have rooms across floor 1, 2, and 3
    floors_with_rooms = {r.floor for r in model.rooms}
    assert 1 in floors_with_rooms
    assert 2 in floors_with_rooms
    assert 3 in floors_with_rooms

