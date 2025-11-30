"""
FastAPI backend for Legal RAG System
Provides REST API endpoints for the React frontend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from query_rag import LegalRAG
from pdf_generator import generate_case_pdf
import uvicorn
import boto3
import config
import io
import json

app = FastAPI(
    title="Legal RAG API",
    description="REST API for Legal Research Assistant",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system once at startup
rag = None
case_id_to_s3 = {}

@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup."""
    global rag, case_id_to_s3
    print("Initializing Legal RAG system...")
    rag = LegalRAG()

    # Load case_id to S3 mapping
    try:
        with open("case_id_to_s3_mapping.json", 'r') as f:
            case_id_to_s3 = json.load(f)
        print(f"Loaded S3 mapping for {len(case_id_to_s3)} cases")
    except FileNotFoundError:
        print("Warning: case_id_to_s3_mapping.json not found. Downloads will not work.")

    print("Legal RAG API ready!")


# Request/Response models
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    message: str


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Legal RAG API is running"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check."""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    return {
        "status": "healthy",
        "message": f"Ready with {len(rag.parent_lookup)} cases"
    }


@app.post("/api/query")
async def query(request: QueryRequest):
    """
    Query the Legal RAG system.

    Args:
        request: QueryRequest with question and optional top_k

    Returns:
        RAG response with answer, sources, and metadata
    """
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Query the RAG system
        response = rag.query(request.question, top_k=request.top_k)

        # Add API metadata
        response['metadata'] = {
            'embedding_provider': rag.embedding_provider,
            'llm_provider': rag.llm_provider,
            'total_cases': len(rag.parent_lookup)
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/api/stats")
async def stats():
    """Get system statistics."""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")

    return {
        "total_cases": len(rag.parent_lookup),
        "embedding_provider": rag.embedding_provider,
        "llm_provider": rag.llm_provider,
        "embedding_model": rag.embedding_model if hasattr(rag, 'embedding_model') else "OpenAI",
    }


@app.get("/api/download/{case_id}")
async def download_case_pdf(case_id: int):
    """
    Download a PDF of the legal case.

    Args:
        case_id: The CAP case ID

    Returns:
        PDF file as a streaming response
    """
    try:
        # Look up S3 key from mapping
        s3_key = case_id_to_s3.get(str(case_id))

        if not s3_key:
            raise HTTPException(
                status_code=404,
                detail=f"Case file not found for case_id {case_id}"
            )

        # Fetch the JSON file from S3
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=config.BUCKET_NAME, Key=s3_key)
        case_data = json.loads(response['Body'].read())

        # Generate PDF from the case data
        pdf_buffer = generate_case_pdf(case_data)

        # Determine filename
        case_name = case_data.get('name_abbreviation', f'Case_{case_id}')
        # Clean filename (remove special characters)
        safe_name = "".join(c for c in case_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}.pdf"

        # Return as streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )


if __name__ == "__main__":
    # Run with: python api.py
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
