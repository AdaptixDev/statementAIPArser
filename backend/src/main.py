"""Main entry point for the backend application."""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.config.settings import Settings
from backend.src.core.statement_processor import StatementProcessor
from backend.src.utils.logging_utils import setup_logger

# Set up logging
logger = setup_logger("backend", level=logging.INFO)

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Process financial statements using AI.")
    parser.add_argument("--pdf", type=str, help="Path to the PDF statement to process")
    parser.add_argument("--output", type=str, help="Directory to save output files")
    parser.add_argument("--use-gemini", action="store_true", help="Use Gemini instead of OpenAI")
    parser.add_argument("--chunk-count", type=int, default=3, help="Number of chunks to split the PDF into (default: 3)")
    
    args = parser.parse_args()
    
    if not args.pdf:
        parser.print_help()
        return
        
    # Check if the PDF file exists
    if not os.path.exists(args.pdf):
        logger.error(f"PDF file not found: {args.pdf}")
        return
        
    # Set default output directory if not provided
    output_dir = args.output if args.output else os.path.dirname(args.pdf)
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Process the PDF statement
    try:
        processor = StatementProcessor()
        result = processor.process_pdf_statement(
            pdf_path=args.pdf,
            output_dir=output_dir,
            use_gemini=args.use_gemini,
            chunk_count=args.chunk_count
        )
        
        logger.info(f"Successfully processed PDF statement: {args.pdf}")
        logger.info(f"Output saved to: {output_dir}")
        
        # Print a summary of the results
        if result and "summary" in result:
            summary = result["summary"]
            logger.info("Summary:")
            if isinstance(summary, dict):
                if "summaryOfIncomeAndOutgoings" in summary:
                    income = summary["summaryOfIncomeAndOutgoings"]["income"]
                    outgoings = summary["summaryOfIncomeAndOutgoings"]["outgoings"]
                    total_in = sum(income.values())
                    total_out = sum(outgoings.values())
                    net_change = total_in - total_out
                    logger.info(f"Total money in: {total_in:.2f}")
                    logger.info(f"Total money out: {total_out:.2f}")
                    logger.info(f"Net change: {net_change:.2f}")
                    
                # Log some of the insights and recommendations
                if "recommendations" in summary:
                    logger.info("Recommendations:")
                    for rec in summary["recommendations"]:
                        logger.info(f"- {rec}")
            
    except Exception as e:
        logger.error(f"Error processing PDF statement: {str(e)}")
        
if __name__ == "__main__":
    main() 