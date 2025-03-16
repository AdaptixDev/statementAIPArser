#!/usr/bin/env python3
"""
Standalone script to process a financial statement using Gemini.
This script follows the exact requirements:
1. Uses a test PDF
2. Chunks the PDF into smaller PDFs (configurable)
3. Sends chunks to Gemini with GEMINI_STATEMENT_PARSE prompt
4. Concatenates responses into a single CSV
5. Sends first chunk with GEMINI_PERSONAL_INFO_PARSE prompt
6. Sends final CSV to Gemini with GEMINI_TRANSACTION_SUMMARY prompt
7. Logs the response to console
"""

import os
import sys
import argparse
import logging
import tempfile
import shutil
import csv
import io
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PyPDF2 import PdfReader, PdfWriter

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# CSV Headers for statement processing
CSV_HEADERS = ['Date', 'Description', 'Amount', 'Direction', 'Balance', 'Category']
CSV_HEADERS_WITHOUT_CATEGORY = ['Date', 'Description', 'Amount', 'Direction', 'Balance']

# Import prompts directly from the core/prompts.py file
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
try:
    from src.core.prompts import (
        GEMINI_STATEMENT_PARSE,
        GEMINI_PERSONAL_INFO_PARSE,
        GEMINI_TRANSACTION_SUMMARY,
        GEMINI_TRANSACTION_CATEGORISATION
    )
    logger.info("Successfully imported prompts from src.core.prompts")
except ImportError:
    logger.error("Failed to import prompts from src.core.prompts")
    # Define fallback prompts if import fails
    GEMINI_STATEMENT_PARSE = """\
Please parse the attached financial statement PDF and a provide a csv response. Only return a valid .csv, no other text or comments, CSV output should have the following structure

For every single transaction identified, output the following data by parsing each line in the statement
Date of transaction,Description of transaction,Amount of transaction,Direction, either paid in  or withdrawn,Balance remaining, Category 

The category field must be present on every output line and must be assigned to one of the following categories by parsing the description data and inferring category

Category fields has to be one of the following an should be inferred from the transaction description:

1. Essential Home - Rent/Mortgage, monthly or weekly consistent payment - must be outgoing
2. Essential Household - Council Tax, Water, Electricity, Gas, Internet, TV Licence, Phone, Mobile, etc. - must be outgoing
3. Non-Essential Household - Sky TV, Netflix, Spotify, Disney+, Apple Music, cleaners, gardeners, etc. - must be outgoing
4. Salary - Money received from a salary or other regular payment - must be incoming
5. Non -Essential Entertainment - Going out, dining out, cinema, theatre, Uber, takeaways - must be outgoing
6. Gambling - Betting, Casino, Lotteries, etc. - Can be incoming or outgoing
7. Cash Withdrawal - Cash withdrawals from ATMs, banks, etc. - must be outgoing
8. Bank Transfer - Money transferred from one account to another - Can be outgoing or incoming
9. Unknown - Any other category that does not fit into the above


If the date is not clear parse the description data to infer.
Any dates must be output in the format dd-mm-yyyy 
There structure should be one transaction per row of CSV
Note that balance remaining may we be negative or overdrawn, possibly denoted with a minus sign or in brackets, or with an OD, or overdrawn. This must be represented in the banace reamining as a negative number


Note that no headers should be returned, just transaction data.
Provide exactly one row per transaction identified, do not skip any transactions for any reason, even missing or incomplete data

If the file does not seem to contain any transactions the just return an empty CSV
"""

    GEMINI_PERSONAL_INFO_PARSE = """\
Please parse the attached financial statement PDF and a provide a csv response consisting of personal data only, 
ignore any transaction data. The data required is as follows 

full name, address, account number, sort code, statement starting balance, statement finishing balance, 
statement period date, bank provider, total paid in, total withdrawn.

Do not provide any other response, commentary or data, just the comma delimited fields highlighted above
"""

    GEMINI_TRANSACTION_SUMMARY = """\
You are an expert at summarising financial transactions.
YOu are given a some personal information and a list of financial transactions and must provide a summary in a valid JSON format.
The incoming data follows the following format:

Date of transaction,Description of transaction,Amount of transaction,Direction, either paid in  or withdrawn,Balance remaining, Category 
 I would like you to summarise transaction, in and out, on a catergory by catergory basis and then give a general summary of the list of transactions from a financial health point of view. Are there any red flags in the list, anything to be concerns about?

You must parse the personal information from the data provided, provide a summary of total incoming and outgoing trasnactions at category level 
and then provide a general commentary on the transactions advising on general finanacial health, possible red flags or concerns, and any general reccomendations

The JSON needs to follow the following structure

{
  "personalInformation": {
    "name": "John Smith",
    "address": "123 Example Street, Example Town, EX1 1EX",
    "accountNumber": "12345678",
    "sortCode": "12-34-56",
    "statementStartingBalance": 8233.65,
    "statementFinishingBalance": 6174.17
  },
  "summaryOfIncomeAndOutgoings": {
    "income": {
      "Essential Home - Rent/Mortgage": 1250.00,
      "Essential Household": 145.99,
      "Unknown": 5275.00
    },
    "outgoings": {
      "Essential Household": 760.64,
      "Non-Essential Household": 33.00,
      "Essential Home - Rent/Mortgage": 0.00,
      "Unknown": 2898.84
    }
  },
  "generalSummaryAndFinancialHealthCommentary": {
    "overallBalance": "The account balance has decreased by £2059.48 during the statement period (from £8233.65 to £6174.17).",
    "inconsistentCategorization": "There are a lot of transactions labelled as 'Unknown.' More specific categorization is needed for proper budgeting and analysis.",
    "essentialHouseholdSpending": "A significant amount is spent on essential household bills.",
    "transfers": "Frequent transfers to and from 'BYRON C' and 'BYRON CJ' suggest money moving between accounts without clear purposes.",
    "standingOrdersAndDirectDebits": "Several standing orders and direct debits are active.",
    "paymentsToIndividuals": "Numerous small payments to individuals could indicate informal lending or reimbursements.",
    "rentMortgagePayments": "Rent/Mortgage payments are made regularly.",
    "councilTaxPayments": "Council tax is being paid on a regular basis.",
    "incomeNote": "It's unclear what the main source of income is; some rent payments may not be 'income' in the strict sense."
  },
  "potentialRedFlagsAndConcerns": [
    "High 'Unknown' Category Spending: Indicates lack of tracking and control over finances.",
    "Frequent Small Transfers: Could be a sign of poor budgeting or overspending without clarity.",
    "Decreasing Balance: Balance declined over the period, unclear if temporary or long-term.",
    "Dependence on Transfers: A large portion of income comes from transfers, suggesting reliance on them."
  ],
  "recommendations": [
    "Categorize Transactions: Categorize all 'Unknown' items to see where money is truly going.",
    "Budgeting: Create a detailed budget to manage income and expenses.",
    "Investigate Transfers: Understand the purpose of frequent transfers to 'BYRON C' and 'BYRON CJ'.",
    "Review Direct Debits and Standing Orders: Ensure they are necessary and amounts are correct.",
    "Seek Financial Advice: If the balance keeps declining or financial management is challenging, consult a professional."
  ]
}
"""
    logger.info("Using fallback prompts")

# Check for the Gemini API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY is not set in the environment.")
    sys.exit(1)

def split_pdf_into_subpdfs(original_pdf_path, chunk_count, temp_dir):
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
        logger.info(f"  Creating sub-PDF #{chunk_idx}: pages {start_page + 1} to {end_page}...")
        
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

    logger.info(f"Completed splitting PDF into {len(subpdf_paths)} sub-PDFs.")
    return subpdf_paths

def wait_for_files_active(client, files):
    """
    Waits for the given files to be active (state=ACTIVE) with periodic logging.
    Raises an exception if any file fails to become ACTIVE.
    """
    logger.info("Waiting for sub-PDF file(s) to become ACTIVE in Gemini...")
    for file_obj in files:
        current_file = client.files.get(name=file_obj.name)
        while current_file.state.name == "PROCESSING":
            logger.info("...still processing, waiting 10 seconds...")
            time.sleep(10)
            current_file = client.files.get(name=file_obj.name)
        if current_file.state.name != "ACTIVE":
            raise Exception(
                f"File {current_file.name} failed to process. "
                f"Current state: {current_file.state.name}"
            )
    logger.info("All file(s) ready.")

def extract_csv_from_response(text):
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

def parse_csv_to_transactions(csv_text):
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
        logger.error(f"Warning: Error parsing CSV: {e}")
        logger.error(f"Raw CSV content: {csv_text[:500]}")  # Print first 500 chars for debugging

    return transactions

def main():
    parser = argparse.ArgumentParser(
        description="Split a PDF into sub-PDFs and process each with Gemini 2.0 using a reusable prompt."
    )
    parser.add_argument("--pdf", required=True, help="Path to the PDF file to process.")
    parser.add_argument("--output", default="./output", help="Directory to save output files")
    parser.add_argument(
        "--chunk-count",
        type=int,
        default=3,
        help="How many smaller PDFs to produce (default=3)."
    )
    parser.add_argument(
        "--export-raw-responses",
        action="store_true",
        help="Export raw Gemini API responses for debugging (overrides Settings.EXPORT_RAW_GEMINI_RESPONSES)"
    )
    args = parser.parse_args()

    pdf_file = args.pdf

    logger.info(f"Checking input file \"{pdf_file}\"...")
    if not os.path.exists(pdf_file):
        logger.error(f"File \"{pdf_file}\" does not exist.")
        return
    if not pdf_file.lower().endswith(".pdf"):
        logger.error(f"File \"{pdf_file}\" is not a PDF.")
        return
    logger.info("Input PDF is valid.")

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        logger.info(f"Created output directory: {args.output}")

    # Initialize Gemini client
    logger.info("Initializing Gemini client...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    logger.info("Gemini client successfully initialized.")

    # Create a temporary directory for storing sub-PDFs
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Created temporary directory: {temp_dir}")

    try:
        # 1. Split the PDF into sub-PDFs (using temp_dir)
        smaller_pdfs = split_pdf_into_subpdfs(pdf_file, args.chunk_count, temp_dir)

        # Now each chunk is just a file path on disk in temp_dir
        all_transactions = []
        
        # Store the first chunk path for additional processing later
        first_chunk_path = smaller_pdfs[0] if smaller_pdfs else None

        logger.info("Starting processing of sub-PDFs...")
        for i, subpdf_path in enumerate(smaller_pdfs, start=1):
            filename = os.path.basename(subpdf_path)
            logger.info(f"[CHUNK {i}] Uploading file \"{subpdf_path}\" to Gemini...")

            # 2. Upload chunk to Gemini from disk - using the simple approach that works
            pdf_obj = client.files.upload(file=subpdf_path)
            logger.info(f"Uploaded file '{pdf_obj.uri}'")

            # 3. Wait for the file to be active, then process...
            wait_for_files_active(client, [pdf_obj])

            # Prepare export path for this chunk if exporting raw responses
            export_path = None
            if args.export_raw_responses:
                export_path = os.path.join(args.output, f"raw_gemini_statement_parse_chunk_{i}.txt")
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(export_path), exist_ok=True)

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[GEMINI_STATEMENT_PARSE, pdf_obj],
                config=types.GenerateContentConfig(max_output_tokens=400000),
            )
            response_text = response.text
            
            # Export raw response if enabled
            if args.export_raw_responses and export_path:
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(response_text)
                logger.info(f"Raw Gemini response for chunk {i} exported to: {export_path}")
            
            # Extract CSV, parse, etc...
            csv_content = extract_csv_from_response(response_text)
            chunk_transactions = parse_csv_to_transactions(csv_content)
            
            # Add new code for immediate categorization
            if chunk_transactions:
                logger.info(f"Categorizing {len(chunk_transactions)} transactions from chunk {i}...")
                
                # Create a CSV without categories for this chunk
                csv_without_categories = io.StringIO()
                writer = csv.DictWriter(csv_without_categories, fieldnames=CSV_HEADERS_WITHOUT_CATEGORY)
                writer.writeheader()
                for transaction in chunk_transactions:
                    # Create a copy without the Category field
                    transaction_without_category = {k: v for k, v in transaction.items() if k != 'Category'}
                    writer.writerow(transaction_without_category)
                
                # Prepare export path for categorization of this chunk
                chunk_categorization_export_path = None
                if args.export_raw_responses:
                    chunk_categorization_export_path = os.path.join(args.output, f"raw_gemini_categorization_chunk_{i}.txt")
                    os.makedirs(os.path.dirname(chunk_categorization_export_path), exist_ok=True)
                
                # Send to Gemini with the categorization prompt
                categorization_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[GEMINI_TRANSACTION_CATEGORISATION, csv_without_categories.getvalue()],
                    config=types.GenerateContentConfig(max_output_tokens=400000),
                )
                
                # Extract CSV from response
                categorized_csv = categorization_response.text
                
                # Export raw response if enabled
                if args.export_raw_responses and chunk_categorization_export_path:
                    with open(chunk_categorization_export_path, 'w', encoding='utf-8') as f:
                        f.write(categorized_csv)
                    logger.info(f"Raw categorization response for chunk {i} exported to: {chunk_categorization_export_path}")
                
                # Parse categorized CSV back to transactions
                categorized_chunk_transactions = parse_csv_to_transactions(categorized_csv)
                logger.info(f"Successfully categorized {len(categorized_chunk_transactions)} transactions for chunk {i}")
                
                # Add categorized transactions to the main list
                all_transactions.extend(categorized_chunk_transactions)
            else:
                logger.info(f"No transactions found in chunk {i}, skipping categorization")
                all_transactions.extend(chunk_transactions)  # Still add empty transactions if any

        # After all chunks processed, write final CSV with already categorized transactions
        total_found = len(all_transactions)
        final_csv_filename = os.path.join(args.output, "final_transactions.csv")
        with open(final_csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(all_transactions)
        logger.info(f"Process complete. Wrote {total_found} categorized transactions to {final_csv_filename}")

        # Additional processing for the first chunk with GEMINI_PERSONAL_INFO_PARSE
        if first_chunk_path:
            logger.info("Starting additional processing for the first chunk to extract personal information...")
            
            # Upload the first chunk again - using the simple approach that works
            logger.info(f"Uploading first chunk \"{first_chunk_path}\" to Gemini for personal info extraction...")
            first_chunk_obj = client.files.upload(file=first_chunk_path)
            logger.info(f"Uploaded file '{first_chunk_obj.uri}'")
            
            # Wait for it to be active
            wait_for_files_active(client, [first_chunk_obj])
            
            # Prepare export path for personal info if exporting raw responses
            personal_info_export_path = None
            if args.export_raw_responses:
                personal_info_export_path = os.path.join(args.output, "raw_gemini_personal_info.txt")
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(personal_info_export_path), exist_ok=True)
            
            # Process with GEMINI_PERSONAL_INFO_PARSE
            logger.info("Sending GEMINI_PERSONAL_INFO_PARSE prompt with first chunk to Gemini...")
            personal_info_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[GEMINI_PERSONAL_INFO_PARSE, first_chunk_obj],
                config=types.GenerateContentConfig(max_output_tokens=400000),
            )
            
            # Log the response to screen
            logger.info("PERSONAL INFO EXTRACTION RESULT")
            logger.info("=" * 80)
            personal_info_text = personal_info_response.text.strip()
            logger.info(personal_info_text)
            logger.info("=" * 80)
            logger.info("END OF PERSONAL INFO EXTRACTION")
            
            # Export raw response if enabled
            if args.export_raw_responses and personal_info_export_path:
                with open(personal_info_export_path, 'w', encoding='utf-8') as f:
                    f.write(personal_info_text)
                logger.info(f"Raw personal info response exported to: {personal_info_export_path}")
            
            # Add the personal info line to the top of the final_transactions.csv file
            logger.info("Adding personal information to the top of the final_transactions.csv file...")
            
            # Read the existing CSV file
            with open(final_csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
                existing_content = csvfile.read()
            
            # Write the personal info line followed by the existing content
            with open(final_csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                # Write the personal info line
                csvfile.write(f"# Personal Information: {personal_info_text}\n")
                # Write the existing content
                csvfile.write(existing_content)
            
            logger.info(f"Personal information added to {final_csv_filename}")
            
            # Final step: Send the completed CSV file to Gemini with GEMINI_TRANSACTION_SUMMARY prompt
            logger.info("Sending final transactions CSV to Gemini for transaction summary...")
            
            # Read the final CSV file
            with open(final_csv_filename, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            # Prepare export path for summary if exporting raw responses
            summary_export_path = None
            if args.export_raw_responses:
                summary_export_path = os.path.join(args.output, "raw_gemini_summary.txt")
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(summary_export_path), exist_ok=True)
            
            # Send to Gemini with the transaction summary prompt
            summary_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[GEMINI_TRANSACTION_SUMMARY, csv_content],
                config=types.GenerateContentConfig(max_output_tokens=400000),
            )
            
            # Output the response to console
            logger.info("TRANSACTION SUMMARY RESULT")
            logger.info("=" * 80)
            logger.info(summary_response.text)
            logger.info("=" * 80)
            logger.info("END OF TRANSACTION SUMMARY")
            
            # Export raw response if enabled
            if args.export_raw_responses and summary_export_path:
                with open(summary_export_path, 'w', encoding='utf-8') as f:
                    f.write(summary_response.text)
                logger.info(f"Raw summary response exported to: {summary_export_path}")
            
            # Save summary to file
            summary_file = os.path.join(args.output, "summary.txt")
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(summary_response.text)
            logger.info(f"Summary saved to {summary_file}")

    finally:
        # Clean up: remove all sub-PDFs in the temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Removed temporary directory: {temp_dir}")


if __name__ == "__main__":
    main() 