# backend/app/endpoints/diffs.py
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel
import uuid

from backend.app.database import get_db
from backend.app.models.document import Document
from backend.app.services.diff_merge import compute_diff, compute_enhanced_diff, merge_documents, smart_merge_documents
from backend.app.services.ai_service import AIRequest
from backend.app.tasks.background_tasks import run_diff_merge_task, run_merge_task, get_task_result

router = APIRouter(prefix="/diffs", tags=["diffs"])


class MergeRequest(BaseModel):
    """Request model for document merge operations"""
    doc_id_a: int
    doc_id_b: int
    conflict_resolution: str = "latest"  # 'latest', 'original', 'both', or 'custom'
    ai_guidance: Optional[Dict[str, Any]] = None


@router.get("/")
async def get_diff(
        doc_id_a: int = Query(..., description="ID of the first document"),
        doc_id_b: int = Query(..., description="ID of the second document"),
        enhanced: bool = Query(False, description="Use enhanced diff with statistics"),
        db: Session = Depends(get_db)
):
    """Get diff between two documents"""
    # Retrieve the documents
    doc_a = db.query(Document).filter(Document.id == doc_id_a).first()
    doc_b = db.query(Document).filter(Document.id == doc_id_b).first()

    if not doc_a or not doc_b:
        raise HTTPException(status_code=404, detail="One or both documents not found")

    if enhanced:
        # Use enhanced diff functionality
        diff_result = await compute_enhanced_diff(doc_a.content, doc_b.content)
        return diff_result.to_dict()
    else:
        # Use basic diff functionality
        diff_lines = compute_diff(doc_a.content, doc_b.content)
        return {"diff": diff_lines}


@router.post("/merge")
async def merge_docs(
        merge_request: MergeRequest,
        db: Session = Depends(get_db)
):
    """Merge two documents with specified conflict resolution strategy using AI"""
    # Retrieve the documents
    doc_a = db.query(Document).filter(Document.id == merge_request.doc_id_a).first()
    doc_b = db.query(Document).filter(Document.id == merge_request.doc_id_b).first()

    if not doc_a or not doc_b:
        raise HTTPException(status_code=404, detail="One or both documents not found")

    # Perform the AI-powered merge
    try:
        merge_result = await smart_merge_documents(
            doc_a.content,
            doc_b.content,
            merge_request.conflict_resolution,
            merge_request.ai_guidance
        )

        # Create a new document with the merged content
        merged_doc = Document(
            filename=f"MERGED_{doc_a.filename}_{doc_b.filename}",
            content=merge_result["merged_content"]
        )
        db.add(merged_doc)
        db.commit()
        db.refresh(merged_doc)

        return {
            "id": merged_doc.id,
            "filename": merged_doc.filename,
            "message": "Documents merged successfully",
            "merge_report": merge_result.get("report", {})
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error during merge process: {str(e)}")


@router.post("/async-merge")
async def create_async_merge(
        merge_request: MergeRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """Create an asynchronous merge task that runs in the background"""
    # Retrieve the documents
    doc_a = db.query(Document).filter(Document.id == merge_request.doc_id_a).first()
    doc_b = db.query(Document).filter(Document.id == merge_request.doc_id_b).first()

    if not doc_a or not doc_b:
        raise HTTPException(status_code=404, detail="One or both documents not found")

    # Create a unique task ID
    task_id = f"merge_task_{uuid.uuid4()}"

    # Create AIRequest object
    ai_request = AIRequest(
        doc_a=doc_a.content,
        doc_b=doc_b.content,
        conflict_resolution=merge_request.conflict_resolution,
        guidance=merge_request.ai_guidance
    )

    # Add the task to background tasks
    background_tasks.add_task(run_merge_task, ai_request, task_id)

    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Merge processing task has been queued",
        "doc_a_id": doc_a.id,
        "doc_b_id": doc_b.id
    }


@router.post("/async-diff")
async def create_async_diff(
        background_tasks: BackgroundTasks,
        doc_id_a: int = Query(...),
        doc_id_b: int = Query(...),
        db: Session = Depends(get_db)
):
    """Create a diff processing task to run in the background"""
    # Retrieve the documents
    doc_a = db.query(Document).filter(Document.id == doc_id_a).first()
    doc_b = db.query(Document).filter(Document.id == doc_id_b).first()

    if not doc_a or not doc_b:
        raise HTTPException(status_code=404, detail="One or both documents not found")

    # Create a unique task ID
    task_id = f"diff_task_{uuid.uuid4()}"

    # Add the task to background tasks
    background_tasks.add_task(run_diff_merge_task, doc_a.content, doc_b.content, task_id)

    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Diff processing task has been queued"
    }


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Get the status and result of an asynchronous diff or merge task"""
    result = get_task_result(task_id)
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return result


@router.get("/merge-result/{task_id}")
async def get_merge_result(
        task_id: str,
        apply_result: bool = Query(False, description="Whether to save the merge result as a new document"),
        db: Session = Depends(get_db)
):
    """
    Get the result of a completed merge task and optionally save it as a new document

    Args:
        task_id: Task identifier
        apply_result: If True, create a new document with the merged content
        db: Database session

    Returns:
        Merge result or created document information
    """
    # Get task result
    result = get_task_result(task_id)

    # Check if task exists and is completed
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if result.get("status") != "completed":
        return result

    # If apply_result is True, create a new document with the merged content
    if apply_result and "result" in result and "merged_content" in result["result"]:
        try:
            # Extract document IDs from task_id if possible
            doc_ids = None
            if task_id.startswith("merge_task_"):
                parts = task_id.split("_")
                if len(parts) >= 4:
                    doc_ids = (parts[2], parts[3])

            # Get filenames if doc_ids were found
            filenames = []
            if doc_ids:
                for doc_id in doc_ids:
                    try:
                        doc = db.query(Document).filter(Document.id == int(doc_id)).first()
                        if doc:
                            filenames.append(doc.filename)
                    except (ValueError, TypeError):
                        pass

            # Create filename
            if len(filenames) == 2:
                filename = f"MERGED_{filenames[0]}_{filenames[1]}"
            else:
                filename = f"MERGED_DOCUMENT_{task_id}"

            # Create document
            merged_doc = Document(
                filename=filename,
                content=result["result"]["merged_content"]
            )
            db.add(merged_doc)
            db.commit()
            db.refresh(merged_doc)

            # Return document info with merge report
            return {
                "id": merged_doc.id,
                "filename": merged_doc.filename,
                "message": "Merged document created successfully",
                "merge_report": result["result"].get("report", {})
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating merged document: {str(e)}"
            )

    # Return the merge result
    return result