"""Google Gemini service for interacting with Google's Gemini API."""

import os
import time
import json
import csv
import io
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from google import genai
from google.genai import types
from PyPDF2 import PdfReader, PdfWriter

from backend.src.config.settings import Settings
from backend.src.utils.exceptions import APIError
from backend.src.core.prompts import (
    GEMINI_STATEMENT_PARSE,
    GEMINI_PERSONAL_INFO_PARSE,
    GEMINI_TRANSACTION_SUMMARY
)

logger = logging.getLogger(__name__)

# CSV Headers
CSV_HEADERS = ['Date', 'Description', 'Amount', 'Direction', 'Balance', 'Category']

# Custom in-memory PDF file with MIME type
class MemoryPDF(io.BytesIO):
    def __init__(self, name: str, *args, **kwargs):
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
    """Service for interacting with Google's Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini service."""
        logger.info("Initializing GeminiService...")
        # Fetch the API key from environment variables or settings
        api_key = os.environ.get("GEMINI_API_KEY") or getattr(Settings, "GEMINI_API_KEY", None)
        if not api_key:
            logger.error("GEMINI_API_KEY is not set in environment variables or Settings.")
            raise ValueError("GEMINI_API_KEY is not set in environment variables or Settings.")
        logger.debug(f"Using GEMINI_API_KEY: {api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}")
        
        try:
            self.client = genai.Client(api_key=api_key)
            logger.info("Gemini client initialized successfully.")
        except Exception as e:
            logger.exception(f"Failed to initialize Gemini client: {str(e)}")
            raise APIError(f"Failed to initialize Gemini client: {str(e)}")
    
    def split_pdf_into_chunks(self, pdf_path: str, chunk_count: int) -> List[Tuple[str, bytes]]:
        """
        Split a PDF into chunks for processing.
        
        Args:
            pdf_path: Path to the PDF file
            chunk_count: Number of chunks to split the PDF into
            
        Returns:
            List of tuples containing (filename, file_bytes) for each chunk
        """
        logger.info(f"Splitting PDF {pdf_path} into {chunk_count} chunks")
        
        # Create a temporary directory for storing chunks
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {temp_dir}")
        
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            logger.debug(f"Total pages in PDF: {total_pages}")
            
            pages_per_chunk = max(1, total_pages // chunk_count)
            logger.debug(f"Pages per chunk: {pages_per_chunk}")
            
            chunks = []
            for i in range(chunk_count):
                start_page = i * pages_per_chunk
                # Ensure the last chunk includes any remaining pages
                end_page = (i + 1) * pages_per_chunk if i < chunk_count - 1 else total_pages
                writer = PdfWriter()
                for page_num in range(start_page, end_page):
                    writer.add_page(reader.pages[page_num])
                chunk_filename = f"chunk_{i+1}.pdf"
                chunk_path = os.path.join(temp_dir, chunk_filename)
                with open(chunk_path, 'wb') as f:
                    writer.write(f)
                with open(chunk_path, 'rb') as f:
                    file_bytes = f.read()
                chunks.append((chunk_filename, file_bytes))
                logger.debug(f"Created chunk {chunk_filename} with {end_page - start_page} pages")
            
            logger.info(f"Successfully split PDF into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.exception(f"Error splitting PDF into chunks: {str(e)}")
            raise APIError(f"Error splitting PDF into chunks: {str(e)}")
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug(f"Removed temporary directory: {temp_dir}")
    
    def upload_file_to_gemini(self, file_name: str, file_bytes: bytes) -> Any:
        """
        Upload a file to Gemini.
        
        Args:
            file_name: Name of the file (e.g., "statement_chunk_1.pdf")
            file_bytes: File content as bytes
            
        Returns:
            Gemini file object
        """
        logger.info(f"Uploading file to Gemini: {file_name}")
        try:
            # Create a MemoryPDF object with the correct file name
            memory_pdf = MemoryPDF(file_name)
            memory_pdf.write(file_bytes)
            memory_pdf.seek(0)
            logger.debug(f"MemoryPDF created for file: {file_name}")
            
            # Upload the file without 'display_name'
            logger.debug("Attempting to upload file to Gemini...")
            file_obj = self.client.files.upload(
                file=memory_pdf,
                content_type="application/pdf"  # Ensure correct MIME type
                # 'display_name' removed as it's unsupported
            )
            logger.info(f"Uploaded file to Gemini: {file_obj.uri}")
            return file_obj
        except TypeError as te:
            logger.exception(f"TypeError during file upload: {str(te)}")
            raise APIError(f"TypeError during file upload: {str(te)}")
        except Exception as e:
            logger.exception(f"Failed to upload file to Gemini: {str(e)}")
            raise APIError(f"Failed to upload file to Gemini: {str(e)}")
    
    def wait_for_file_active(self, file_obj: Any) -> None:
        """
        Wait for a file to become active in Gemini.
        
        Args:
            file_obj: Gemini file object
        """
        logger.info(f"Waiting for file to become active: {file_obj.uri}")
        
        try:
            current_file = self.client.files.get(name=file_obj.name)
            logger.debug(f"Initial file state: {current_file.state.name}")
            while current_file.state.name == "PROCESSING":
                logger.info("File still processing, waiting 5 seconds...")
                time.sleep(5)
                current_file = self.client.files.get(name=file_obj.name)
                logger.debug(f"Updated file state: {current_file.state.name}")
            
            if current_file.state.name != "ACTIVE":
                logger.error(f"File {current_file.name} failed to process. Current state: {current_file.state.name}")
                raise APIError(f"File {current_file.name} failed to process. Current state: {current_file.state.name}")
            
            logger.info(f"File is now active: {file_obj.uri}")
        except Exception as e:
            logger.exception(f"Error while waiting for file to become active: {str(e)}")
            raise APIError(f"Error while waiting for file to become active: {str(e)}")
    
    def parse_csv_to_transactions(self, csv_text: str) -> List[Dict[str, Any]]:
        """
        Parse CSV text to a list of transaction dictionaries.
        
        Args:
            csv_text: CSV content as string
            
        Returns:
            List of transaction dictionaries
        """
        logger.info("Parsing CSV content to transactions")
        transactions = []
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_text))
            for row in csv_reader:
                transactions.append(row)
            logger.info(f"Parsed {len(transactions)} transactions from CSV")
        except Exception as e:
            logger.exception(f"Error parsing CSV: {str(e)}")
            logger.debug(f"CSV content preview: {csv_text[:500]}")
            raise APIError(f"Error parsing CSV: {str(e)}")
        return transactions
    
    def extract_csv_from_response(self, response_text: str) -> str:
        """
        Extract CSV content from a Gemini response.
        
        Args:
            response_text: Response text from Gemini
            
        Returns:
            CSV content
        """
        logger.info("Extracting CSV from Gemini response")
        
        # First try to find code-fenced CSV
        lines = response_text.split('\n')
        in_csv_block = False
        csv_lines = []
        
        for line in lines:
            if line.strip().startswith('```csv'):
                in_csv_block = True
                logger.debug("Found start of code-fenced CSV block")
                continue
            elif in_csv_block and line.strip().startswith('```'):
                logger.debug("Found end of code-fenced CSV block")
                break
            elif in_csv_block:
                csv_lines.append(line)
        
        if csv_lines:
            csv_content = '\n'.join(csv_lines).strip()
            logger.info(f"Extracted code-fenced CSV: {len(csv_content)} characters")
            return csv_content
        
        # If no code fence found, try to extract CSV directly
        for i, line in enumerate(lines):
            if any(header in line for header in ['Date', 'Description', 'Amount']):
                csv_content = '\n'.join(lines[i:]).strip()
                logger.info(f"Extracted CSV starting with headers: {len(csv_content)} characters")
                return csv_content
        
        logger.warning("No CSV content found in Gemini response")
        return response_text
    
    def extract_transactions(self, pdf_path: str, prompt_template: str = GEMINI_STATEMENT_PARSE, chunk_count: int = 3) -> List[Dict[str, Any]]:
        """
        Extract transactions from a PDF statement.
        
        Args:
            pdf_path: Path to the PDF file
            prompt_template: Prompt template for Gemini
            chunk_count: Number of chunks to split the PDF into
            
        Returns:
            List of transaction dictionaries
        """
        logger.info(f"Extracting transactions from PDF: {pdf_path}")
        transactions = []
        try:
            # Split PDF into chunks
            chunks = self.split_pdf_into_chunks(pdf_path, chunk_count)
            logger.debug(f"PDF split into {len(chunks)} chunks")
            
            for idx, (chunk_name, chunk_bytes) in enumerate(chunks, start=1):
                logger.info(f"Processing chunk {idx}: {chunk_name}")
                try:
                    # Upload chunk to Gemini
                    file_obj = self.upload_file_to_gemini(chunk_name, chunk_bytes)
                    
                    # Wait for file to become active
                    self.wait_for_file_active(file_obj)
                    
                    # Generate transactions using Gemini model
                    logger.info(f"Generating transactions for chunk {idx} with Gemini")
                    response = self.client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[prompt_template],
                        config=types.GenerateContentConfig(max_output_tokens=400000),
                    )
                    logger.debug(f"Received response from Gemini for chunk {idx}")
                    
                    # Extract CSV from response
                    csv_content = self.extract_csv_from_response(response.text)
                    
                    # Parse CSV to transactions
                    chunk_transactions = self.parse_csv_to_transactions(csv_content)
                    transactions.extend(chunk_transactions)
                    
                    logger.info(f"Extracted {len(chunk_transactions)} transactions from chunk {idx}")
                except APIError as api_err:
                    logger.error(f"APIError processing chunk {idx}: {str(api_err)}")
                except Exception as e:
                    logger.exception(f"Unexpected error processing chunk {idx}: {str(e)}")
            
            logger.info(f"Total transactions extracted: {len(transactions)}")
            return transactions
        except APIError as api_err:
            logger.error(f"APIError during transaction extraction: {str(api_err)}")
            raise
        except Exception as e:
            logger.exception(f"Error extracting transactions: {str(e)}")
            raise APIError(f"Error extracting transactions: {str(e)}")
    
    def extract_personal_info(self, pdf_path: str, prompt_template: str = GEMINI_PERSONAL_INFO_PARSE) -> Dict[str, Any]:
        """
        Extract personal information from a PDF statement.
        
        Args:
            pdf_path: Path to the PDF file
            prompt_template: Prompt template for Gemini
            
        Returns:
            Dictionary containing personal information
        """
        logger.info(f"Extracting personal information from PDF: {pdf_path}")
        personal_info = {}
        try:
            # Read PDF bytes
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            logger.debug(f"Read {len(pdf_bytes)} bytes from PDF")

            # Upload PDF to Gemini
            file_name = os.path.basename(pdf_path)
            file_obj = self.upload_file_to_gemini(file_name, pdf_bytes)
            
            # Wait for file to become active
            self.wait_for_file_active(file_obj)
            
            # Generate personal info using Gemini model
            logger.info("Generating personal information with Gemini")
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt_template],
                config=types.GenerateContentConfig(max_output_tokens=400000),
            )
            logger.debug("Received response from Gemini for personal info")
            
            # Extract CSV from response
            csv_content = self.extract_csv_from_response(response.text)
            
            # Parse CSV to personal info
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            for row in csv_reader:
                personal_info = row
                break  # Assuming only one row for personal info
            logger.info("Personal information extracted successfully")
            
            return personal_info
        except APIError as api_err:
            logger.error(f"APIError during personal info extraction: {str(api_err)}")
            raise
        except Exception as e:
            logger.exception(f"Error extracting personal information: {str(e)}")
            raise APIError(f"Error extracting personal information: {str(e)}")
    
    def generate_transaction_summary(self, transactions: List[Dict[str, Any]], prompt_template: str = GEMINI_TRANSACTION_SUMMARY) -> Dict[str, Any]:
        """
        Generate a summary of transactions.
        
        Args:
            transactions: List of transaction dictionaries
            prompt_template: Prompt template for Gemini
            
        Returns:
            Dictionary containing the summary
        """
        logger.info(f"Generating transaction summary for {len(transactions)} transactions")
        try:
            # Convert transactions to CSV
            csv_buffer = io.StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(transactions)
            csv_content = csv_buffer.getvalue()
            logger.debug(f"Generated CSV content for summary: {len(csv_content)} characters")
            logger.debug(f"CSV preview: {csv_content[:200]}...")
            
            # Send the prompt and CSV to Gemini
            logger.info("Sending prompt and CSV to Gemini for transaction summary")
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt_template, csv_content],
                config=types.GenerateContentConfig(max_output_tokens=400000),
            )
            logger.debug("Received response from Gemini for transaction summary")
            
            # Extract summary from the response
            response_text = response.text
            logger.debug(f"Response text length: {len(response_text)}")
            logger.debug(f"Response preview: {response_text[:200]}...")
            
            # Try to parse as JSON
            try:
                summary = json.loads(response_text)
                logger.info("Successfully parsed transaction summary as JSON")
                return summary
            except json.JSONDecodeError:
                logger.warning("Response is not valid JSON, returning as text")
                return {"text": response_text}
        except APIError as api_err:
            logger.error(f"APIError during transaction summary generation: {str(api_err)}")
            raise
        except Exception as e:
            logger.exception(f"Error generating transaction summary: {str(e)}")
            raise APIError(f"Error generating transaction summary: {str(e)}")
    
    def process_pdf_statement(self, pdf_path: str, prompt_template: str = GEMINI_STATEMENT_PARSE, output_csv_path: Optional[str] = None, pages_per_chunk: int = 3) -> List[Dict[str, Any]]:
        """
        Process a PDF statement and extract transactions.
        
        Args:
            pdf_path: Path to the PDF file
            prompt_template: Template for the prompt to send to Gemini
            output_csv_path: Path to save the CSV output (optional)
            pages_per_chunk: Number of pages per chunk when splitting the PDF
            
        Returns:
            List of transaction dictionaries
        """
        logger.info(f"Processing PDF statement: {pdf_path}")
        
        # Extract transactions from the PDF
        transactions = self.extract_transactions(pdf_path, prompt_template=prompt_template, chunk_count=pages_per_chunk)
        
        # Save to CSV if output path is provided
        if output_csv_path and transactions:
            logger.info(f"Saving transactions to CSV: {output_csv_path}")
            os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
            
            with open(output_csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                for transaction in transactions:
                    writer.writerow({
                        'Date': transaction.get('Date', ''),
                        'Description': transaction.get('Description', ''),
                        'Amount': transaction.get('Amount', ''),
                        'Direction': transaction.get('Direction', ''),
                        'Balance': transaction.get('Balance', ''),
                        'Category': transaction.get('Category', '')
                    })
            
            logger.info(f"Saved {len(transactions)} transactions to CSV")
        
        return transactions 