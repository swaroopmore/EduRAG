"""Authorization: users must never see or modify each other's data."""

import uuid

import pytest

from app.main import app
from tests.conftest import DEFAULT_PAGES, make_pdf


def test_every_data_route_requires_authentication(client):
    """No endpoint except health/login/register works without a token."""
    public = {("GET", "/"), ("GET", "/health"), ("GET", "/health/ready"), ("POST", "/auth/login"), ("POST", "/auth/register")}
    schema = app.openapi()
    checked = 0
    for path, methods in schema["paths"].items():
        for method in methods:
            if (method.upper(), path) in public:
                continue
            url = path.replace("{subject_id}", str(uuid.uuid4())).replace("{document_id}", str(uuid.uuid4())) \
                      .replace("{flashcard_id}", str(uuid.uuid4())).replace("{plan_id}", str(uuid.uuid4()))
            r = client.request(method.upper(), url, json={} if method != "get" else None)
            assert r.status_code == 401, f"{method.upper()} {path} -> {r.status_code}"
            checked += 1
    assert checked >= 25


@pytest.fixture
def world(alice, bob):
    """Alice owns a fully populated subject; Bob owns nothing of hers."""
    subject = alice.subject("Alice Biology")
    doc = alice.upload_pdf(subject)
    assert alice.post(f"/notes/generate/{subject}").status_code == 200
    assert alice.post(f"/flashcards/generate/{subject}").status_code == 200
    assert alice.post(f"/quiz/generate/{subject}").status_code == 200
    assert alice.post(f"/study-plans/generate/{subject}").status_code == 200
    assert alice.post("/chat/ask", json={"subject_id": subject, "question": "What is photosynthesis?"}).status_code == 200
    card = alice.get(f"/flashcards/{subject}").json()[0]
    session = alice.get(f"/study-plans/{subject}").json()[0]
    return {"subject": subject, "doc": doc, "card": card, "session": session}


@pytest.mark.parametrize(
    "method,template",
    [
        ("get", "/subjects/{s}"),
        ("delete", "/subjects/{s}"),
        ("get", "/documents/{s}"),
        ("get", "/notes/{s}"),
        ("post", "/notes/generate/{s}"),
        ("get", "/flashcards/{s}"),
        ("post", "/flashcards/generate/{s}"),
        ("get", "/quiz/{s}"),
        ("post", "/quiz/generate/{s}"),
        ("get", "/quiz/{s}/attempts"),
        ("get", "/study-plans/{s}"),
        ("post", "/study-plans/generate/{s}"),
        ("get", "/chat/history/{s}"),
        ("delete", "/chat/history/{s}"),
    ],
)
def test_bob_cannot_touch_alices_subject_resources(bob, world, method, template):
    r = getattr(bob, method)(template.format(s=world["subject"]))
    assert r.status_code == 404, f"{method} {template} -> {r.status_code} {r.text}"
    assert r.json()["code"] in {"subject_not_found", "not_found"}


def test_bob_cannot_modify_alices_subject_or_data(bob, world, alice):
    s = world["subject"]
    assert bob.put(f"/subjects/{s}", json={"name": "Hijacked"}).status_code == 404
    assert bob.post(f"/quiz/{s}/attempts", json={"answers": {}}).status_code == 404
    assert bob.post("/chat/ask", json={"subject_id": s, "question": "What is photosynthesis?"}).status_code == 404
    assert bob.post("/chat/stream", json={"subject_id": s, "question": "What is photosynthesis?"}).status_code == 200  # SSE carries the error event
    assert alice.get(f"/subjects/{s}").json()["name"] == "Alice Biology"
    # Alice's generated data untouched
    assert len(alice.get(f"/notes/{s}").json()) == 2


def test_bob_cannot_upload_into_alices_subject(bob, world, alice):
    r = bob.upload(world["subject"], make_pdf(["Bob injects text into Alice's subject."]), "inject.pdf")
    assert r.status_code == 404
    assert len(alice.get(f"/documents/{world['subject']}").json()) == 1


def test_bob_cannot_access_alices_documents(bob, world, vectors):
    doc_id = world["doc"]["id"]
    for method, url in [("get", f"/documents/{doc_id}/status"), ("get", f"/documents/{doc_id}/file"),
                        ("post", f"/documents/{doc_id}/reindex"), ("delete", f"/documents/{doc_id}")]:
        assert getattr(bob, method)(url).status_code == 404, url
    assert bob.get("/documents").json() == []
    assert vectors.document_chunk_count(doc_id) > 0  # untouched


def test_bob_cannot_scope_chat_to_alices_document(bob, world):
    bobs_subject = bob.subject("Bob's")
    bob.upload_pdf(bobs_subject, ["Bob's own document about geology and rocks."], "bob.pdf")
    r = bob.post("/chat/ask", json={"subject_id": bobs_subject, "question": "photosynthesis?", "document_id": world["doc"]["id"]})
    assert r.status_code == 404


def test_bob_cannot_mutate_alices_flashcards_or_sessions(bob, alice, world):
    assert bob.patch(f"/flashcards/item/{world['card']['id']}", json={"mastered": True}).status_code == 404
    assert bob.patch(f"/study-plans/item/{world['session']['id']}", json={"completed": True}).status_code == 404
    assert alice.get(f"/flashcards/{world['subject']}").json()[0]["mastered"] is False


def test_generate_on_foreign_subject_does_not_delete_owners_data(bob, alice, world):
    bob.post(f"/notes/generate/{world['subject']}")
    bob.post(f"/flashcards/generate/{world['subject']}")
    assert len(alice.get(f"/notes/{world['subject']}").json()) == 2
    assert len(alice.get(f"/flashcards/{world['subject']}").json()) == 5


def test_dashboard_and_subject_lists_only_show_own_data(bob, world):
    assert bob.get("/subjects").json() == []
    d = bob.get("/dashboard").json()
    assert (d["subjects"], d["documents"], d["notes"], d["flashcards"], d["quizzes"], d["study_plans"]) == (0, 0, 0, 0, 0, 0)
    assert d["recent_activity"] == [] and d["recent_documents"] == [] and d["subject_progress"] == []


def test_malformed_ids_are_rejected_not_crashing(alice):
    assert alice.get("/notes/not-a-uuid").status_code == 422
    assert alice.get(f"/notes/{uuid.uuid4()}").status_code == 404
