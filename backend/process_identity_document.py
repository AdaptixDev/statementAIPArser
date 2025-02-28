#!/usr/bin/env python3
"""
Example script for processing identity documents (driving licenses and passports) with Gemini.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.src.services import IdentityDocumentGeminiService
from backend.src.utils.logging_utils import setup_logger

# Set up logging
logger = setup_logger("identity_document_processor", level=logging.INFO)

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Process identity documents using Gemini.")
    parser.add_argument("--pdf", type=str, required=True, help="Path to the PDF document to process")
    parser.add_argument("--type", type=str, choices=["driving_license", "passport"], default="driving_license",
                        help="Type of document to process (driving_license or passport)")
    parser.add_argument("--output", type=str, help="Path to save the output JSON file")
    
    args = parser.parse_args()
    
    # Check if the PDF file exists
    if not os.path.exists(args.pdf):
        logger.error(f"PDF file not found: {args.pdf}")
        return
    
    # Set default output file if not provided
    output_file = args.output
    if not output_file:
        base_name = Path(args.pdf).stem
        output_file = f"{base_name}_{args.type}_data.json"
    
    # Process the document
    try:
        logger.info(f"Processing {args.type} document: {args.pdf}")
        
        # Initialize the service
        service = IdentityDocumentGeminiService()
        
        # Process the document
        if args.type == "driving_license":
            result = service.process_driving_license(args.pdf)
        else:  # passport
            result = service.process_passport(args.pdf)
        
        # Save the result to a JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Successfully processed {args.type} document")
        logger.info(f"Output saved to: {output_file}")
        
        # Print a summary of the results
        if "document_data" in result:
            document_data = result["document_data"]
            logger.info("Document Data Summary:")
            if "fullName" in document_data:
                logger.info(f"Full Name: {document_data['fullName']}")
            if "dateOfBirth" in document_data:
                logger.info(f"Date of Birth: {document_data['dateOfBirth']}")
            if "licenseNumber" in document_data:
                logger.info(f"License Number: {document_data['licenseNumber']}")
            if "passportNumber" in document_data:
                logger.info(f"Passport Number: {document_data['passportNumber']}")
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")

if __name__ == "__main__":
    main() 