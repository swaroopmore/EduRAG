"""Dashboard (real data only), subjects CRUD/cascade and startup recovery."""

import json
import os
from pathlib import Path

from app.ai.vectorstore.chroma_service import get_vectorstore
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.document import Document
from app.services import ingestion_service as ingestion
from tests.conftest import QUIZ_JSON


# --------------------------------------------------------------------- dashboard
def test_dashboard_empty_user_has_no_invented_numbers(alice):
    d = alice.get("/dashboard").json()
    assert d["subjects"] == d["documents"] == d["notes"] == d["flashcards"] == d["quizzes"] == 0
    assert d["average_quiz_accuracy"] is None
    assert d["subject_progress"] == [] and d["recent_activity"] == [] and d["recent_documents"] == []


def test_dashboard_reflects_real_activity(alice, llm):
    subject = alice.subject("Biology")
    alice.upload_pdf(subject)
    alice.post(f"/flashcards/generate/{subject}")
    alice.post(f"/notes/generate/{subject}")
    alice.post(f"/quiz/generate/{subject}")
    alice.post(f"/study-plans/generate/{subject}?days=3")
    card = alice.get(f"/flashcards/{subject}").json()[0]
    alice.patch(f"/flashcards/item/{card['id']}", json={"mastered": True})
    plan = alice.get(f"/study-plans/{subject}").json()[0]
    alice.patch(f"/study-plans/item/{plan['id']}", json={"completed": True})

    qs = alice.get(f"/quiz/{subject}").json()
    key = {q["question"]: q["correct_answer"] for q in json.loads(QUIZ_JSON)}
    alice.post(f"/quiz/{subject}/attempts", json={"answers": {q["id"]: key[q["question"]] for q in qs[:3]}})

    d = alice.get("/dashboard").json()
    assert (d["subjects"], d["documents"], d["documents_ready"]) == (1, 1, 1)
    assert (d["flashcards"], d["flashcards_mastered"], d["notes"], d["quizzes"], d["study_plans"]) == (5, 1, 2, 5, 3)
    assert d["study_sessions_completed"] == 1 and d["quiz_attempts"] == 1
    assert d["average_quiz_accuracy"] == 60  # 3 of 5 answered correctly
    progress = d["subject_progress"][0]
    assert progress["name"] == "Biology" and progress["flashcards_mastered"] == 1
    assert progress["progress"] is not None and 0 <= progress["progress"] <= 100
    assert d["recent_documents"][0]["status"] == "ready"
    assert d["recent_activity"]


def test_dashboard_never_counts_other_users(alice, bob):
    s = bob.subject()
    bob.upload_pdf(s)
    bob.post(f"/flashcards/generate/{s}")
    d = alice.get("/dashboard").json()
    assert d["documents"] == 0 and d["flashcards"] == 0 and d["subjects"] == 0


def test_dashboard_needs_auth(client):
    assert client.get("/dashboard").status_code == 401


def test_dashboard_counts_failed_documents(alice):
    s = alice.subject()
    alice.upload_settled(s, b"%PDF-1.4 not really a pdf", "broken.pdf")
    d = alice.get("/dashboard").json()
    assert d["documents_failed"] == 1 and d["documents_ready"] == 0


# ---------------------------------------------------------------------- subjects
def test_subject_crud_and_validation(alice):
    r = alice.post("/subjects", json={"name": "  Physics   101 ", "description": "  motion "})
    assert r.status_code == 201 and r.json()["name"] == "Physics 101" and r.json()["description"] == "motion"
    sid = r.json()["id"]
    assert alice.post("/subjects", json={"name": "   "}).status_code == 422
    assert alice.post("/subjects", json={"name": "x" * 101}).status_code == 422
    assert alice.put(f"/subjects/{sid}", json={"name": "Physics 102"}).json()["name"] == "Physics 102"
    assert alice.get(f"/subjects/{sid}").json()["document_count"] == 0
    assert alice.delete(f"/subjects/{sid}").status_code == 204
    assert alice.get(f"/subjects/{sid}").status_code == 404


def test_duplicate_subject_names_rejected_per_user_only(alice, bob):
    alice.subject("Chemistry")
    assert alice.post("/subjects", json={"name": "chemistry"}).status_code == 409
    assert bob.post("/subjects", json={"name": "Chemistry"}).status_code == 201


def test_subject_list_carries_real_counts(alice):
    s = alice.subject()
    alice.upload_pdf(s)
    alice.post(f"/flashcards/generate/{s}")
    item = alice.get("/subjects").json()[0]
    assert item["document_count"] == 1 and item["ready_document_count"] == 1 and item["flashcard_count"] == 5


def test_deleting_subject_removes_everything_including_vectors_and_files(alice):
    s = alice.subject()
    doc = alice.upload_pdf(s)
    alice.post(f"/notes/generate/{s}")
    store = get_vectorstore()
    assert store.document_chunk_count(doc["id"]) > 0
    upload_root = Path(settings.UPLOAD_DIR)
    assert any(upload_root.rglob("*.pdf"))
    assert alice.delete(f"/subjects/{s}").status_code == 204
    assert store.document_chunk_count(doc["id"]) == 0
    assert not any(upload_root.rglob("*.pdf"))
    db = SessionLocal()
    try:
        assert db.query(Document).count() == 0
    finally:
        db.close()


# ---------------------------------------------------------------------- recovery
def _set_document(doc_id, **fields):
    db = SessionLocal()
    try:
        d = db.get(Document, doc_id)
        for k, v in fields.items():
            setattr(d, k, v)
        db.commit()
    finally:
        db.close()


def test_recovery_reindexes_ready_document_whose_vectors_vanished(alice):
    """Failure scenario 7: server restarted with an empty vector store."""
    s = alice.subject()
    doc = alice.upload_pdf(s)
    store = get_vectorstore()
    store.delete_document(doc["id"])
    assert store.document_chunk_count(doc["id"]) == 0

    stats = ingestion.recover_documents()
    assert stats["reindexed"] == 1
    status = alice.get(f"/documents/{doc['id']}/status").json()
    assert status["status"] == "ready" and store.document_chunk_count(doc["id"]) > 0


def test_recovery_marks_document_failed_when_file_and_vectors_are_gone(alice):
    s = alice.subject()
    doc = alice.upload_pdf(s)
    get_vectorstore().delete_document(doc["id"])
    for f in Path(settings.UPLOAD_DIR).rglob("*.pdf"):
        os.remove(f)
    stats = ingestion.recover_documents()
    assert stats["failed"] == 1
    status = alice.get(f"/documents/{doc['id']}/status").json()
    assert status["status"] == "failed" and "upload" in status["error_message"].lower()


def test_recovery_requeues_interrupted_processing(alice):
    s = alice.subject()
    doc = alice.upload_pdf(s)
    get_vectorstore().delete_document(doc["id"])
    _set_document(doc["id"], status="indexing", stage="embedding")
    stats = ingestion.recover_documents()
    assert stats["requeued"] == 1
    assert alice.get(f"/documents/{doc['id']}/status").json()["status"] == "ready"


def test_recovery_leaves_healthy_documents_alone(alice):
    s = alice.subject()
    alice.upload_pdf(s)
    assert ingestion.recover_documents() == {"requeued": 0, "reindexed": 0, "failed": 0}
