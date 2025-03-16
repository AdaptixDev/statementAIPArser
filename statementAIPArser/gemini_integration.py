#!/usr/bin/env python3
"""
Integration with Gemini 2.0 taking a PDF, splitting into smaller PDFs, 
and processing each sub-PDF sequentially using a reusable prompt from backend/src/core/prompts.py.
"""

import os
import time
import json
import csv
import io
import argparse
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PyPDF2 import PdfReader, PdfWriter  # pip install PyPDF2
import shutil
import tempfile

# Import your reusable prompt
from backend.src.core.prompts import GEMINI_STATEMENT_PARSE, GEMINI_PERSONAL_INFO_PARSE, GEMINI_TRANSACTION_SUMMARY, GEMINI_TRANSACTION_CATEGORISATION

# CSV Headers
CSV_HEADERS = ['Date', 'Description', 'Amount', 'Direction', 'Balance', 'Category']

# --- New: Custom in-memory PDF file with MIME type ---
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

def split_pdf_into_subpdfs(original_pdf_path: str, chunk_count: int, temp_dir: str) -> list:
    """
    Splits the PDF at `original_pdf_path` into `chunk_count` smaller PDFs,
    storing them in `temp_dir`. Returns a list of file paths for the sub-PDFs.
    """
    print(f"\nSplitting PDF \"{original_pdf_path}\" into {chunk_count} sub-PDFs...")
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
        print(f"  Creating sub-PDF #{chunk_idx}: pages {start_page + 1} to {end_page}...")
        
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

    print(f"Completed splitting PDF into {len(subpdf_paths)} sub-PDFs.\n")
    return subpdf_paths


def upload_to_gemini(client, pdf_tuple):
    """
    Uploads the given in-memory PDF tuple to Gemini with progress logging.
    Expects pdf_tuple to be (filename, file-like object).
    Returns the uploaded file object.
    """
    filename, memory_file = pdf_tuple
    # Ensure the in-memory file's name ends with .pdf for good measure
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    memory_file.name = filename  # e.g. "Statement_..._chunk_1.pdf"

    print(f"  Uploading sub-PDF \"{filename}\" to Gemini...")

    # Pass content_type="application/pdf" rather than mime_type=...
    file_obj = client.files.upload(
        file=memory_file,
        content_type="application/pdf",  # <--- The parameter name is content_type
        display_name=filename            # Optionally set a display name
    )

    print(f"  -> Uploaded file '{file_obj.display_name}' as: {file_obj.uri}")
    return file_obj


def wait_for_files_active(client, files):
    """
    Waits for the given files to be active (state=ACTIVE) with periodic logging.
    Raises an exception if any file fails to become ACTIVE.
    """
    print("  Waiting for sub-PDF file(s) to become ACTIVE in Gemini...")
    for file_obj in files:
        current_file = client.files.get(name=file_obj.name)
        while current_file.state.name == "PROCESSING":
            print("    ...still processing, waiting 10 seconds...")
            time.sleep(10)
            current_file = client.files.get(name=file_obj.name)
        if current_file.state.name != "ACTIVE":
            raise Exception(
                f"File {current_file.name} failed to process. "
                f"Current state: {current_file.state.name}"
            )
    print("  -> All file(s) ready.\n")


def extract_csv_from_response(text: str) -> str:
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


def parse_csv_to_transactions(csv_text: str) -> list:
    """
    Parses CSV text into a list of transaction dictionaries.
    Cleans and standardizes each field to match expected headers.
    Ensures that each transaction appears as a single line in the output CSV.
    """
    transactions = []
    try:
        # Use StringIO to treat the string as a file
        csv_file = io.StringIO(csv_text)
        reader = csv.reader(csv_file)
        
        # Process each row
        for row in reader:
            # Skip empty rows
            if not row or all(cell.strip() == '' for cell in row):
                continue

            def clean(cell):
                # Remove any embedded newlines and extra quotes; trim whitespace.
                return cell.replace("\n", " ").replace('"', '').strip()

            cleaned_row = {}
            cleaned_row['Date'] = clean(row[0].replace('Date:', '')) if len(row) > 0 else ''
            cleaned_row['Description'] = clean(row[1].replace('Description:', '')) if len(row) > 1 else ''
            if len(row) > 2:
                try:
                    cleaned_row['Amount'] = float(clean(row[2].replace('Amount:', '')).replace(',', ''))
                except ValueError:
                    cleaned_row['Amount'] = None
            else:
                cleaned_row['Amount'] = None
            cleaned_row['Direction'] = clean(row[3].replace('Direction:', '')) if len(row) > 3 else ''
            if len(row) > 4:
                try:
                    cleaned_row['Balance'] = float(clean(row[4].replace('Balance:', '')).replace(',', ''))
                except ValueError:
                    cleaned_row['Balance'] = None
            else:
                cleaned_row['Balance'] = None
            if len(row) > 5:
                cleaned_row['Category'] = clean(row[5].replace('Category:', ''))
            else:
                cleaned_row['Category'] = ''
            
            # Only add rows with at least a Date or Description
            if cleaned_row['Date'] or cleaned_row['Description']:
                transactions.append(cleaned_row)
            
    except Exception as e:
        print("Warning: Error parsing CSV:", e)
        print("Raw CSV content:")
        print(csv_text[:500])  # Print first 500 chars for debugging

    return transactions


def main():
    parser = argparse.ArgumentParser(
        description="Split a PDF into sub-PDFs and process each with Gemini 2.0 using a reusable prompt."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file to process.")
    parser.add_argument(
        "--chunk_count",
        type=int,
        default=3,
        help="How many smaller PDFs to produce (default=3)."
    )
    args = parser.parse_args()

    pdf_file = args.pdf_path

    print(f"\n[INFO] Checking input file \"{pdf_file}\"...")
    if not os.path.exists(pdf_file):
        print(f"[ERROR] File \"{pdf_file}\" does not exist.")
        return
    if not pdf_file.lower().endswith(".pdf"):
        print(f"[ERROR] File \"{pdf_file}\" is not a PDF.")
        return
    print("[INFO] Input PDF is valid.\n")

    # Load .env if present
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"[INFO] Loaded environment variables from \"{env_path}\".")
    else:
        print(f"[WARNING] .env file not found at \"{env_path}\". Continuing without loading environment.")

    # Check for the Gemini API key
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY is not set in the environment.")
        return

    print("[INFO] Initializing Gemini client...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("[INFO] Gemini client successfully initialized.\n")

    # Create a temporary directory for storing sub-PDFs
    temp_dir = tempfile.mkdtemp()
    print(f"[INFO] Created temporary directory: {temp_dir}")

    try:
        # 1. Split the PDF into sub-PDFs (using temp_dir)
        smaller_pdfs = split_pdf_into_subpdfs(pdf_file, args.chunk_count, temp_dir)

        # Now each chunk is just a file path on disk in temp_dir
        all_transactions = []
        
        # Store the first chunk path for additional processing later
        first_chunk_path = smaller_pdfs[0] if smaller_pdfs else None

        print("[INFO] Starting processing of sub-PDFs...\n")
        for i, subpdf_path in enumerate(smaller_pdfs, start=1):
            filename = os.path.basename(subpdf_path)
            print(f"  [CHUNK {i}] Uploading file \"{subpdf_path}\" to Gemini...")

            # 2. Upload chunk to Gemini from disk
            pdf_obj = client.files.upload(file=subpdf_path)
            print(f"  -> Uploaded file '{pdf_obj.display_name}' as: {pdf_obj.uri}")

            # 3. Wait for the file to be active, then process...
            wait_for_files_active(client, [pdf_obj])

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[GEMINI_STATEMENT_PARSE, pdf_obj],
                config=types.GenerateContentConfig(max_output_tokens=400000),
            )
            response_text = response.text
            # Extract CSV, parse, etc...
            csv_content = extract_csv_from_response(response_text)
            chunk_transactions = parse_csv_to_transactions(csv_content)
            
            # Categorize transactions for this chunk immediately
            if chunk_transactions:
                print(f"  [CHUNK {i}] Categorizing {len(chunk_transactions)} transactions...")
                
                # Create a CSV from chunk transactions without categories
                csv_without_categories = io.StringIO()
                writer = csv.DictWriter(csv_without_categories, fieldnames=['Date', 'Description', 'Amount', 'Direction', 'Balance'])
                writer.writeheader()
                for transaction in chunk_transactions:
                    # Create a copy without the Category field
                    transaction_without_category = {k: v for k, v in transaction.items() if k != 'Category'}
                    writer.writerow(transaction_without_category)
                
                # Send to Gemini with the categorization prompt
                categorization_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[GEMINI_TRANSACTION_CATEGORISATION, csv_without_categories.getvalue()],
                    config=types.GenerateContentConfig(max_output_tokens=400000),
                )
                
                # Extract CSV from response
                categorized_csv = categorization_response.text
                
                # Parse the categorized CSV
                categorized_chunk_transactions = parse_csv_to_transactions(categorized_csv)
                print(f"  [CHUNK {i}] Successfully categorized {len(categorized_chunk_transactions)} transactions")
                
                # Add categorized transactions to the main list
                all_transactions.extend(categorized_chunk_transactions)
            else:
                print(f"  [CHUNK {i}] No transactions found, skipping categorization")

        # After all chunks processed, write final CSV
        total_found = len(all_transactions)
        final_csv_filename = "final_transactions.csv"
        with open(final_csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(all_transactions)
        print(f"[INFO] Process complete. Aggregated {total_found} transactions. Final CSV written to {final_csv_filename}")

        # Additional processing for the first chunk with GEMINI_PERSONAL_INFO_PARSE
        if first_chunk_path:
            print("\n[INFO] Starting additional processing for the first chunk to extract personal information...")
            
            # Upload the first chunk again
            print(f"  Uploading first chunk \"{first_chunk_path}\" to Gemini for personal info extraction...")
            first_chunk_obj = client.files.upload(file=first_chunk_path)
            print(f"  -> Uploaded file '{first_chunk_obj.display_name}' as: {first_chunk_obj.uri}")
            
            # Wait for it to be active
            wait_for_files_active(client, [first_chunk_obj])
            
            # Process with GEMINI_PERSONAL_INFO_PARSE
            print("  Sending GEMINI_PERSONAL_INFO_PARSE prompt with first chunk to Gemini...")
            personal_info_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[GEMINI_PERSONAL_INFO_PARSE, first_chunk_obj],
                config=types.GenerateContentConfig(max_output_tokens=400000),
            )
            
            # Log the response to screen
            print("\n[PERSONAL INFO EXTRACTION RESULT]")
            print("=" * 80)
            personal_info_text = personal_info_response.text.strip()
            print(personal_info_text)
            print("=" * 80)
            print("[END OF PERSONAL INFO EXTRACTION]")
            
            # Add the personal info line to the top of the final_transactions.csv file
            print("\n[INFO] Adding personal information to the top of the final_transactions.csv file...")
            
            # Read the existing CSV file
            with open(final_csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
                existing_content = csvfile.read()
            
            # Write the personal info line followed by the existing content
            with open(final_csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                # Write the personal info line
                csvfile.write(f"# Personal Information: {personal_info_text}\n")
                # Write the existing content
                csvfile.write(existing_content)
            
            print(f"[INFO] Personal information added to {final_csv_filename}")
            
            # Final step: Send the completed CSV file to Gemini with GEMINI_TRANSACTION_SUMMARY prompt
            print("\n[INFO] Sending final transactions CSV to Gemini for transaction summary...")
            
            # Read the final CSV file
            with open(final_csv_filename, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            # Send to Gemini with the transaction summary prompt
            summary_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[GEMINI_TRANSACTION_SUMMARY, csv_content],
                config=types.GenerateContentConfig(max_output_tokens=400000),
            )
            
            # Output the response to console
            print("\n[TRANSACTION SUMMARY RESULT]")
            print("=" * 80)
            print(summary_response.text)
            print("=" * 80)
            print("[END OF TRANSACTION SUMMARY]")

    finally:
        # Clean up: remove all sub-PDFs in the temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"[INFO] Removed temporary directory: {temp_dir}")


if __name__ == "__main__":
    main() 