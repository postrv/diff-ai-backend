# backend/app/main.py
from fastapi import FastAPI
from backend.app.endpoints import (auth, documents, diffs)
from backend.app.db_init import create_tables
from backend.app.config import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI-Powered Document Diffing and Merging App")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from different modules
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(diffs.router)

@app.on_event("startup")
async def startup_event():
    """Run on application startup to ensure database is initialized"""
    create_tables()

@app.get("/", tags=["root"])
async def root():
    """Root endpoint returning API information"""
    return {
        "app_name": "AI-Powered Document Diffing and Merging App",
        "version": "0.1.0",
        "status": "operational"
    }