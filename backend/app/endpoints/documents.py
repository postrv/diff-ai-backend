# backend/app/endpoints/documents.py
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.app.database import get_db
from backend.app.models.document import Document

router = APIRouter(prefix="/documents", tags=["documents"])

# Ensure the uploads directory exists.
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a document, store it in the file system and save metadata to the database.
    """
    try:
        contents = await file.read()
        try:
            text_content = contents.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid text file format. Only text files are supported.")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file content: {str(e)}")

    # Save file to disk (for reference/backup).
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(contents)

    # Create and persist a document record in the database.
    new_doc = Document(filename=file.filename, content=text_content)
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return {"id": new_doc.id, "filename": new_doc.filename, "message": "Document uploaded successfully"}


@router.get("/", response_model=List[dict])
async def list_documents(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        db: Session = Depends(get_db)
):
    """
    List all documents with pagination support.
    """
    documents = db.query(Document).order_by(Document.created_at.desc()).offset(offset).limit(limit).all()
    result = []
    for doc in documents:
        result.append({
            "id": doc.id,
            "filename": doc.filename,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        })
    return result


@router.get("/{doc_id}")
async def get_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific document by ID.
    """
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": document.id,
        "filename": document.filename,
        "content": document.content,
        "created_at": document.created_at,
        "updated_at": document.updated_at
    }


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Delete a document from the database and file system.
    """
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Try to delete file from file system if it exists
    file_path = os.path.join(UPLOAD_DIR, document.filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            # Log error but continue with DB deletion
            print(f"Error removing file: {e}")

    # Delete from database
    db.delete(document)
    db.commit()

    return {"message": f"Document {doc_id} successfully deleted"}