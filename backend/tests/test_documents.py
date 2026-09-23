import os
import time
from pathlib import Path

from app.core.config import settings
from tests.conftest import DEFAULT_PAGES, make_blank_pdf, make_docx, make_pdf, make_pptx


# --------------------------------------------------------------- Scenario 1: upload -> index -> retrieve
def test_upload_pdf_indexes_and_metadata_is_tenant_scoped(alice, vectors):
    subject = alice.subject()
    before = vectors.count()

    doc = alice.upload_pdf(subject)

    assert doc["status"] == "ready"
    assert doc["page_count"] == 3
    assert doc["chunk_count"] and doc["chunk_count"] >= 3
    assert vectors.count() == before + doc["chunk_count"]  # Chroma count increased

    chunks = vectors.get_chunks(alice.user_id, subject)
    assert len(chunks) == doc["chunk_count"]
    for chunk in chunks:
        meta = chunk.metadata
        assert meta["user_id"] == alice.user_id
        assert meta["subject_id"] == subject
        assert meta["document_id"] == doc["id"]
        assert meta["filename"] == "biology.pdf"
        assert isinstance(meta["page"], int)
        assert "/" not in meta["source"] and "\\" not in meta["source"]  # never a server path
    assert {c.metadata["page"] for c in chunks} == {0, 1, 2}


def test_list_endpoints_and_status(alice):
    subject = alice.subject()
    doc = alice.upload_pdf(subject)
    by_subject = alice.get(f"/documents/{subject}").json()
    everything = alice.get("/documents").json()
    assert [d["id"] for d in by_subject] == [doc["id"]] == [d["id"] for d in everything]
    assert everything[0]["subject_name"] == "Biology"
    assert alice.get(f"/documents/{doc['id']}/status").json()["status"] == "ready"


def test_real_background_queue_reaches_ready(alice, monkeypatch):
    """Exercise the actual thread-pool path (other tests run the job inline)."""
    import app.services.ingestion_service as ingestion

    monkeypatch.undo()  # drop the inline patch from the autouse fixture
    subject = alice.subject()
    doc = alice.upload(subject, make_pdf(DEFAULT_PAGES), "async.pdf").json()
    assert doc["status"] in ("uploaded", "processing", "indexing", "ready")
    for _ in range(50):
        status = alice.get(f"/documents/{doc['id']}/status").json()
        if status["status"] == "ready":
            break
        time.sleep(0.2)
    ingestion.ingestion_queue.shutdown()
    assert status["status"] == "ready"


def test_other_formats_are_supported(alice, vectors):
    subject = alice.subject()
    docx = alice.upload_settled(subject, make_docx(["Newton's laws describe motion. " * 5]), "physics.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    pptx = alice.upload_settled(subject, make_pptx(["Kinematics covers velocity and acceleration in one dimension."]), "slides.pptx",
                        "application/vnd.openxmlformats-officedocument.presentationml.presentation")
    txt = alice.upload_settled(subject, b"Thermodynamics studies heat, work and energy transfer between systems.", "heat.txt", "text/plain")
    assert [docx["status"], pptx["status"], txt["status"]] == ["ready"] * 3
    slide_chunks = [c for c in vectors.get_chunks(alice.user_id, subject) if c.metadata["file_type"] == "pptx"]
    assert slide_chunks and slide_chunks[0].metadata["unit"] == "slide"


# ------------------------------------------------------------------------------ upload security
def test_rejects_unsupported_extension(alice):
    subject = alice.subject()
    r = alice.upload(subject, b"MZ\x90\x00binary", "virus.exe", "application/octet-stream")
    assert r.status_code == 415


def test_rejects_file_whose_content_is_not_a_pdf(alice):
    subject = alice.subject()
    r = alice.upload(subject, b"MZ\x90\x00 this is really an executable", "invoice.pdf", "application/pdf")
    assert r.status_code == 415
    assert "valid PDF" in r.json()["detail"]
    assert not any(Path(settings.UPLOAD_DIR).glob("*")) if Path(settings.UPLOAD_DIR).exists() else True


def test_rejects_mismatched_mime_type(alice):
    subject = alice.subject()
    r = alice.upload(subject, make_pdf(DEFAULT_PAGES), "sneaky.pdf", "text/html")
    assert r.status_code == 415


def test_rejects_empty_and_oversized_files(alice, monkeypatch):
    subject = alice.subject()
    assert alice.upload(subject, b"", "empty.pdf").status_code == 415
    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)
    big = b"%PDF-1.4\n" + b"0" * (1024 * 1024 + 10)
    r = alice.upload(subject, big, "big.pdf")
    assert r.status_code == 413
    leftovers = list(Path(settings.UPLOAD_DIR).glob("*")) if Path(settings.UPLOAD_DIR).exists() else []
    assert leftovers == []  # partial file cleaned up


def test_path_traversal_filename_is_neutralised(alice):
    subject = alice.subject()
    r = alice.upload(subject, make_pdf(DEFAULT_PAGES), "../../../etc/passwd.pdf")
    assert r.status_code == 200
    doc = r.json()
    assert doc["original_filename"] == "passwd.pdf"
    assert "/" not in doc["filename"] and doc["filename"].endswith(".pdf")
    stored = list(Path(settings.UPLOAD_DIR).glob("*.pdf"))
    assert len(stored) == 1 and stored[0].parent == Path(settings.UPLOAD_DIR).resolve()


def test_rejects_zip_without_docx_structure(alice):
    import io, zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("hello.txt", "not a docx")
    r = alice.upload(alice.subject(), buf.getvalue(), "fake.docx", "application/zip")
    assert r.status_code == 415


# ------------------------------------------------------------------------------ processing failures
def test_scanned_pdf_without_text_fails_gracefully(alice, vectors):
    subject = alice.subject()
    doc = alice.upload_settled(subject, make_blank_pdf(), "scan.pdf")
    assert doc["status"] == "failed"
    assert "No readable text" in doc["error_message"]
    assert vectors.get_chunks(alice.user_id, subject) == []


def test_corrupted_pdf_fails_gracefully(alice):
    doc = alice.upload_settled(alice.subject(), b"%PDF-1.4\nthis is not really a pdf at all\n%%EOF", "broken.pdf")
    assert doc["status"] == "failed"
    assert doc["error_message"]


def test_unexpected_pipeline_crash_marks_failed_and_cleans_vectors(alice, vectors, monkeypatch):
    from app.ai.pipeline.document_pipeline import DocumentPipeline

    def boom(self, chunks, ids, document_id):
        vectors.add_chunks(chunks[:1], ids[:1])  # simulate a partial write
        raise RuntimeError("embedding service exploded")

    monkeypatch.setattr(DocumentPipeline, "index", boom)
    subject = alice.subject()
    doc = alice.upload_settled(subject, make_pdf(DEFAULT_PAGES), "x.pdf")
    assert doc["status"] == "failed"
    assert "exploded" not in doc["error_message"]  # technical detail stays in the logs
    assert vectors.get_chunks(alice.user_id, subject) == []  # partial vectors removed


# ------------------------------------------------------------------- delete / reindex / download
def test_delete_document_removes_vectors_and_file(alice, vectors):
    subject = alice.subject()
    doc = alice.upload_pdf(subject)
    assert list(Path(settings.UPLOAD_DIR).glob("*.pdf"))
    assert alice.delete(f"/documents/{doc['id']}").status_code == 204
    assert vectors.get_chunks(alice.user_id, subject) == []
    assert list(Path(settings.UPLOAD_DIR).glob("*.pdf")) == []
    assert alice.get(f"/documents/{doc['id']}/status").status_code == 404


def test_reindex_recreates_vectors_without_duplicates(alice, vectors):
    subject = alice.subject()
    doc = alice.upload_pdf(subject)
    count = vectors.count()
    vectors.delete_document(doc["id"])  # e.g. Chroma volume was lost
    assert vectors.count() == count - doc["chunk_count"]
    r = alice.post(f"/documents/{doc['id']}/reindex")
    assert r.status_code == 200
    assert alice.get(f"/documents/{doc['id']}/status").json()["status"] == "ready"
    assert vectors.count() == count  # exactly the same, no duplicates
    alice.post(f"/documents/{doc['id']}/reindex")
    assert vectors.count() == count


def test_reindex_fails_clearly_when_file_is_gone(alice):
    subject = alice.subject()
    doc = alice.upload_pdf(subject)
    for f in Path(settings.UPLOAD_DIR).glob("*.pdf"):
        os.remove(f)
    r = alice.post(f"/documents/{doc['id']}/reindex")
    assert r.status_code == 409 and r.json()["code"] == "file_missing"


def test_open_document_file(alice):
    subject = alice.subject()
    original = make_pdf(DEFAULT_PAGES)
    doc = alice.upload(subject, original, "lecture one.pdf").json()
    r = alice.get(f"/documents/{doc['id']}/file")
    assert r.status_code == 200
    assert r.content == original
    assert r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"].startswith("inline")
