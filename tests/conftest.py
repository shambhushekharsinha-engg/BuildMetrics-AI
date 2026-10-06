"""
Shared pytest fixtures for BuildMetrics AI test suite.
Provides environment setup, shared API client, and sample building fixtures.
"""
import os
import pytest


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set required environment variables for all tests."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test_buildmetrics.db")
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_test_key")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")  # graceful fallback in model store


@pytest.fixture(scope="session")
def api_client():
    """Shared FastAPI TestClient for all API tests."""
    from fastapi.testclient import TestClient
    from api import app
    return TestClient(app)


@pytest.fixture(scope="session")
def sample_building_id(api_client):
    """Generate a real building and return its ID for multi-test reuse."""
    resp = api_client.post("/api/v1/generate", json={
        "prompt": "Shared fixture building for tests",
        "plot_length": 20.0,
        "plot_width": 15.0,
        "max_height": 9.0,
        "num_floors": 2,
        "style": "Modern",
    })
    assert resp.status_code == 200
    return resp.json()["building_id"]


@pytest.fixture
def minimal_building():
    """Return a minimal BuildingModel for unit tests (no DB, no API)."""
    from build_matrix.models import BuildingModel, PlotDimensions, ArchitecturalStyle
    plot = PlotDimensions(length=20.0, width=15.0, num_floors=2)
    return BuildingModel(plot=plot, style=ArchitecturalStyle.MODERN)
