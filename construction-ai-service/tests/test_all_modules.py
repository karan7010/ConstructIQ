"""
Placeholder test file for all modules.
Will be expanded in later phases.
"""

from fastapi.testclient import TestClient


def test_health_check():
    """Test that the /health endpoint returns correct response."""
    from main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "construction-ai-service"


def test_modules_importable():
    """Test that all module stubs can be imported without errors."""
    from modules import cad_parser
    from modules import estimation_engine
    from modules import deviation_analysis
    from modules import ml_predictor
    from modules import rag_assistant

    assert cad_parser.DEFAULT_WALL_HEIGHT == 3.0
    assert estimation_engine.BRICKS_PER_M2_WALL == 50
    assert deviation_analysis.DEVIATION_PCT_THRESHOLD == 20.0
    assert ml_predictor.RISK_THRESHOLDS["low"] == 0.3
    assert rag_assistant.TOP_K_RESULTS == 5
