"""FastAPI application for the backend API."""

import os
import tempfile
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.src.core.statement_processor import StatementProcessor
from backend.src.utils.logging_utils import setup_logger

# Set up logging
logger = setup_logger("api", level=logging.INFO)

# Create FastAPI app
app = FastAPI(
    title="Financial Statement Parser API",
    description="API for parsing financial statements using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create statement processor
processor = StatementProcessor()

class ProcessResponse(BaseModel):
    """Response model for the process endpoint."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Financial Statement Parser API"}

@app.post("/process", response_model=ProcessResponse)
async def process_statement(
    file: UploadFile = File(...),
    use_gemini: bool = Form(False)
):
    """
    Process a financial statement PDF.
    
    Args:
        file: The PDF file to process
        use_gemini: Whether to use Gemini instead of OpenAI
        
    Returns:
        ProcessResponse object with the processing results
    """
    try:
        # Check if the file is a PDF
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File must be a PDF")
            
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the uploaded file
            temp_file_path = os.path.join(temp_dir, file.filename)
            with open(temp_file_path, "wb") as f:
                f.write(await file.read())
                
            # Process the PDF statement
            result = processor.process_pdf_statement(
                pdf_path=temp_file_path,
                output_dir=temp_dir,
                use_gemini=use_gemini
            )
            
            return ProcessResponse(
                success=True,
                message=f"Successfully processed {file.filename}",
                data=result
            )
            
    except Exception as e:
        logger.error(f"Error processing statement: {str(e)}")
        return ProcessResponse(
            success=False,
            message=f"Error processing statement: {str(e)}",
            data=None
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 