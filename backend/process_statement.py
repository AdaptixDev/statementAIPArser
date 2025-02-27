"""
Standalone script to process a financial statement using the Gemini service.
This script doesn't rely on the package being installed.
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to the Python path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.src.services.gemini_service import GeminiService
from backend.src.utils.logging_utils import setup_logger
from backend.src.config.settings import Settings

# Load environment variables from .env file if it exists
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
    print(f"Loading .env from: {env_path}")

# Explicitly set ENABLE_FILE_STORAGE to True
Settings.ENABLE_FILE_STORAGE = True

# Set up logging
logger = setup_logger("backend", level=logging.INFO)

def main():
    """Process a financial statement using the Gemini service."""
    parser = argparse.ArgumentParser(description="Process a financial statement using the Gemini service.")
    parser.add_argument("--pdf", required=True, help="Path to the PDF statement to process")
    parser.add_argument("--output", default="./output", help="Directory to save output files")
    parser.add_argument("--use-gemini", action="store_true", help="Use Gemini for processing")
    parser.add_argument("--chunk-count", type=int, default=3, help="Number of chunks to split the PDF into")
    
    args = parser.parse_args()
    
    # Check if the PDF file exists
    if not os.path.exists(args.pdf):
        logger.error(f"PDF file not found: {args.pdf}")
        return
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    try:
        # Initialize the Gemini service with the API key from Settings
        if args.use_gemini:
            # Print the API key for debugging (first few characters only)
            api_key = Settings.GOOGLE_API_KEY
            if api_key:
                masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
                logger.info(f"Using Gemini API key: {masked_key}")
            else:
                logger.warning("No Gemini API key found in settings. Will use mock data.")
            
            # Initialize the Gemini service
            gemini_service = GeminiService()
            
            # Process the PDF statement
            logger.info(f"Processing PDF statement: {args.pdf}")
            
            # Import the prompt templates from the correct location
            from backend.src.core.prompts import (
                GEMINI_STATEMENT_PARSE,
                GEMINI_PERSONAL_INFO_PARSE,
                GEMINI_TRANSACTION_SUMMARY
            )
            
            # Extract personal information
            logger.info("Extracting personal information...")
            personal_info = gemini_service.extract_personal_info(
                pdf_path=args.pdf,
                prompt_template=GEMINI_PERSONAL_INFO_PARSE
            )
            
            # Process transactions
            logger.info("Processing transactions...")
            output_csv = os.path.join(args.output, "transactions.csv") if Settings.ENABLE_FILE_STORAGE else None
            
            transactions = gemini_service.process_pdf_statement(
                pdf_path=args.pdf,
                prompt_template=GEMINI_STATEMENT_PARSE,
                output_csv_path=output_csv,
                pages_per_chunk=args.chunk_count
            )
            
            # Generate transaction summary
            if transactions:
                logger.info("Generating transaction summary...")
                summary = gemini_service.generate_transaction_summary(
                    transactions=transactions,
                    prompt_template=GEMINI_TRANSACTION_SUMMARY
                )
                # Add summary to result
                result = {
                    "personal_info": personal_info,
                    "transactions": transactions,
                    "summary": summary
                }
            
            # Save the result to a JSON file
            output_file = os.path.join(args.output, 'result.json')
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"Results saved to {output_file}")
            
            # Print summary
            logger.info(f"Summary:")
            logger.info(f"Total money in: {result['summary']['total_in']:.2f}")
            logger.info(f"Total money out: {result['summary']['total_out']:.2f}")
            logger.info(f"Net change: {result['summary']['net_change']:.2f}")
        else:
            logger.info("Gemini processing not enabled. Use --use-gemini flag to enable.")
        
    except Exception as e:
        logger.error(f"Error processing PDF statement: {str(e)}")

if __name__ == "__main__":
    main() 