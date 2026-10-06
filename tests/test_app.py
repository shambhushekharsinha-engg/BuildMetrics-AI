"""
Streamlit AppTest smoke tests for app.py.
Verifies the app file compiles cleanly and key modules are importable
without triggering a full Streamlit network session.
"""
import py_compile
import compileall
import os
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
    from build_matrix import models, engineering, schemas  # noqa: F401


def test_models_importable():
    """Key model classes must be importable."""
    from build_matrix.models import (  # noqa: F401
        BuildingModel, PlotDimensions, RoomSpec,
        ArchitecturalStyle, BOQEstimate, Blueprint2DConfig,
    )


def test_api_module_importable():
    """api.py must be importable (FastAPI app construction runs cleanly)."""
    import api  # noqa: F401
    assert hasattr(api, "app"), "api module must expose 'app' FastAPI instance"


def test_db_module_importable():
    """db.py must be importable without crashing."""
    import db  # noqa: F401
    assert hasattr(db, "repo"), "db module must expose 'repo' DatabaseRepository"


def test_cost_engine_importable():
    """cost_engine.py must be importable without Streamlit dependency."""
    import cost_engine  # noqa: F401
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
    from build_matrix.models import (
        BuildingModel, PlotDimensions, ArchitecturalStyle, BOQEstimate
    )
    from build_matrix.eco_engine import compute_eco_metrics

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
    from build_matrix.models import (
        BuildingModel, PlotDimensions, ArchitecturalStyle,
        RoomSpec, BOQEstimate
    )
    from build_matrix.comparison import compare_designs

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
