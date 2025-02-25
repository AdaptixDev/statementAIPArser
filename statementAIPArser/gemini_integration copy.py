#!/usr/bin/env python3
"""
Integration with Gemini 2.0 taking a PDF, splitting into smaller PDFs, 
and processing each sub-PDF sequentially using a reusable prompt from ai_prompts.py.
"""

import os
import time
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PyPDF2 import PdfReader, PdfWriter  # pip install PyPDF2

# Import your reusable prompt
from prompts.ai_prompts import GEMINI_STATEMENT_PARSE

def split_pdf_into_subpdfs(original_pdf_path: str, chunk_count: int) -> list:
    """
    Splits the PDF at `original_pdf_path` into `chunk_count` smaller PDFs.
    Returns a list of file paths to the sub-PDFs.
    Logs progress as it proceeds.
    """
    print(f"\nStarting PDF splitting process for \"{original_pdf_path}\" into {chunk_count} sub-PDF(s)...")
    reader = PdfReader(original_pdf_path)
    total_pages = len(reader.pages)
    print(f"Original PDF has {total_pages} page(s).")

    base_name = Path(original_pdf_path).stem
    extension = Path(original_pdf_path).suffix

    # Calculate how many pages go into each chunk (attempt evenly distributed)
    pages_per_chunk = max(1, (total_pages + chunk_count - 1) // chunk_count)
    print(f"Each chunk will contain up to {pages_per_chunk} page(s) (final chunk may have fewer).")

    subpdf_paths = []
    start_page = 0
    chunk_idx = 1

    # Create smaller PDF files
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
        print(f"    -> Created sub-PDF: {subpdf_path} ({end_page - start_page} page(s) in this chunk).")

        start_page = end_page
        chunk_idx += 1

    print(f"Splitting complete. Generated {len(subpdf_paths)} sub-PDF(s).\n")
    return subpdf_paths


def upload_to_gemini(client, path):
    """Uploads the given file to Gemini with progress logging."""
    print(f"  Uploading sub-PDF \"{path}\" to Gemini...")
    file_obj = client.files.upload(file=path)
    memory_file = file_obj.file
    filename = file_obj.display_name
    memory_file.name = filename if filename.endswith(".pdf") else (filename + ".pdf")
    print(f"  -> Uploaded file '{file_obj.display_name}' as: {file_obj.uri}")
    return file_obj


def wait_for_files_active(client, files):
    """Waits for the given files to be active with periodic logging."""
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


def extract_json_from_code_fence(text: str) -> str:
    """
    Returns only the JSON found between ```json ... ``` fences (line-based),
    or an empty string if none is found. 
    Does NOT alter backslashes or do replacements.
    """
    lines = text.split('\n')
    in_json_block = False
    json_lines = []

    for line in lines:
        if line.strip().startswith('```json'):
            in_json_block = True
            continue
        if in_json_block and line.strip().startswith('```'):
            break  # stop collecting lines
        if in_json_block:
            json_lines.append(line)

    return '\n'.join(json_lines).strip()


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

    # Load .env
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"[INFO] Loaded environment variables from \"{env_path}\".")
    else:
        print(f"[WARNING] .env file not found at \"{env_path}\". Continuing without loading environment.")

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY is not set in the environment.")
        return

    # Create the client instance using the new SDK
    print("[INFO] Initializing Gemini client...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("[INFO] Gemini client successfully initialized.\n")

    # Split the main PDF into sub-PDFs
    smaller_pdfs = split_pdf_into_subpdfs(pdf_file, args.chunk_count)

    # We'll gather results across all PDF chunks
    all_transactions = []

    # Process each sub-PDF the same way you originally did with a single file
    print("Beginning sequential processing of sub-PDFs...\n")
    for i, subpdf_path in enumerate(smaller_pdfs, start=1):
        print(f"==== [CHUNK {i}/{len(smaller_pdfs)}] Processing sub-PDF: {subpdf_path} ====\n")

        # 1. Upload
        pdf_obj = upload_to_gemini(client, subpdf_path)

        # 2. Wait for it to be active
        wait_for_files_active(client, [pdf_obj])

        # 3. Use the prompt (from ai_prompts.py) + file
        print("  Sending prompt + this sub-PDF to Gemini:")
        print("  Prompt text:\n")
        print(GEMINI_STATEMENT_PARSE)
        print("\n  [END OF PROMPT]\n")

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[GEMINI_STATEMENT_PARSE, pdf_obj],
            config=types.GenerateContentConfig(
                max_output_tokens=400000  # Adjust if needed
            ),
        )

        response_text = response.text
        print("Gemini response (text):\n")
        print(response_text)
        print("\nDetailed Model Dump JSON (SDK metadata, not your statement JSON):")
        print(response.model_dump_json(exclude_none=True, indent=4))

        # 4. Extract JSON from the code fence
        json_string = extract_json_from_code_fence(response_text)
        # Fallback if no code fence found
        if not json_string:
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start != -1 and end != -1 and start < end:
                json_string = response_text[start:end + 1]

        # 5. Parse the JSON & collect transactions
        try:
            parsed_data = json.loads(json_string)
            sub_transactions = parsed_data.get("Transactions", [])
            print(f"  [RESULT] # of transactions found in sub-PDF {i}: {len(sub_transactions)}")
            all_transactions.extend(sub_transactions)
        except json.JSONDecodeError as e:
            print(f"[WARNING] Could not parse JSON from model response: {e}")
            print("[INFO] No transactions found in this chunk.")

        print(f"==== [END CHUNK {i}] ====\n")

    # Summarize across all chunks
    total_found = len(all_transactions)
    print(f"==== Completed. Aggregated a total of {total_found} transactions across all sub-PDFs. ====")
    final_result = {
        "Transactions": all_transactions,
        "TransactionCount": total_found,
    }
    # Here, you can do more logic if needed—like deduplicate transactions, etc.

    print("\nFinal JSON result (all chunks combined):")
    print(json.dumps(final_result, indent=2))
    print("[INFO] Process complete.\n")


if __name__ == "__main__":
    main() 