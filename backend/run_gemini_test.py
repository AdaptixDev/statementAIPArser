#!/usr/bin/env python3
"""
Simple script to test the Gemini processing functionality.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.src.services.gemini_service import GeminiService
from backend.src.core.prompts import (
    GEMINI_STATEMENT_PARSE,
    GEMINI_PERSONAL_INFO_PARSE,
    GEMINI_TRANSACTION_SUMMARY
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the Gemini processing on a test PDF."""
    # Path to the test PDF
    pdf_path = "./data/Statement_163322_10185383_26_Nov_2024.pdf"
    output_dir = "./output"
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize the Gemini service
    logger.info("Initializing Gemini service...")
    gemini_service = GeminiService()
    
    try:
        # Extract personal information
        logger.info("Extracting personal information...")
        personal_info = gemini_service.extract_personal_info(
            pdf_path=pdf_path,
            prompt_template=GEMINI_PERSONAL_INFO_PARSE
        )
        logger.info(f"Personal information: {personal_info}")
        
        # Process transactions
        logger.info("Processing transactions...")
        output_csv = os.path.join(output_dir, "transactions.csv")
        transactions = gemini_service.process_pdf_statement(
            pdf_path=pdf_path,
            prompt_template=GEMINI_STATEMENT_PARSE,
            output_csv_path=output_csv,
            pages_per_chunk=3
        )
        logger.info(f"Extracted {len(transactions)} transactions")
        
        # Generate transaction summary
        if transactions:
            logger.info("Generating transaction summary...")
            summary = gemini_service.generate_transaction_summary(
                transactions=transactions,
                prompt_template=GEMINI_TRANSACTION_SUMMARY
            )
            logger.info(f"Summary: {summary}")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 