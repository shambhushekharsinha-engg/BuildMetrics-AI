import pytest
from fastapi.testclient import TestClient
from api import app
from pydantic import TypeAdapter
from build_matrix.models import BuildingModel, ArchitecturalStyle

client = TestClient(app)

def test_generate_and_roundtrip():
    # 1. Test POST /api/v1/generate
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
    
    # 2. Test deserialization roundtrip
    # Ensures Enums like ArchitecturalStyle aren't silently broken
    reconstructed_model = TypeAdapter(BuildingModel).validate_python(serialized_model)
    assert reconstructed_model.style == ArchitecturalStyle.MODERN
    assert reconstructed_model.plot.num_floors == 3
    assert reconstructed_model.plot.length == 30.0
    
    # 3. Test POST /api/v1/render/3d
    render_payload = {"building_id": building_id}
    render_resp = client.post("/api/v1/render/3d", json=render_payload)
    assert render_resp.status_code == 200
    assert "html" in render_resp.text.lower()
