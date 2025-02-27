#!/usr/bin/env python3
"""
Direct test of the gemini_service.py functionality.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for the Gemini API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY is not set in the environment.")
    sys.exit(1)

# Import directly from the original file
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.services.gemini_service_backup import GeminiService

def main():
    """Run the Gemini processing on a test PDF."""
    try:
        # Path to the test PDF
        pdf_path = "./data/Statement_163322_10185383_26_Nov_2024.pdf"
        output_dir = "./output"
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize the Gemini service
        logger.info("Initializing Gemini service...")
        gemini_service = GeminiService()
        
        # Process the PDF
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract personal information
        logger.info("Extracting personal information...")
        personal_info = gemini_service.extract_personal_info(pdf_path)
        logger.info(f"Personal information: {personal_info}")
        
        # Process transactions
        logger.info("Processing transactions...")
        output_csv = os.path.join(output_dir, "transactions.csv")
        transactions = gemini_service.process_pdf_statement(
            pdf_path=pdf_path,
            output_csv_path=output_csv,
            pages_per_chunk=3
        )
        logger.info(f"Extracted {len(transactions)} transactions")
        
        # Generate transaction summary
        if transactions:
            logger.info("Generating transaction summary...")
            summary = gemini_service.generate_transaction_summary(transactions)
            logger.info(f"Summary: {summary}")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 