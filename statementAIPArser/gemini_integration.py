#!/usr/bin/env python3
"""
Integration with Gemini 2.0 taking a PDF, splitting into smaller PDFs, 
and processing each sub-PDF sequentially using a reusable prompt from ai_prompts.py.
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

# Import your reusable prompt
from prompts.ai_prompts import GEMINI_STATEMENT_PARSE

# CSV Headers
CSV_HEADERS = ['Date', 'Description', 'Amount', 'Direction', 'Balance']

def split_pdf_into_subpdfs(original_pdf_path: str, chunk_count: int) -> list:
    """
    Splits the PDF at `original_pdf_path` into `chunk_count` smaller PDFs.
    Returns a list of file paths to the sub-PDFs.
    Logs progress as it proceeds.
    """
    print(f"\nSplitting PDF \"{original_pdf_path}\" into {chunk_count} sub-PDFs...")
    reader = PdfReader(original_pdf_path)
    total_pages = len(reader.pages)
    base_name = Path(original_pdf_path).stem
    extension = Path(original_pdf_path).suffix

    # integer division rounding up
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

        subpdf_path = f"{base_name}_chunk_{chunk_idx}{extension}"
        with open(subpdf_path, 'wb') as f:
            writer.write(f)

        subpdf_paths.append(subpdf_path)
        start_page = end_page
        chunk_idx += 1

    print(f"Completed splitting PDF into {len(subpdf_paths)} sub-PDFs.\n")
    return subpdf_paths


def upload_to_gemini(client, path):
    """
    Uploads the given file to Gemini with progress logging.
    Returns the uploaded file object.
    """
    print(f"  Uploading sub-PDF \"{path}\" to Gemini...")
    file_obj = client.files.upload(file=path)
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

    # Initialize Gemini client
    print("[INFO] Initializing Gemini client...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("[INFO] Gemini client successfully initialized.\n")

    # 1. Split the PDF into sub-PDFs
    smaller_pdfs = split_pdf_into_subpdfs(pdf_file, args.chunk_count)

    # Lists to aggregate
    all_transactions = []
    all_responses = []

    # 2. Process each sub-PDF
    print("Starting processing of sub-PDFs...\n")

    # If you want to group the chunk outputs in a subfolder:
    # outputs_dir = "gemini_chunk_responses"
    # os.makedirs(outputs_dir, exist_ok=True)

    for i, subpdf_path in enumerate(smaller_pdfs, start=1):
        print(f"Processing chunk {i} of {len(smaller_pdfs)}...")

        # a) Upload
        pdf_obj = upload_to_gemini(client, subpdf_path)

        # b) Wait for it to be active
        wait_for_files_active(client, [pdf_obj])

        # Log the Gemini request prompt for transparency
        print("Sending request to Gemini with the following prompt:")
        print(GEMINI_STATEMENT_PARSE)

        # c) Generate content using prompt + PDF
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[GEMINI_STATEMENT_PARSE, pdf_obj],
            config=types.GenerateContentConfig(
                max_output_tokens=400000
            ),
        )
        response_text = response.text
        
        # Log the raw response to the console as well as save it
        print("Received raw response from Gemini:")
        print(response_text)
        raw_filename = f"gemini_response_chunk_{i}_raw.txt"
        # raw_filename = os.path.join(outputs_dir, raw_filename)
        with open(raw_filename, "w", encoding="utf-8") as raw_file:
            raw_file.write(response_text)
        print(f"Saved raw Gemini text for chunk {i} to {raw_filename}")

        # d) Extract and parse CSV
        csv_content = extract_csv_from_response(response_text)
        chunk_transactions = parse_csv_to_transactions(csv_content)
        
        # e) Save the chunk CSV to disk
        chunk_csv_filename = f"transactions_chunk_{i}.csv"
        # chunk_csv_filename = os.path.join(outputs_dir, chunk_csv_filename)
        with open(chunk_csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(chunk_transactions)
        print(f"Saved CSV chunk to {chunk_csv_filename}")

        # f) Store response and transactions in memory
        chunk_data = {
            "raw_response": response_text,
            "transactions": chunk_transactions
        }
        all_responses.append(chunk_data)
        all_transactions.extend(chunk_transactions)
        
        print(f"Chunk {i}: {len(chunk_transactions)} transactions found.")

    # 3. Final aggregated result
    total_found = len(all_transactions)
    print(f"\nCompleted processing. Aggregated {total_found} transactions in total.")

    # Write final concatenated CSV
    final_csv_filename = "final_transactions.csv"
    with open(final_csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(all_transactions)

    # Also save metadata about the processing
    metadata = {
        "TotalTransactions": total_found,
        "ProcessedChunks": len(smaller_pdfs),
        "TransactionsPerChunk": [len(resp["transactions"]) for resp in all_responses]
    }
    
    with open("processing_metadata.json", "w", encoding="utf-8") as metafile:
        json.dump(metadata, metafile, indent=2)

    print(f"Final CSV written to {final_csv_filename}")
    print(f"Processing metadata written to processing_metadata.json")
    print("[INFO] Process complete.\n")


if __name__ == "__main__":
    main() 