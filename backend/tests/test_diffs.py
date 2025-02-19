# backend/tests/test_diffs.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.models.document import Document


@pytest.mark.asyncio
async def test_get_diff(client, db_session):
    """Test retrieving diff between two documents."""
    # Create two test documents in the database
    doc_a = Document(
        filename="doc_a.txt",
        content="This is document A.\nIt has some content.\nThis is the end."
    )
    doc_b = Document(
        filename="doc_b.txt",
        content="This is document B.\nIt has different content.\nThis is the end."
    )

    db_session.add(doc_a)
    db_session.add(doc_b)
    db_session.commit()
    db_session.refresh(doc_a)
    db_session.refresh(doc_b)

    # Test basic diff
    response = client.get(
        f"/diffs/?doc_id_a={doc_a.id}&doc_id_b={doc_b.id}&enhanced=false"
    )
    assert response.status_code == 200
    data = response.json()
    assert "diff" in data
    assert isinstance(data["diff"], list)
    assert len(data["diff"]) > 0

    # Test enhanced diff
    response = client.get(
        f"/diffs/?doc_id_a={doc_a.id}&doc_id_b={doc_b.id}&enhanced=true"
    )
    assert response.status_code == 200
    data = response.json()
    assert "diff_lines" in data
    assert "stats" in data
    assert "ai_summary" in data
    assert isinstance(data["stats"], dict)
    assert "added_lines" in data["stats"]
    assert "removed_lines" in data["stats"]


def test_get_diff_nonexistent_documents(client):
    """Test diff with nonexistent document IDs."""
    response = client.get("/diffs/?doc_id_a=99999&doc_id_b=99998")
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_merge_docs(client, db_session):
    """Test document merging functionality."""
    # Create two test documents in the database
    doc_a = Document(
        filename="merge_a.txt",
        content="Line 1\nLine 2\nLine 3"
    )
    doc_b = Document(
        filename="merge_b.txt",
        content="Line 1\nModified Line 2\nLine 3\nLine 4"
    )

    db_session.add(doc_a)
    db_session.add(doc_b)
    db_session.commit()
    db_session.refresh(doc_a)
    db_session.refresh(doc_b)

    # Test merge with "latest" strategy
    merge_request = {
        "doc_id_a": doc_a.id,
        "doc_id_b": doc_b.id,
        "conflict_resolution": "latest"
    }
    response = client.post("/diffs/merge", json=merge_request)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "filename" in data
    assert data["filename"].startswith("MERGED_")

    # Verify the merged document was created
    merged_doc_response = client.get(f"/documents/{data['id']}")
    assert merged_doc_response.status_code == 200
    merged_doc = merged_doc_response.json()
    assert merged_doc["content"] == doc_b.content  # With "latest" strategy


@pytest.mark.asyncio
async def test_async_diff(client, db_session):
    """Test asynchronous diff processing."""
    # Create two test documents in the database
    doc_a = Document(
        filename="async_a.txt",
        content="This is a test.\nFor async processing."
    )
    doc_b = Document(
        filename="async_b.txt",
        content="This is a test.\nWith a change.\nFor async processing."
    )

    db_session.add(doc_a)
    db_session.add(doc_b)
    db_session.commit()
    db_session.refresh(doc_a)
    db_session.refresh(doc_b)

    # Test async diff endpoint
    response = client.post(
        f"/diffs/async-diff?doc_id_a={doc_a.id}&doc_id_b={doc_b.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "status" in data
    assert data["status"] == "Processing started"

    # Test task status endpoint
    if "task_id" in data:
        task_id = data["task_id"]
        # Wait a moment for task to start processing
        import time
        time.sleep(1)

        status_response = client.get(f"/diffs/task-status/{task_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["processing", "completed", "failed"]