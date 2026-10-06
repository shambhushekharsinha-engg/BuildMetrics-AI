"""
Unit tests for cost_engine.py.
Verifies ML model loading, cost prediction, and module independence from Streamlit.
"""
import os
import pytest


class TestCostEngineImport:
    def test_module_imports_without_streamlit(self):
        """cost_engine must be importable without any Streamlit dependency."""
        import cost_engine  # noqa: F401
        assert True  # No ImportError = pass

    def test_predict_cost_function_exists(self):
        """predict_cost must be a callable."""
        from cost_engine import predict_cost
        assert callable(predict_cost)

    def test_load_model_function_exists(self):
        """load_model must be a callable."""
        from cost_engine import load_model
        assert callable(load_model)


class TestCostModelFile:
    def test_model_file_exists(self):
        """cost_model.pkl must be present at project root."""
        assert os.path.exists("cost_model.pkl"), (
            "cost_model.pkl not found. Run `python train_model.py` to generate it."
        )

    def test_model_file_not_trivially_small(self):
        """cost_model.pkl must be >1KB (sanity check against empty/corrupt file)."""
        size = os.path.getsize("cost_model.pkl")
        assert size > 1000, f"cost_model.pkl is suspiciously small: {size} bytes"

    def test_model_loads_successfully(self):
        """load_model() must return a non-None scikit-learn model."""
        from cost_engine import load_model
        model = load_model()
        assert model is not None
        # Must have a predict method (scikit-learn protocol)
        assert hasattr(model, "predict"), "Model must implement sklearn predict interface"


class TestCostPrediction:
    def test_prediction_returns_float(self):
        """predict_cost must return a float."""
        from cost_engine import predict_cost
        result = predict_cost(area=200.0, floors=2, tier=2, grade=2)
        assert isinstance(result, float)

    def test_prediction_is_positive(self):
        """Construction cost must be a positive number."""
        from cost_engine import predict_cost
        result = predict_cost(area=200.0, floors=2, tier=2, grade=2)
        assert result > 0, f"Expected positive cost, got {result}"

    @pytest.mark.parametrize("area,floors,tier,grade", [
        (100.0, 1, 1, 1),   # small, metro, economy
        (250.0, 2, 2, 2),   # medium, city, standard
        (500.0, 3, 3, 3),   # large, town, premium
        (50.0, 1, 1, 3),    # tiny, metro, premium
        (1000.0, 10, 1, 3), # tower, metro, premium
        (2000.0, 20, 2, 2), # large tower, standard
    ])
    def test_prediction_parametrized(self, area, floors, tier, grade):
        """predict_cost must handle various valid inputs without error."""
        from cost_engine import predict_cost
        result = predict_cost(area=area, floors=floors, tier=tier, grade=grade)
        assert isinstance(result, (int, float))
        assert result >= 0, f"Got negative cost: {result} for inputs ({area},{floors},{tier},{grade})"

    def test_premium_costs_more_than_economy(self):
        """Grade 3 (premium) should cost more than grade 1 (economy) for same building."""
        from cost_engine import predict_cost
        economy = predict_cost(area=300.0, floors=2, tier=2, grade=1)
        premium = predict_cost(area=300.0, floors=2, tier=2, grade=3)
        assert premium >= economy, (
            f"Premium ({premium:.0f}) should not be cheaper than economy ({economy:.0f})"
        )

    def test_metro_costs_more_than_town(self):
        """Tier 1 (metro) should cost more than tier 3 (town) for same building."""
        from cost_engine import predict_cost
        town = predict_cost(area=300.0, floors=2, tier=3, grade=2)
        metro = predict_cost(area=300.0, floors=2, tier=1, grade=2)
        assert metro >= town, (
            f"Metro ({metro:.0f}) should not be cheaper than town ({town:.0f})"
        )

    def test_model_lru_cache_works(self):
        """load_model should return the same object on repeated calls (LRU cached)."""
        from cost_engine import load_model
        m1 = load_model()
        m2 = load_model()
        assert m1 is m2, "Expected LRU-cached model (same object reference)"
