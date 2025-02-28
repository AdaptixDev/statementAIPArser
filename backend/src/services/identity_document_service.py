#!/usr/bin/env python3
"""
Service for processing identity documents (driving licenses and passports) with Gemini.
"""

import os
import logging
import json
import tempfile
import shutil
from typing import Dict, Any, Optional

from backend.src.services.gemini_service import GeminiService

# Configure logging
logger = logging.getLogger(__name__)

# Identity document prompts
GEMINI_DRIVING_LICENSE_PARSE = """
Please analyze this driving license image and extract the following information in JSON format:
- Full name
- Date of birth
- License number
- Issue date
- Expiry date
- Address
- License type/categories
- Issuing authority
- Photo description (brief description of the photo if visible)

Return the data in the following JSON format:
{
  "fullName": "John Smith",
  "dateOfBirth": "01-01-1980",
  "licenseNumber": "ABC123456",
  "issueDate": "01-01-2020",
  "expiryDate": "01-01-2030",
  "address": "123 Example Street, Example Town, EX1 1EX",
  "licenseCategories": ["B", "B1"],
  "issuingAuthority": "DVLA",
  "photoDescription": "Headshot of a male with short brown hair"
}

If any field cannot be determined, use null for that field. Do not include any explanatory text outside the JSON structure.
"""

GEMINI_PASSPORT_PARSE = """
Please analyze this passport image and extract the following information in JSON format:
- Full name
- Date of birth
- Passport number
- Issue date
- Expiry date
- Nationality
- Place of birth
- Issuing authority
- Gender
- Photo description (brief description of the photo if visible)

Return the data in the following JSON format:
{
  "fullName": "John Smith",
  "dateOfBirth": "01-01-1980",
  "passportNumber": "ABC123456",
  "issueDate": "01-01-2020",
  "expiryDate": "01-01-2030",
  "nationality": "British",
  "placeOfBirth": "London",
  "issuingAuthority": "HMPO",
  "gender": "M",
  "photoDescription": "Headshot of a male with short brown hair"
}

If any field cannot be determined, use null for that field. Do not include any explanatory text outside the JSON structure.
"""


class IdentityDocumentGeminiService(GeminiService):
    """
    Specialized service for processing identity documents with Gemini.
    Supports driving licenses and passports.
    """
    
    def __init__(self):
        """Initialize the identity document service."""
        super().__init__()
        
    def process_document(self, pdf_path: str, document_type: str = "driving_license", chunk_count: int = 1) -> dict:
        """
        Process an identity document with Gemini.
        
        Args:
            pdf_path: Path to the PDF file to process
            document_type: Type of document to process ('driving_license' or 'passport')
            chunk_count: Number of chunks to split the PDF into (usually 1 for identity documents)
            
        Returns:
            A dictionary containing the extracted information
        """
        # Validate document type
        if document_type not in ["driving_license", "passport"]:
            raise ValueError("Document type must be 'driving_license' or 'passport'")
        
        # Create a temporary directory for storing sub-PDFs
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {temp_dir}")
        
        try:
            # For identity documents, we typically don't need to split the PDF
            # But we'll use the same approach for consistency
            smaller_pdfs = self.split_pdf_into_subpdfs(pdf_path, chunk_count, temp_dir)
            
            if not smaller_pdfs:
                logger.error("Failed to split PDF into sub-PDFs")
                return {"error": "Failed to process document"}
            
            # Use the first (and likely only) chunk
            document_path = smaller_pdfs[0]
            
            # Upload document to Gemini
            pdf_obj = self.upload_to_gemini(document_path)
            
            # Wait for the file to be active
            self.wait_for_files_active([pdf_obj])
            
            # Select the appropriate prompt based on document type
            if document_type == "driving_license":
                prompt = GEMINI_DRIVING_LICENSE_PARSE
            else:  # passport
                prompt = GEMINI_PASSPORT_PARSE
            
            # Process with the selected prompt
            response_text = self.generate_content(prompt, pdf_obj)
            
            # Parse the JSON response
            try:
                document_data = json.loads(response_text)
                return {
                    "document_type": document_type,
                    "document_data": document_data
                }
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response from Gemini")
                return {
                    "document_type": document_type,
                    "error": "Failed to parse response",
                    "raw_response": response_text
                }
            
        finally:
            # Clean up: remove all sub-PDFs in the temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"Removed temporary directory: {temp_dir}")
    
    def process_driving_license(self, pdf_path: str) -> dict:
        """
        Process a driving license with Gemini.
        
        Args:
            pdf_path: Path to the PDF file to process
            
        Returns:
            A dictionary containing the extracted information
        """
        return self.process_document(pdf_path, document_type="driving_license")
    
    def process_passport(self, pdf_path: str) -> dict:
        """
        Process a passport with Gemini.
        
        Args:
            pdf_path: Path to the PDF file to process
            
        Returns:
            A dictionary containing the extracted information
        """
        return self.process_document(pdf_path, document_type="passport") 