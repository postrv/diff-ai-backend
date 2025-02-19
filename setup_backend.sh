#!/bin/bash
set -e

# Check if a virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
  echo "Error: No virtual environment detected. Please activate your venv before running this script."
  exit 1
fi

echo "Setting up backend structure..."

# Create directories
mkdir -p backend/app/models
mkdir -p backend/app/endpoints
mkdir -p backend/app/services
mkdir -p backend/app/tasks
mkdir -p backend/tests

# Create main.py
cat << 'EOF' > backend/app/main.py
from fastapi import FastAPI
# TODO: Import routers from endpoints (e.g., auth, documents, diffs)

app = FastAPI(title="AI-Powered Document Diffing and Merging App")

@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI-powered Document Diffing and Merging App!"}

# TODO: Add startup and shutdown event handlers if needed
EOF

# Create config.py
cat << 'EOF' > backend/app/config.py
import os

# TODO: Define additional configuration variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/db")
EOF

# Create models/__init__.py
cat << 'EOF' > backend/app/models/__init__.py
# TODO: Import your model definitions here
EOF

# Create models/document.py
cat << 'EOF' > backend/app/models/document.py
# TODO: Define the Document model (e.g., using SQLAlchemy or Pydantic schemas)
EOF

# Create endpoints/__init__.py
cat << 'EOF' > backend/app/endpoints/__init__.py
# TODO: Import individual routers to be included in the main application
EOF

# Create endpoints/auth.py
cat << 'EOF' > backend/app/endpoints/auth.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
async def login():
    # TODO: Implement login functionality and token generation
    return {"message": "Login endpoint - TODO"}
EOF

# Create endpoints/documents.py
cat << 'EOF' > backend/app/endpoints/documents.py
from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # TODO: Handle document upload, storage, and metadata processing
    return {"filename": file.filename, "status": "uploaded"}
EOF

# Create endpoints/diffs.py
cat << 'EOF' > backend/app/endpoints/diffs.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_diff():
    # TODO: Integrate AI-powered diff and merge logic
    return {"message": "Diff endpoint - TODO"}
EOF

# Create services/diff_merge.py
cat << 'EOF' > backend/app/services/diff_merge.py
# TODO: Implement the diff and merge functionality, optionally integrating an AI service

def compute_diff(document_a: str, document_b: str) -> dict:
    # For now, use a simple diff algorithm (e.g., difflib) as a placeholder.
    # Later, integrate an AI service or a more sophisticated algorithm.
    return {"diff": "Not implemented yet"}
EOF

# Create tasks/background_tasks.py
cat << 'EOF' > backend/app/tasks/background_tasks.py
# TODO: Implement background tasks for heavy processing using Celery or another task queue

def run_diff_merge_task():
    # Placeholder for asynchronous diff/merge task execution
    pass
EOF

# Create tests/__init__.py
cat << 'EOF' > backend/tests/__init__.py
# Placeholder for test package initialization
EOF

# Create tests/test_auth.py
cat << 'EOF' > backend/tests/test_auth.py
# TODO: Write tests for authentication endpoints
def test_login():
    # Replace with actual test code
    assert True
EOF

# Create tests/test_documents.py
cat << 'EOF' > backend/tests/test_documents.py
# TODO: Write tests for document upload and management endpoints
def test_upload_document():
    # Replace with actual test code
    assert True
EOF

# Create tests/test_diff_merge.py
cat << 'EOF' > backend/tests/test_diff_merge.py
# TODO: Write tests for the diff/merge service
def test_compute_diff():
    from app.services.diff_merge import compute_diff
    result = compute_diff("Document A", "Document B")
    assert "diff" in result
EOF

# Create requirements.txt
cat << 'EOF' > backend/requirements.txt
fastapi
uvicorn
# TODO: Add additional dependencies (e.g., SQLAlchemy, Celery, etc.)
EOF

# Create Dockerfile
cat << 'EOF' > backend/Dockerfile
# TODO: Customize the Dockerfile as needed for production

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create .env.example
cat << 'EOF' > backend/.env.example
# Example environment variables
DATABASE_URL=postgresql://user:password@localhost/db
# TODO: Add any additional environment variables
EOF

# Create README.md
cat << 'EOF' > backend/README.md
# AI-Powered Document Diffing and Merging App (Backend)

This backend service is built with FastAPI.

## Setup

1. Ensure you have Python and an activated virtual environment.
2. Install dependencies with:
   \`\`\`
   pip install -r requirements.txt
   \`\`\`

## Running the Application

\`\`\`
uvicorn app.main:app --reload
\`\`\`

## TODO

- Implement authentication.
- Implement document management.
- Implement AI-powered diff/merge functionality.
- Add background task processing.
EOF

echo "Backend structure created successfully in the 'backend' directory."
