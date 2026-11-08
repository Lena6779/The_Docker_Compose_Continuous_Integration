from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "ollama" in data


def test_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "document_count" in data
