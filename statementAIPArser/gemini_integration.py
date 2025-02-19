#!/usr/bin/env python3
"""
Revised integration with Gemini 2.0 using a reusable prompt from ai_prompts.py.

This script:
1. Loads the GEMINI_API_KEY from .env.
2. Takes a PDF file (validated by extension and existence) and an accompanying prompt.
3. Uploads the PDF file to Gemini.
4. Waits for the file to become active.
5. Sends the prompt and the file reference to Gemini via generate_content.
6. Logs the output response to the console.
Counts the number of transactions (if present) in the JSON response
by parsing the text as JSON.
"""

import os
import time
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import your reusable prompt
from prompts.ai_prompts import GEMINI_STATEMENT_PARSE

# Explicitly load the .env file from the same directory as this script
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    print("Warning: .env file not found at", env_path)
load_dotenv(dotenv_path=env_path)
print("Loaded GEMINI_API_KEY:", os.environ.get("GEMINI_API_KEY"))

# Create a client instance using the new SDK
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def upload_to_gemini(path):
    """Uploads the given file to Gemini."""
    file_obj = client.files.upload(file=path)
    print(f"Uploaded file '{file_obj.display_name}' as: {file_obj.uri}")
    return file_obj

def wait_for_files_active(files):
    """Waits for the given files to be active."""
    print("Waiting for file processing...")
    for file_obj in files:
        current_file = client.files.get(name=file_obj.name)
        while current_file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(10)
            current_file = client.files.get(name=file_obj.name)
        if current_file.state.name != "ACTIVE":
            raise Exception(
                f"File {current_file.name} failed to process. Current state: {current_file.state.name}"
            )
    print("...all files ready\n", flush=True)

def extract_json_from_code_fence(text: str) -> str:
    """
    Returns only the JSON found between ```json ... ``` fences (line-based),
    or an empty string if none is found. Does NOT alter backslashes, does NOT do replacements.
    """
    lines = text.split('\n')
    in_json_block = False
    json_lines = []

    for line in lines:
        # If we see the start fence
        if line.strip().startswith('```json'):
            in_json_block = True
            continue
        # If we are in the block and we see the closing fence
        if in_json_block and line.strip().startswith('```'):
            break  # stop collecting lines
        # If we are in the block, collect the line
        if in_json_block:
            json_lines.append(line)

    joined = '\n'.join(json_lines).strip()
    return joined

def main():
    parser = argparse.ArgumentParser(
        description="Process a PDF with Gemini 2.0 using a reusable prompt."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file to process.")
    args = parser.parse_args()

    pdf_file = args.pdf_path
    if not os.path.exists(pdf_file):
        print(f"Error: File {pdf_file} does not exist.")
        return
    if not pdf_file.lower().endswith(".pdf"):
        print(f"Error: File {pdf_file} is not a PDF.")
        return

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not set in the environment.")
        return

    # 1. Upload the PDF file
    pdf_obj = upload_to_gemini(pdf_file)

    # 2. Wait for the file to be active
    wait_for_files_active([pdf_obj])

    # 3. Use the prompt from ai_prompts.py (along with the PDF)
    print("Sending prompt + PDF file to Gemini...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[GEMINI_STATEMENT_PARSE, pdf_obj]
    )

    print("\nGemini response (text):")
    print(response.text)

    # Optionally print detailed JSON from the model object
    print("\nDetailed Model Dump JSON (SDK metadata, not your statement JSON):")
    print(response.model_dump_json(exclude_none=True, indent=4))

    # 4. Extract JSON from the code fence
    json_string = extract_json_from_code_fence(response.text)

    # If extraction fails to find the code-fence block, fallback:
    if not json_string:
        # try to find the first '{' and last '}' in the entire response
        start = response.text.find('{')
        end = response.text.rfind('}')
        if start != -1 and end != -1 and start < end:
            json_string = response.text[start:end + 1]

    # 5. Parse the JSON & count transactions
    try:
        parsed_data = json.loads(json_string)
        transactions = parsed_data.get("Transactions", [])
        num_transactions = len(transactions)
        print(f"\nNumber of transactions found: {num_transactions}")
    except json.JSONDecodeError as e:
        print(f"\nCould not parse JSON from model response: {e}")
        print("Number of transactions found: 0")

if __name__ == "__main__":
    main() 