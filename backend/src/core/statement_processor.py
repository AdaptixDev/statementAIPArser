"""Core functionality for processing financial statements."""

import os
import time
import logging
import tempfile
import csv
import shutil
import json
import io
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    # Try importing from backend.src (when running from root directory)
    from backend.src.config.settings import Settings
    from backend.src.utils.exceptions import FileProcessingError
    from backend.src.utils.pdf_utils import PDFConverter, ImageData
    from backend.src.services.openai_service import OpenAIAssistantService
    from backend.src.services.gemini_service import GeminiService, CSV_HEADERS
    from backend.src.core.prompts import (
        GEMINI_STATEMENT_PARSE,
        GEMINI_PERSONAL_INFO_PARSE,
        GEMINI_TRANSACTION_SUMMARY,
        GEMINI_TRANSACTION_CATEGORISATION
    )
    from backend.src.core.data_processor import DataProcessor
except ImportError:
    # Try importing from src (when running from backend directory)
    from src.config.settings import Settings
    from src.utils.exceptions import FileProcessingError
    from src.utils.pdf_utils import PDFConverter, ImageData
    from src.services.openai_service import OpenAIAssistantService
    from src.services.gemini_service import GeminiService, CSV_HEADERS
    from src.core.prompts import (
        GEMINI_STATEMENT_PARSE,
        GEMINI_PERSONAL_INFO_PARSE,
        GEMINI_TRANSACTION_SUMMARY,
        GEMINI_TRANSACTION_CATEGORISATION
    )
    from src.core.data_processor import DataProcessor

logger = logging.getLogger(__name__)

# Global in-memory stores when file storage is disabled
in_memory_transactions = []  # List to collect transaction JSON responses
in_memory_personal_info = None  # To hold the personal info extraction JSON

class StatementProcessor:
    """Core functionality for processing financial statements."""
    
    def __init__(self):
        """Initialize the statement processor."""
        self.data_processor = DataProcessor()
        self.openai_service = None
        self.gemini_service = None
        
    def _get_openai_service(self) -> OpenAIAssistantService:
        """Get the OpenAI service."""
        if not self.openai_service:
            self.openai_service = OpenAIAssistantService()
        return self.openai_service
    
    def _get_gemini_service(self) -> GeminiService:
        """Get the Gemini service."""
        if not self.gemini_service:
            self.gemini_service = GeminiService()
        return self.gemini_service
    
    def process_front_page_personal_info(
        self,
        front_image: ImageData,
        use_gemini: bool = False
    ) -> Dict[str, Any]:
        """
        Process the front page image to extract personal information.
        
        Args:
            front_image: Front page image data (file path or in-memory tuple)
            use_gemini: Whether to use Gemini instead of OpenAI
            
        Returns:
            Dictionary containing extracted personal information
        """
        try:
            if use_gemini:
                # Use Gemini for personal info extraction
                gemini = self._get_gemini_service()
                
                if isinstance(front_image, tuple):
                    # front_image is (pseudo_filename, image_bytes)
                    file_name, _ = front_image
                    # Save to a temporary file for Gemini processing
                    temp_path = os.path.join(os.getcwd(), "temp_front_page.jpg")
                    with open(temp_path, "wb") as f:
                        f.write(front_image[1])
                    original_identifier = file_name
                    file_path = temp_path
                else:
                    # front_image is a file path
                    file_path = front_image
                    original_identifier = front_image
                    
                logger.info(f"Processing personal information extraction with Gemini for: {original_identifier}")
                personal_info = gemini.extract_personal_info(
                    pdf_path=file_path,
                    page_image_path=file_path if file_path.endswith(('.jpg', '.jpeg', '.png')) else None
                )
                
                # Clean up temporary file if created
                if isinstance(front_image, tuple) and os.path.exists(temp_path):
                    os.remove(temp_path)
                    
            else:
                # Use OpenAI for personal info extraction
                if isinstance(front_image, tuple):
                    # front_image is (pseudo_filename, image_bytes)
                    file_name, file_bytes = front_image
                    logger.info(f"Processing personal information extraction for in-memory front image: {file_name}")
                    original_identifier = file_name
                else:
                    # front_image is a file path
                    logger.info(f"Processing personal information extraction for: {os.path.basename(front_image)}")
                    with open(front_image, "rb") as f:
                        file_bytes = f.read()
                    file_name = os.path.basename(front_image)
                    original_identifier = front_image
                    
                # Send to OpenAI Assistant
                personal_info = self._get_openai_service().extract_personal_info(
                    file_bytes=file_bytes,
                    file_name=file_name
                )
                
            logger.info(f"Personal information extraction response: {personal_info}")
            
            # Store in memory if file storage is disabled
            global in_memory_personal_info
            in_memory_personal_info = personal_info
            
            return personal_info
            
        except Exception as e:
            logger.error(f"Error processing front page personal info: {str(e)}")
            raise FileProcessingError(f"Error processing front page personal info: {str(e)}")
            
    def process_statement_pages(
        self,
        image_files: List[ImageData],
        use_gemini: bool = False,
        output_csv: Optional[str] = None,
        export_raw_responses: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Process statement pages to extract transaction data.
        
        Args:
            image_files: List of image data (file paths or in-memory tuples)
            use_gemini: Whether to use Gemini instead of OpenAI
            output_csv: Path to save the output CSV (optional)
            export_raw_responses: Whether to export raw responses (overrides Settings.EXPORT_RAW_GEMINI_RESPONSES)
            
        Returns:
            List of transaction dictionaries
        """
        try:
            all_transactions = []
            
            if use_gemini:
                # Use Gemini for transaction extraction
                gemini = self._get_gemini_service()
                
                # For Gemini, we need to process the entire PDF at once
                # So we need to convert the image files back to a PDF
                if isinstance(image_files[0], tuple):
                    # image_files contains (pseudo_filename, image_bytes) tuples
                    # Save to temporary files for Gemini processing
                    temp_dir = os.path.join(os.getcwd(), "temp_images")
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                        
                    temp_files = []
                    for i, (file_name, file_bytes) in enumerate(image_files):
                        temp_path = os.path.join(temp_dir, f"temp_page_{i}.jpg")
                        with open(temp_path, "wb") as f:
                            f.write(file_bytes)
                        temp_files.append(temp_path)
                        
                    # TODO: Convert temp_files to a PDF
                    # For now, just process the first image
                    pdf_path = temp_files[0]
                    
                else:
                    # image_files contains file paths
                    # TODO: Convert image files to a PDF
                    # For now, just process the first image
                    pdf_path = image_files[0]
                    
                logger.info(f"Processing statement with Gemini")
                
                # Determine output directory for raw responses
                output_dir = None
                if output_csv:
                    output_dir = os.path.dirname(output_csv)
                
                # Get both transactions and raw response
                transactions, raw_response = gemini.process_pdf_statement_with_raw_response(
                    pdf_path=pdf_path,
                    prompt_template=GEMINI_STATEMENT_PARSE,
                    export_raw_responses=export_raw_responses,
                    output_dir=output_dir
                )
                
                # Save the raw response if output_csv is provided
                if output_csv and raw_response:
                    raw_output_path = output_csv.replace(".csv", "_raw.txt")
                    with open(raw_output_path, "w", encoding="utf-8") as f:
                        f.write(raw_response)
                    logger.info(f"Raw response saved to {raw_output_path}")
                
                # Add transactions to the result
                all_transactions.extend(transactions)
                
                # Categorize transactions
                if all_transactions:
                    logger.info("Categorizing transactions with Gemini...")
                    # Create a CSV from all transactions without categories
                    csv_content = io.StringIO()
                    writer = csv.DictWriter(csv_content, fieldnames=['Date', 'Description', 'Amount', 'Direction', 'Balance'])
                    writer.writeheader()
                    for transaction in all_transactions:
                        # Create a copy without the Category field
                        transaction_without_category = {k: v for k, v in transaction.items() if k != 'Category'}
                        writer.writerow(transaction_without_category)
                    
                    # Categorize transactions
                    categorized_csv = gemini.categorize_transactions(csv_content.getvalue())
                    
                    # Parse categorized CSV back to transactions
                    all_transactions = gemini.parse_csv_to_transactions(categorized_csv)
                    logger.info(f"Successfully categorized {len(all_transactions)} transactions")
                
                # Clean up temporary files
                if isinstance(image_files[0], tuple) and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"Removed temporary directory: {temp_dir}")
            else:
                # Use OpenAI for transaction extraction
                openai = self._get_openai_service()
                
                # Process each image separately
                for image_data in image_files:
                    if isinstance(image_data, tuple):
                        # image_data is (pseudo_filename, image_bytes)
                        file_name, file_bytes = image_data
                        logger.info(f"Processing statement page: {file_name}")
                        original_identifier = file_name
                    else:
                        # image_data is a file path
                        logger.info(f"Processing statement page: {os.path.basename(image_data)}")
                        with open(image_data, "rb") as f:
                            file_bytes = f.read()
                        file_name = os.path.basename(image_data)
                        original_identifier = image_data
                        
                    # Send to OpenAI Assistant
                    response = openai.extract_transactions(
                        file_bytes=file_bytes,
                        file_name=file_name
                    )
                    
                    # Extract transactions from the response
                    if isinstance(response, list):
                        transactions = response
                    elif isinstance(response, dict) and 'transactions' in response:
                        transactions = response['transactions']
                    else:
                        transactions = [response]
                        
                    all_transactions.extend(transactions)
                    
                    # Store in memory if file storage is disabled
                    global in_memory_transactions
                    in_memory_transactions.extend(transactions)
                    
                    # Add a small delay to avoid rate limiting
                    time.sleep(1)
                    
            # Export to CSV if requested
            if output_csv and all_transactions and Settings.ENABLE_FILE_STORAGE:
                self.data_processor.export_transactions_to_csv(
                    transactions=all_transactions,
                    output_file=output_csv
                )
                
            return all_transactions
            
        except Exception as e:
            logger.error(f"Error processing statement pages: {str(e)}")
            raise FileProcessingError(f"Error processing statement pages: {str(e)}")
            
    def process_pdf_statement(
        self,
        pdf_path: str,
        output_dir: str,
        use_gemini: bool = False,
        chunk_count: int = 3
    ) -> Dict[str, Any]:
        """
        Process a PDF statement and extract transactions and personal information.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save output files
            use_gemini: Whether to use Gemini instead of OpenAI
            chunk_count: Number of chunks to split the PDF into
            
        Returns:
            Dictionary containing the extracted data
        """
        try:
            logger.info(f"Processing PDF statement: {pdf_path}")
            
            # Create the output directory if it doesn't exist
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Process with Gemini or OpenAI
            if use_gemini:
                # Get the Gemini service
                gemini = self._get_gemini_service()
                
                # Create a temporary directory for storing sub-PDFs
                temp_dir = tempfile.mkdtemp()
                logger.info(f"Created temporary directory: {temp_dir}")
                
                try:
                    # Step 1: Split the PDF into chunks
                    logger.info(f"Splitting PDF into {chunk_count} chunks")
                    smaller_pdfs = gemini.split_pdf_into_subpdfs(pdf_path, chunk_count, temp_dir)
                    
                    # Store the first chunk path for additional processing later
                    first_chunk_path = smaller_pdfs[0] if smaller_pdfs else None
                    
                    # Step 2: Process each chunk for transactions
                    all_transactions = []
                    
                    logger.info("Starting processing of sub-PDFs...")
                    for i, chunk_path in enumerate(smaller_pdfs, start=1):
                        logger.info(f"Processing chunk {i}/{len(smaller_pdfs)} for transactions")
                        # Get the raw response and transactions
                        chunk_transactions, raw_response = gemini.process_pdf_statement_with_raw_response(
                            pdf_path=chunk_path,
                            prompt_template=GEMINI_STATEMENT_PARSE
                        )
                        all_transactions.extend(chunk_transactions)
                        
                        # Save the raw response to a file if file storage is enabled
                        if Settings.ENABLE_FILE_STORAGE:
                            raw_response_file = os.path.join(output_dir, f"raw_response_chunk_{i}.csv")
                            logger.info(f"Saving raw Gemini response for chunk {i} to: {raw_response_file}")
                            with open(raw_response_file, "w", encoding="utf-8") as f:
                                f.write(raw_response)
                    
                    # Save all transactions to CSV
                    output_csv = os.path.join(output_dir, "transactions.csv") if Settings.ENABLE_FILE_STORAGE else None
                    if output_csv:
                        logger.info(f"Saving {len(all_transactions)} transactions to CSV: {output_csv}")
                        with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
                            writer.writeheader()
                            writer.writerows(all_transactions)
                    
                    # Step 3: Extract personal information from the first chunk
                    logger.info("Starting additional processing for the first chunk to extract personal information...")
                    personal_info = gemini.extract_personal_info(
                        pdf_path=first_chunk_path,
                        prompt_template=GEMINI_PERSONAL_INFO_PARSE
                    )
                    
                    # Step 4: Generate transaction summary
                    logger.info("Sending final transactions to Gemini for transaction summary...")
                    summary = gemini.generate_transaction_summary(
                        transactions=all_transactions,
                        prompt_template=GEMINI_TRANSACTION_SUMMARY
                    )
                    
                finally:
                    # Clean up temporary directory
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"Removed temporary directory: {temp_dir}")
            else:
                # For OpenAI, we need to convert PDF to images
                converter = PDFConverter()
                front_page, all_pages = converter.pdf_to_images(
                    pdf_path=pdf_path,
                    output_dir=os.path.join(output_dir, "images") if Settings.ENABLE_FILE_STORAGE else None
                )
                
                # Get the OpenAI service
                openai = self._get_openai_service()
                
                # Extract personal information from the front page
                if front_page:
                    logger.info("Processing front page for personal information extraction")
                    if isinstance(front_page, tuple):
                        # front_image is (pseudo_filename, image_bytes)
                        file_name, file_bytes = front_page
                        logger.info(f"Processing personal information extraction for in-memory front image: {file_name}")
                    else:
                        # front_image is a file path
                        logger.info(f"Processing personal information extraction for: {os.path.basename(front_page)}")
                        with open(front_page, "rb") as f:
                            file_bytes = f.read()
                        file_name = os.path.basename(front_page)
                    
                    # Send to OpenAI Assistant
                    personal_info = openai.extract_personal_info(
                        file_bytes=file_bytes,
                        file_name=file_name
                    )
                else:
                    personal_info = {}
                
                # Process each page for transactions
                transactions = []
                for page in all_pages:
                    if isinstance(page, tuple):
                        # page is (pseudo_filename, image_bytes)
                        file_name, file_bytes = page
                        logger.info(f"Processing transactions for in-memory page: {file_name}")
                    else:
                        # page is a file path
                        logger.info(f"Processing transactions for: {os.path.basename(page)}")
                        with open(page, "rb") as f:
                            file_bytes = f.read()
                        file_name = os.path.basename(page)
                    
                    # Send to OpenAI Assistant
                    page_transactions = openai.extract_transactions(
                        file_bytes=file_bytes,
                        file_name=file_name
                    )
                    transactions.extend(page_transactions)
                
                # Generate transaction summary
                summary = openai.generate_transaction_summary(transactions)
                
                # Save transactions to CSV
                output_csv = os.path.join(output_dir, "transactions.csv") if Settings.ENABLE_FILE_STORAGE else None
                if output_csv:
                    logger.info(f"Saving {len(transactions)} transactions to CSV: {output_csv}")
                    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
                        writer.writeheader()
                        writer.writerows(transactions)
                
                all_transactions = transactions
            
            # Merge personal information and transactions
            output_json = os.path.join(output_dir, "result.json") if Settings.ENABLE_FILE_STORAGE else None
            result = {
                "personal_info": personal_info,
                "transactions": all_transactions,
                "summary": summary
            }
            
            # Save the result to a JSON file
            if output_json:
                with open(output_json, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Saved result to JSON: {output_json}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF statement: {str(e)}")
            raise FileProcessingError(f"Error processing PDF statement: {str(e)}")

    def process_pdf_statement_with_gemini(
        self,
        pdf_path: str,
        output_dir: str,
        chunk_count: int = 3,
        output_json: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a PDF statement using Gemini.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save output files
            chunk_count: Number of chunks to split the PDF into
            output_json: Path to save the output JSON file
            
        Returns:
            Dictionary containing the result
        """
        logger.info(f"Processing PDF statement with Gemini: {pdf_path}")
        
        try:
            # Get the Gemini service
            gemini = self._get_gemini_service()
            
            # Create a temporary directory for storing sub-PDFs
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Created temporary directory: {temp_dir}")
            
            try:
                # Step 1: Split the PDF into chunks
                logger.info(f"Splitting PDF into {chunk_count} chunks")
                smaller_pdfs = gemini.split_pdf_into_subpdfs(pdf_path, chunk_count, temp_dir)
                
                # Process each chunk for transactions
                all_transactions = []
                
                logger.info("Starting processing of sub-PDFs...")
                for i, chunk_path in enumerate(smaller_pdfs, start=1):
                    logger.info(f"Processing chunk {i}/{len(smaller_pdfs)} for transactions")
                    # Get the raw response and transactions
                    chunk_transactions, raw_response = gemini.process_pdf_statement_with_raw_response(
                        pdf_path=chunk_path,
                        prompt_template=GEMINI_STATEMENT_PARSE
                    )
                    all_transactions.extend(chunk_transactions)
                    
                    # Save the raw response to a file if file storage is enabled
                    if Settings.ENABLE_FILE_STORAGE:
                        raw_response_file = os.path.join(output_dir, f"raw_response_chunk_{i}.csv")
                        logger.info(f"Saving raw Gemini response for chunk {i} to: {raw_response_file}")
                        with open(raw_response_file, "w", encoding="utf-8") as f:
                            f.write(raw_response)
                
                # Save all transactions to CSV
                if Settings.ENABLE_FILE_STORAGE:
                    csv_path = os.path.join(output_dir, "transactions.csv")
                    logger.info(f"Saving {len(all_transactions)} transactions to CSV: {csv_path}")
                    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
                        writer.writeheader()
                        writer.writerows(all_transactions)
                
                transactions = all_transactions
            finally:
                # Clean up: remove all sub-PDFs in the temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"Removed temporary directory: {temp_dir}")
            
            # Extract personal information from the PDF
            logger.info("Step 2: Extracting personal information from PDF")
            personal_info = gemini.extract_personal_info(pdf_path)
            logger.info("Personal information extracted")
            
            # Generate transaction summary
            logger.info("Step 3: Generating transaction summary")
            summary = gemini.generate_transaction_summary(transactions)
            logger.info("Transaction summary generated")
            
            # Combine results
            result = {
                "personal_info": personal_info,
                "transactions": transactions,
                "summary": summary
            }
            
            # Save result to JSON
            if output_json or Settings.ENABLE_FILE_STORAGE:
                json_path = output_json or os.path.join(output_dir, "result.json")
                logger.info(f"Saving result to JSON: {json_path}")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF statement with Gemini: {str(e)}")
            raise FileProcessingError(f"Error processing PDF statement with Gemini: {str(e)}") 