#!/usr/bin/env python3
"""
Integration with Gemini 2.0 for processing various document types.
This module provides a base service for Gemini API interactions and specialized
services for different document types like financial statements and identity documents.
"""

import os
import time
import json
import csv
import io
import logging
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PyPDF2 import PdfReader, PdfWriter
import shutil
import tempfile

# Import prompts from the core module
try:
    # Try importing from backend.src (when running from root directory)
    from backend.src.core.prompts import (
        GEMINI_STATEMENT_PARSE,
        GEMINI_PERSONAL_INFO_PARSE,
        GEMINI_TRANSACTION_SUMMARY,
        GEMINI_TRANSACTION_CATEGORISATION
    )
    from backend.src.config.settings import Settings
except ImportError:
    # Try importing from src (when running from backend directory)
    from src.core.prompts import (
        GEMINI_STATEMENT_PARSE,
        GEMINI_PERSONAL_INFO_PARSE,
        GEMINI_TRANSACTION_SUMMARY,
        GEMINI_TRANSACTION_CATEGORISATION
    )
    from src.config.settings import Settings

# CSV Headers for statement processing
CSV_HEADERS = ['Date', 'Description', 'Amount', 'Direction', 'Balance', 'Category']
CSV_HEADERS_WITHOUT_CATEGORY = ['Date', 'Description', 'Amount', 'Direction', 'Balance']

# Configure logging
logger = logging.getLogger(__name__)

# --- Custom in-memory PDF file with MIME type ---
class MemoryPDF(io.BytesIO):
    def __init__(self, name, *args, **kwargs):
        """
        Initialize the in-memory file and assign the filename and MIME type.
        """
        super().__init__(*args, **kwargs)
        self.name = name
        self.mime_type = "application/pdf"
        
    def __fspath__(self):
        """
        Return the file's name for os.fspath() so that the external libraries
        (like Gemini's client) can infer the MIME type from the '.pdf' extension.
        """
        return self.name


class GeminiService:
    """
    Base service for interacting with the Gemini API.
    Provides core functionality for processing documents with Gemini.
    """
    
    def __init__(self):
        """Initialize the Gemini service with API credentials."""
        # Load environment variables
        load_dotenv()
        
        # Get API key
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
            
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        logger.info("Gemini client initialized successfully")
        
    def split_pdf_into_subpdfs(self, original_pdf_path: str, chunk_count: int, temp_dir: str) -> list:
        """
        Splits the PDF at `original_pdf_path` into `chunk_count` smaller PDFs,
        storing them in `temp_dir`. Returns a list of file paths for the sub-PDFs.
        """
        logger.info(f"Splitting PDF \"{original_pdf_path}\" into {chunk_count} sub-PDFs...")
        reader = PdfReader(original_pdf_path)
        total_pages = len(reader.pages)
        base_name = Path(original_pdf_path).stem
        extension = Path(original_pdf_path).suffix

        pages_per_chunk = max(1, (total_pages + chunk_count - 1) // chunk_count)
        subpdf_paths = []
        start_page = 0
        chunk_idx = 1

        while start_page < total_pages and chunk_idx <= chunk_count:
            end_page = min(start_page + pages_per_chunk, total_pages)
            logger.info(f"Creating sub-PDF #{chunk_idx}: pages {start_page + 1} to {end_page}...")
            
            writer = PdfWriter()
            for i in range(start_page, end_page):
                writer.add_page(reader.pages[i])

            # Write the sub-PDF to disk in the temp directory
            subpdf_filename = f"{base_name}_chunk_{chunk_idx}{extension}"
            subpdf_path = os.path.join(temp_dir, subpdf_filename)

            with open(subpdf_path, "wb") as f:
                writer.write(f)

            subpdf_paths.append(subpdf_path)
            start_page = end_page
            chunk_idx += 1

        logger.info(f"Completed splitting PDF into {len(subpdf_paths)} sub-PDFs")
        return subpdf_paths
    
    def upload_to_gemini(self, file_path: str) -> object:
        """
        Uploads a file to Gemini and returns the file object.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            The uploaded file object
        """
        logger.info(f"Uploading file \"{file_path}\" to Gemini...")
        
        # Upload the file to Gemini
        file_obj = self.client.files.upload(file=file_path)
        logger.info(f"Uploaded file '{file_obj.display_name}' as: {file_obj.uri}")
        
        return file_obj
    
    def wait_for_files_active(self, files: list) -> None:
        """
        Waits for the given files to be active (state=ACTIVE) with periodic logging.
        Raises an exception if any file fails to become ACTIVE.
        
        Args:
            files: List of file objects to wait for
        """
        logger.info("Waiting for file(s) to become ACTIVE in Gemini...")
        for file_obj in files:
            current_file = self.client.files.get(name=file_obj.name)
            while current_file.state.name == "PROCESSING":
                logger.info("...still processing, waiting 10 seconds...")
                time.sleep(10)
                current_file = self.client.files.get(name=file_obj.name)
            if current_file.state.name != "ACTIVE":
                raise Exception(
                    f"File {current_file.name} failed to process. "
                    f"Current state: {current_file.state.name}"
                )
        logger.info("All file(s) ready")
    
    def generate_content(self, prompt: str, file_obj: object, max_output_tokens: int = 400000, export_path: str = None) -> str:
        """
        Generates content using Gemini with the given prompt and file.
        
        Args:
            prompt: The prompt to use
            file_obj: The file object to process
            max_output_tokens: Maximum number of tokens to generate
            export_path: Path to export the raw response (if Settings.EXPORT_RAW_GEMINI_RESPONSES is True)
            
        Returns:
            The generated text response
        """
        logger.info("Sending prompt with file to Gemini...")
        
        # Generate content
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, file_obj],
            config=types.GenerateContentConfig(max_output_tokens=max_output_tokens),
        )
        
        # Export raw response if enabled and export_path is provided
        if export_path and Settings.EXPORT_RAW_GEMINI_RESPONSES:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(export_path), exist_ok=True)
                
                # Write response to file
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info(f"Raw Gemini response exported to: {export_path}")
            except Exception as e:
                logger.warning(f"Failed to export raw Gemini response: {str(e)}")
        
        return response.text
    
    def process_document(self, pdf_path: str, chunk_count: int = 3) -> dict:
        """
        Base method for processing a document with Gemini.
        This should be overridden by subclasses to implement document-specific processing.
        
        Args:
            pdf_path: Path to the PDF file to process
            chunk_count: Number of chunks to split the PDF into
            
        Returns:
            A dictionary containing the processing results
        """
        raise NotImplementedError("Subclasses must implement process_document()")

    def process_pdf_statement_with_raw_response(self, pdf_path: str, prompt_template: str = GEMINI_STATEMENT_PARSE, export_raw_responses: bool = False, output_dir: str = None) -> tuple:
        """
        Process a PDF statement and return both the transactions and the raw CSV response.
        
        Args:
            pdf_path: Path to the PDF file
            prompt_template: Template for the prompt to send to Gemini
            export_raw_responses: Whether to export raw responses (overrides Settings.EXPORT_RAW_GEMINI_RESPONSES)
            output_dir: Directory to export raw responses to (if None, uses the directory of pdf_path)
            
        Returns:
            Tuple containing (list of transaction dictionaries, raw CSV response)
        """
        logger.info(f"Processing PDF statement with raw response: {pdf_path}")
        
        # Determine output directory for raw responses
        if export_raw_responses and output_dir is None:
            output_dir = os.path.dirname(pdf_path)
        
        # Override Settings.EXPORT_RAW_GEMINI_RESPONSES if export_raw_responses is True
        original_export_setting = Settings.EXPORT_RAW_GEMINI_RESPONSES
        if export_raw_responses:
            Settings.EXPORT_RAW_GEMINI_RESPONSES = True
        
        try:
            # Upload the PDF to Gemini
            pdf_obj = self.upload_to_gemini(pdf_path)
            
            # Wait for the file to be active
            self.wait_for_files_active([pdf_obj])
            
            # Prepare export path
            export_path = None
            if Settings.EXPORT_RAW_GEMINI_RESPONSES and output_dir:
                export_path = os.path.join(output_dir, "raw_gemini_statement_parse.txt")
            
            # Process with the provided prompt template
            response_text = self.generate_content(
                prompt_template, 
                pdf_obj,
                export_path=export_path
            )
            
            # Extract CSV from the response
            csv_content = self.extract_csv_from_response(response_text)
            
            # Parse the CSV to transactions
            transactions = self.parse_csv_to_transactions(csv_content)
            
            # Return both the transactions and the raw CSV response
            return transactions, response_text
        finally:
            # Restore original export setting
            Settings.EXPORT_RAW_GEMINI_RESPONSES = original_export_setting

    def extract_csv_from_response(self, text: str) -> str:
        """
        Returns the CSV content from the response, handling both code-fenced and raw CSV.
        """
        # First try to find code-fenced CSV
        lines = text.split('\n')
        in_csv_block = False
        csv_lines = []

        for line in lines:
            if line.strip().startswith('```csv'):
                in_csv_block = True
                continue
            elif in_csv_block and line.strip().startswith('```'):
                break
            elif in_csv_block:
                csv_lines.append(line)

        if csv_lines:
            return '\n'.join(csv_lines).strip()

        # If no code fence found, try to extract CSV directly
        # (assuming it starts with the header row)
        for i, line in enumerate(lines):
            if any(header in line for header in ['Date', 'Description', 'Amount']):
                return '\n'.join(lines[i:]).strip()

        return text  # Return full text if no clear CSV structure found
        
    def parse_csv_to_transactions(self, csv_text: str) -> list:
        """
        Parse CSV text into a list of transaction dictionaries.
        
        Args:
            csv_text: CSV text to parse
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        
        try:
            # Use csv.reader to parse the CSV
            reader = csv.reader(io.StringIO(csv_text))
            
            # Process each row
            for row in reader:
                # Skip empty rows
                if not row or all(not cell.strip() for cell in row):
                    continue
                
                # Clean up the data
                def clean(text):
                    return text.strip().replace('\n', ' ').replace('\r', '')
                
                # Create a dictionary for this transaction
                cleaned_row = {
                    'Date': '',
                    'Description': '',
                    'Amount': '',
                    'Direction': '',
                    'Balance': '',
                    'Category': ''
                }
                
                # Map the columns to the dictionary
                if len(row) > 0:
                    cleaned_row['Date'] = clean(row[0].replace('Date:', ''))
                if len(row) > 1:
                    cleaned_row['Description'] = clean(row[1].replace('Description:', ''))
                if len(row) > 2:
                    cleaned_row['Amount'] = clean(row[2].replace('Amount:', ''))
                if len(row) > 3:
                    cleaned_row['Direction'] = clean(row[3].replace('Direction:', ''))
                if len(row) > 4:
                    cleaned_row['Balance'] = clean(row[4].replace('Balance:', ''))
                if len(row) > 5:
                    cleaned_row['Category'] = clean(row[5].replace('Category:', ''))
                
                # Only add rows with at least a Date or Description
                if cleaned_row['Date'] or cleaned_row['Description']:
                    transactions.append(cleaned_row)
                
        except Exception as e:
            logger.warning(f"Error parsing CSV: {e}")
            logger.debug(f"Raw CSV content: {csv_text[:500]}")  # Print first 500 chars for debugging

        return transactions

    def categorize_transactions(self, transactions_csv: str, prompt_template: str = GEMINI_TRANSACTION_CATEGORISATION, export_path: str = None) -> str:
        """
        Categorize transactions using Gemini.
        
        Args:
            transactions_csv: CSV string containing transaction data
            prompt_template: Prompt template for categorization
            export_path: Path to export the raw response (if Settings.EXPORT_RAW_GEMINI_RESPONSES is True)
            
        Returns:
            CSV string with categorized transactions
        """
        logger.info(f"Categorizing transactions with Gemini")
        
        try:
            # Send to Gemini with the categorization prompt
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt_template, transactions_csv],
                config=types.GenerateContentConfig(max_output_tokens=400000),
            )
            
            # Extract CSV from response
            categorized_csv = response.text
            
            # Export raw response if enabled and export_path is provided
            if export_path and Settings.EXPORT_RAW_GEMINI_RESPONSES:
                try:
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(export_path), exist_ok=True)
                    
                    # Write response to file
                    with open(export_path, 'w', encoding='utf-8') as f:
                        f.write(categorized_csv)
                    logger.info(f"Raw categorization response exported to: {export_path}")
                except Exception as e:
                    logger.warning(f"Failed to export raw categorization response: {str(e)}")
            
            logger.info(f"Successfully categorized transactions")
            
            return categorized_csv
        except Exception as e:
            logger.exception(f"Error categorizing transactions: {str(e)}")
            raise APIError(f"Error categorizing transactions: {str(e)}")


class StatementGeminiService(GeminiService):
    """
    Specialized service for processing financial statements with Gemini.
    """
    
    def process_document(self, pdf_path: str, chunk_count: int = 3, export_raw_responses: bool = False, output_dir: str = None) -> dict:
        """
        Process a financial statement PDF with Gemini.
        
        Args:
            pdf_path: Path to the PDF file to process
            chunk_count: Number of chunks to split the PDF into
            export_raw_responses: Whether to export raw responses (overrides Settings.EXPORT_RAW_GEMINI_RESPONSES)
            output_dir: Directory to export raw responses to (if None, uses the directory of pdf_path)
            
        Returns:
            A dictionary containing the processing results
        """
        # Create a temporary directory for storing sub-PDFs
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {temp_dir}")
        
        # Determine output directory for raw responses
        if export_raw_responses and output_dir is None:
            output_dir = os.path.dirname(pdf_path)
        
        # Override Settings.EXPORT_RAW_GEMINI_RESPONSES if export_raw_responses is True
        original_export_setting = Settings.EXPORT_RAW_GEMINI_RESPONSES
        if export_raw_responses:
            Settings.EXPORT_RAW_GEMINI_RESPONSES = True
        
        try:
            # Split the PDF into sub-PDFs
            smaller_pdfs = self.split_pdf_into_subpdfs(pdf_path, chunk_count, temp_dir)
            
            # Process each sub-PDF
            all_transactions = []
            first_chunk_path = smaller_pdfs[0] if smaller_pdfs else None
            
            logger.info("Starting processing of sub-PDFs...")
            for i, subpdf_path in enumerate(smaller_pdfs, start=1):
                # Upload chunk to Gemini
                pdf_obj = self.upload_to_gemini(subpdf_path)
                
                # Wait for the file to be active
                self.wait_for_files_active([pdf_obj])
                
                # Prepare export path for this chunk
                export_path = None
                if Settings.EXPORT_RAW_GEMINI_RESPONSES and output_dir:
                    export_path = os.path.join(output_dir, f"raw_gemini_statement_parse_chunk_{i}.txt")
                
                # Process with GEMINI_STATEMENT_PARSE prompt
                response_text = self.generate_content(
                    GEMINI_STATEMENT_PARSE, 
                    pdf_obj,
                    export_path=export_path
                )
                
                # Extract CSV and parse transactions
                csv_content = self.extract_csv_from_response(response_text)
                chunk_transactions = self.parse_csv_to_transactions(csv_content)
                
                # Categorize transactions for this chunk immediately
                if chunk_transactions:
                    logger.info(f"Categorizing transactions for chunk {i}...")
                    # Create a CSV from chunk transactions without categories
                    csv_content = io.StringIO()
                    writer = csv.DictWriter(csv_content, fieldnames=CSV_HEADERS_WITHOUT_CATEGORY)
                    writer.writeheader()
                    for transaction in chunk_transactions:
                        # Create a copy without the Category field
                        transaction_without_category = {k: v for k, v in transaction.items() if k != 'Category'}
                        writer.writerow(transaction_without_category)
                    
                    # Prepare export path for categorization of this chunk
                    categorization_export_path = None
                    if Settings.EXPORT_RAW_GEMINI_RESPONSES and output_dir:
                        categorization_export_path = os.path.join(output_dir, f"raw_gemini_categorization_chunk_{i}.txt")
                    
                    # Categorize transactions for this chunk
                    categorized_csv = self.categorize_transactions(
                        csv_content.getvalue(),
                        export_path=categorization_export_path
                    )
                    
                    # Parse categorized CSV back to transactions
                    categorized_chunk_transactions = self.parse_csv_to_transactions(categorized_csv)
                    logger.info(f"Successfully categorized {len(categorized_chunk_transactions)} transactions for chunk {i}")
                    
                    # Add categorized transactions to the main list
                    all_transactions.extend(categorized_chunk_transactions)
                else:
                    logger.info(f"No transactions found in chunk {i}, skipping categorization")
            
            # Process personal information from the first chunk
            personal_info = None
            if first_chunk_path:
                logger.info("Processing first chunk for personal information...")
                
                # Upload the first chunk again
                first_chunk_obj = self.upload_to_gemini(first_chunk_path)
                
                # Wait for it to be active
                self.wait_for_files_active([first_chunk_obj])
                
                # Prepare export path for personal info
                personal_info_export_path = None
                if Settings.EXPORT_RAW_GEMINI_RESPONSES and output_dir:
                    personal_info_export_path = os.path.join(output_dir, "raw_gemini_personal_info.txt")
                
                # Process with GEMINI_PERSONAL_INFO_PARSE prompt
                personal_info_response = self.generate_content(
                    GEMINI_PERSONAL_INFO_PARSE, 
                    first_chunk_obj,
                    export_path=personal_info_export_path
                )
                personal_info = personal_info_response.strip()
            
            # Generate transaction summary
            summary = None
            if all_transactions:
                # Create a CSV from all transactions
                csv_content = io.StringIO()
                writer = csv.DictWriter(csv_content, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(all_transactions)
                
                # Add personal info to the top
                if personal_info:
                    csv_with_personal_info = f"# Personal Information: {personal_info}\n{csv_content.getvalue()}"
                else:
                    csv_with_personal_info = csv_content.getvalue()
                
                # Prepare export path for summary
                summary_export_path = None
                if Settings.EXPORT_RAW_GEMINI_RESPONSES and output_dir:
                    summary_export_path = os.path.join(output_dir, "raw_gemini_summary.txt")
                
                # Generate summary
                summary_response = self.generate_content(
                    GEMINI_TRANSACTION_SUMMARY, 
                    csv_with_personal_info,
                    export_path=summary_export_path
                )
                
                try:
                    # Try to parse as JSON
                    summary = json.loads(summary_response)
                except json.JSONDecodeError:
                    # If not valid JSON, use the raw text
                    summary = {"raw_summary": summary_response}
            
            return {
                "transactions": all_transactions,
                "personal_info": personal_info,
                "summary": summary
            }
        finally:
            # Restore original export setting
            Settings.EXPORT_RAW_GEMINI_RESPONSES = original_export_setting
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"Removed temporary directory: {temp_dir}") 