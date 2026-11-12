import pytest
from app.rag import RAGStore
from app.llm import SynthesisEngine

@pytest.fixture(scope="module")
def setup_engine():
    store = RAGStore("data")
    store.load_and_index()
    engine = SynthesisEngine()
    return store, engine

def test_documents_indexed(setup_engine):
    store, _ = setup_engine
    assert len(store.documents) == 4
    assert "QC-SOP-014_Rev04_Incoming_Material_Inspection.pdf" in store.documents
    assert store.documents["QC-SOP-014_Rev04_Incoming_Material_Inspection.pdf"].is_active is True
    assert store.documents["QC-SOP-014_Rev03_Incoming_Material_Inspection.pdf"].is_active is False

def test_sample_q1_coolant(setup_engine):
    store, engine = setup_engine
    q = "What is the recommended coolant concentration for the TX-200 CNC turning centre?"
    results, found = store.search(q, top_k=3)
    assert found is True
    out = engine.generate_answer(q, results, found)
    assert "6 - 8 %" in out["answer"]
    assert "TX-200" in out["answer"]
    assert out["citations"][0]["doc_id"] == "MNT-MAN-CNC-02"

def test_sample_q2_al104(setup_engine):
    store, engine = setup_engine
    q = "The machine is showing alarm AL-104. What does it mean and what should the operator do?"
    results, found = store.search(q, top_k=3)
    assert found is True
    out = engine.generate_answer(q, results, found)
    assert "Way lube oil level low" in out["answer"]
    assert "ISO VG 68" in out["answer"]
    assert "RESET" in out["answer"]

def test_sample_q3_lockout(setup_engine):
    store, engine = setup_engine
    q = "Who is allowed to remove a lockout lock from a machine?"
    results, found = store.search(q, top_k=3)
    assert found is True
    out = engine.generate_answer(q, results, found)
    assert "only their own lock" in out["answer"].lower()
    assert "SAF-SOP-003" in out["citations"][0]["doc_id"]

def test_sample_q4_bh220(setup_engine):
    store, engine = setup_engine
    q = "What is the outer diameter tolerance for the BH-220 bearing housing?"
    results, found = store.search(q, top_k=3)
    assert found is True
    out = engine.generate_answer(q, results, found)
    assert "90.000" in out["answer"]
    assert "+/- 0.050" in out["answer"]
    assert out["citations"][0]["doc_id"] == "QC-SOP-014"
    assert out["citations"][0]["revision"] == "Rev 04"

def test_sample_q5_spindle_runout(setup_engine):
    store, engine = setup_engine
    q = "How often should spindle runout be checked, and who does it?"
    results, found = store.search(q, top_k=3)
    assert found is True
    out = engine.generate_answer(q, results, found)
    assert "Monthly" in out["answer"]
    assert "Maintenance technician" in out["answer"]

def test_custom_q_quarantine_cage(setup_engine):
    store, engine = setup_engine
    q = "Where should rejected incoming material be moved, and who keeps the key?"
    results, found = store.search(q, top_k=3)
    assert found is True
    out = engine.generate_answer(q, results, found)
    assert "Quarantine Cage Q1" in out["answer"]
    assert "Shift QC Supervisor" in out["answer"]

def test_custom_q_chuck_torque(setup_engine):
    store, engine = setup_engine
    q = "What torque and tightening pattern should be used when re-mounting the chuck on the TX-200 CNC?"
    results, found = store.search(q, top_k=3)
    assert found is True
    out = engine.generate_answer(q, results, found)
    assert "110 Nm" in out["answer"]
    assert "criss-cross" in out["answer"]

def test_custom_q_sampling_lot(setup_engine):
    store, engine = setup_engine
    q = "If a lot of 200 bought-out components arrives at receiving, how many samples must be inspected, and when is the lot rejected?"
    results, found = store.search(q, top_k=3)
    assert found is True
    out = engine.generate_answer(q, results, found)
    assert "13" in out["answer"]
    assert "QC-SOP-014" in out["citations"][0]["doc_id"]

def test_custom_q_absent_lock_owner(setup_engine):
    store, engine = setup_engine
    q = "What steps must be followed if an operator leaves the plant with their lockout lock still attached?"
    results, found = store.search(q, top_k=3)
    assert found is True
    out = engine.generate_answer(q, results, found)
    assert "Production Manager" in out["answer"]
    assert "Safety Officer" in out["answer"]
    assert "SF-12" in out["answer"]

def test_unanswerable_question_guardrail(setup_engine):
    store, engine = setup_engine
    q = "What is the recommended feed rate and spindle speed for cutting aluminium on the TX-200?"
    results, found = store.search(q, top_k=3)
    out = engine.generate_answer(q, results, found)
    assert out["found"] is False
    assert "Not found in documents" in out["answer"]

