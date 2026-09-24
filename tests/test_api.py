import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from api import app
from build_matrix.models import ArchitecturalStyle, BuildingModel

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

def test_health_check():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "buildmetrics-api"


# ---------------------------------------------------------------------------
# Blueprint Generation + Roundtrip
# ---------------------------------------------------------------------------

def test_generate_and_roundtrip():
    """End-to-end generation + Pydantic deserialization roundtrip."""
    req_payload = {
        "prompt": "Test modern villa with 3 floors",
        "plot_length": 30.0,
        "plot_width": 20.0,
        "max_height": 12.0,
        "num_floors": 3,
        "style": "Modern"
    }
    resp = client.post("/api/v1/generate", json=req_payload)
    assert resp.status_code == 200

    data = resp.json()
    assert "building_id" in data
    assert "model" in data

    building_id = data["building_id"]
    serialized_model = data["model"]

    # Test deserialization roundtrip - ensures Enums are not silently broken
    reconstructed_model = TypeAdapter(BuildingModel).validate_python(serialized_model)
    assert reconstructed_model.style == ArchitecturalStyle.MODERN
    assert reconstructed_model.plot.num_floors == 3
    assert reconstructed_model.plot.length == 30.0

    return building_id, serialized_model


def test_generate_invalid_style():
    """API must return 400 on an invalid style."""
    resp = client.post("/api/v1/generate", json={
        "plot_length": 10.0,
        "plot_width": 10.0,
        "max_height": 9.0,
        "num_floors": 2,
        "style": "NOT_A_REAL_STYLE"
    })
    assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# 3D Rendering
# ---------------------------------------------------------------------------

def test_render_3d():
    """Generate a building then test POST /api/v1/render/3d."""
    gen_resp = client.post("/api/v1/generate", json={
        "prompt": "Simple 2-floor house",
        "plot_length": 20.0,
        "plot_width": 15.0,
        "max_height": 9.0,
        "num_floors": 2,
        "style": "Modern"
    })
    assert gen_resp.status_code == 200
    building_id = gen_resp.json()["building_id"]

    render_payload = {"building_id": building_id}
    render_resp = client.post("/api/v1/render/3d", json=render_payload)
    assert render_resp.status_code == 200
    assert "html" in render_resp.text.lower()
    assert "Three.js" in render_resp.text or "three" in render_resp.text.lower()
    # Verify Phase 9 walkthrough feature is included
    assert "PointerLockControls" in render_resp.text or "walkthrough" in render_resp.text.lower()


# ---------------------------------------------------------------------------
# 2D Rendering
# ---------------------------------------------------------------------------

def test_render_2d():
    """Generate a building then test POST /api/v1/render/2d."""
    gen_resp = client.post("/api/v1/generate", json={
        "prompt": "Classic 1-floor bungalow",
        "plot_length": 15.0,
        "plot_width": 12.0,
        "max_height": 5.0,
        "num_floors": 1,
        "style": "Classic / Traditional"
    })
    assert gen_resp.status_code == 200
    building_id = gen_resp.json()["building_id"]

    render_payload = {
        "building_id": building_id,
        "floor": 1,
        "theme": "Classic Blueprint",
        "dpi": 72,
    }
    render_resp = client.post("/api/v1/render/2d", json=render_payload)
    assert render_resp.status_code == 200
    # Verify PNG magic bytes
    assert render_resp.content[:4] == b"\x89PNG"


# ---------------------------------------------------------------------------
# Synchronous Export — All Formats
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("export_format,expected_magic", [
    ("png", b"\x89PNG"),
    ("svg", b"<?xml"),
    ("pdf", b"%PDF"),
])
def test_sync_export_formats(export_format, expected_magic):
    """Generate and synchronously export in each 2D format. Validate file headers."""
    gen_resp = client.post("/api/v1/generate", json={
        "prompt": f"Test {export_format} export",
        "plot_length": 20.0,
        "plot_width": 15.0,
        "max_height": 9.0,
        "num_floors": 2,
        "style": "Modern"
    })
    assert gen_resp.status_code == 200
    building_id = gen_resp.json()["building_id"]

    export_resp = client.post("/api/v1/export", json={
        "building_id": building_id,
        "format": export_format,
        "floor": 1
    })
    assert export_resp.status_code == 200
    assert export_resp.content[:len(expected_magic)] == expected_magic


def test_sync_export_obj():
    """Export 3D OBJ mesh — verify file starts with OBJ comment."""
    gen_resp = client.post("/api/v1/generate", json={
        "prompt": "3D OBJ test",
        "plot_length": 20.0,
        "plot_width": 15.0,
        "max_height": 9.0,
        "num_floors": 2,
        "style": "Modern"
    })
    assert gen_resp.status_code == 200
    building_id = gen_resp.json()["building_id"]

    export_resp = client.post("/api/v1/export", json={
        "building_id": building_id,
        "format": "obj",
        "floor": 1
    })
    assert export_resp.status_code == 200
    # OBJ files start with a comment (#) or vertex declaration (v )
    assert len(export_resp.content) > 0


def test_export_invalid_format():
    """API must return 400 on unsupported export format."""
    gen_resp = client.post("/api/v1/generate", json={
        "plot_length": 10.0,
        "plot_width": 10.0,
        "max_height": 9.0,
        "num_floors": 1,
        "style": "Modern"
    })
    building_id = gen_resp.json()["building_id"]

    resp = client.post("/api/v1/export", json={
        "building_id": building_id,
        "format": "invalid_format",
        "floor": 1
    })
    assert resp.status_code == 400


def test_export_nonexistent_building():
    """Must return 404 when building_id doesn't exist in store."""
    resp = client.post("/api/v1/export", json={
        "building_id": "00000000-0000-0000-0000-000000000000",
        "format": "png",
        "floor": 1
    })
    assert resp.status_code == 404
