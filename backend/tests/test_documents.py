# backend/tests/test_documents.py
import os
import pytest
from fastapi.testclient import TestClient


def test_upload_document(client, upload_dir, tmp_path):
    """Test document upload functionality."""
    # Create a temporary text file
    file_content = "This is a test document."
    file_path = tmp_path / "test.txt"
    file_path.write_text(file_content)

    with open(file_path, "rb") as f:
        response = client.post(
            "/documents/upload",
            files={"file": ("test.txt", f, "text/plain")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["filename"] == "test.txt"
    assert "message" in data

    # Verify file was saved to disk
    assert os.path.exists(os.path.join(upload_dir, "test.txt"))


def test_list_documents(client, db_session):
    """Test document listing endpoint."""
    # Upload a document first to ensure there's something to list
    file_content = "Test document for listing."
    file_path = "test_list.txt"

    with open(file_path, "w") as f:
        f.write(file_content)

    try:
        with open(file_path, "rb") as f:
            client.post(
                "/documents/upload",
                files={"file": ("test_list.txt", f, "text/plain")}
            )

        # Now test the listing endpoint
        response = client.get("/documents/")
        assert response.status_code == 200

        # Should be a list of documents
        documents = response.json()
        assert isinstance(documents, list)
        assert len(documents) > 0

        # Check document structure
        doc = documents[0]
        assert "id" in doc
        assert "filename" in doc
        assert "created_at" in doc
    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)


def test_get_document(client, db_session):
    """Test retrieving a specific document."""
    # Upload a document first
    file_content = "Test document for retrieval."
    file_path = "test_get.txt"

    with open(file_path, "w") as f:
        f.write(file_content)

    try:
        with open(file_path, "rb") as f:
            upload_response = client.post(
                "/documents/upload",
                files={"file": ("test_get.txt", f, "text/plain")}
            )

        doc_id = upload_response.json()["id"]

        # Test getting the document
        response = client.get(f"/documents/{doc_id}")
        assert response.status_code == 200

        # Check document content
        doc = response.json()
        assert doc["id"] == doc_id
        assert doc["filename"] == "test_get.txt"
        assert doc["content"] == file_content
    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)


def test_get_nonexistent_document(client):
    """Test retrieving a document that doesn't exist."""
    response = client.get("/documents/99999")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_delete_document(client, db_session, upload_dir):
    """Test document deletion."""
    # Upload a document first
    file_content = "Test document for deletion."
    file_path = "test_delete.txt"

    with open(file_path, "w") as f:
        f.write(file_content)

    try:
        with open(file_path, "rb") as f:
            upload_response = client.post(
                "/documents/upload",
                files={"file": ("test_delete.txt", f, "text/plain")}
            )

        doc_id = upload_response.json()["id"]

        # Test deleting the document
        response = client.delete(f"/documents/{doc_id}")
        assert response.status_code == 200
        assert "message" in response.json()

        # Verify the document is gone
        get_response = client.get(f"/documents/{doc_id}")
        assert get_response.status_code == 404
    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)