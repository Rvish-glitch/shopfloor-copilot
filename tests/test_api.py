from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["indexed_documents"] == 4

def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "BiztelAI" in response.text
    assert "Shop Floor Copilot" in response.text
    assert "Revision-Aware Engine" in response.text

def test_documents_api():
    response = client.get("/api/documents")
    assert response.status_code == 200
    docs = response.json()["documents"]
    assert len(docs) == 4
    # Check that Rev 04 is active and Rev 03 is superseded
    rev04 = next(d for d in docs if "Rev04" in d["filename"])
    rev03 = next(d for d in docs if "Rev03" in d["filename"])
    assert rev04["is_active"] is True
    assert rev03["is_active"] is False

def test_query_sample_q1():
    response = client.post("/api/query", json={
        "question": "What is the recommended coolant concentration for the TX-200 CNC turning centre?"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert "6 - 8 %" in data["answer"]
    assert len(data["citations"]) > 0

def test_query_alarm_al104():
    response = client.post("/api/query", json={
        "question": "The machine is showing alarm AL-104. What does it mean and what should the operator do?"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert "Way lube oil level low" in data["answer"]
    assert "ISO VG 68" in data["answer"]

def test_query_out_of_scope():
    response = client.post("/api/query", json={
        "question": "What is the recommended feed rate and spindle speed for cutting aluminium on the TX-200?"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is False
    assert "Not found in documents" in data["answer"]

def test_query_empty():
    response = client.post("/api/query", json={"question": ""})
    assert response.status_code == 400

