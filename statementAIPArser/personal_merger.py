import json
import glob
import os
from dateutil.parser import parse  # Requires python-dateutil package.
from datetime import datetime
import re

def merge_personal_and_transactions(
    in_memory_transactions: list = None,
    in_memory_personal_info: dict = None,
    personal_info_glob="*_personal_info.json",
    transactions_file="merged_statement_analysis.json",
    output_file="final_statement_data.json",
    directory="."
):
    """
    Merges the personal JSON data with the transactions JSON data
    into one final JSON file.

    If in-memory values are provided, they are used instead of reading from disk.
    The final merged JSON file is written to disk.
    """
    # Get personal info data.
    if in_memory_personal_info is not None:
        personal_data = in_memory_personal_info
    else:
        personal_files = glob.glob(os.path.join(directory, personal_info_glob))
        if not personal_files:
            print(f"[ERROR] No personal info files found with pattern {personal_info_glob}")
            return
        with open(personal_files[0], "r", encoding="utf-8") as pf:
            personal_data = json.load(pf)

    # Get transactions data.
    if in_memory_transactions is not None:
        transactions_data = {"Transactions": in_memory_transactions}
    else:
        transactions_path = os.path.join(directory, transactions_file)
        if not os.path.exists(transactions_path):
            print(f"[ERROR] Transactions file not found: {transactions_file}")
            return
        with open(transactions_path, "r", encoding="utf-8") as tf:
            transactions_data = json.load(tf)

    # Combine the data into a single structure.
    final_data = {
        "Personal Information": personal_data,
        "Transactions": transactions_data.get("Transactions", [])
    }

    # --- Flatten the transactions if they are nested ---
    flat_transactions = []
    for item in final_data["Transactions"]:
        if isinstance(item, dict) and "Transactions" in item:
            flat_transactions.extend(item["Transactions"])
        else:
            flat_transactions.append(item)
    final_data["Transactions"] = flat_transactions

    # --- Remove any transactions with description variations of 'Brought Forward' (case-insensitive) ---
    # The regular expression below matches "brought" followed by one or more whitespace or hyphen characters and then "forward"
    btf_pattern = re.compile(r"\bbrought[\s\-]+forward\b", re.IGNORECASE)
    filtered_transactions = []
    for tx in final_data["Transactions"]:
        desc = tx.get("Description", "")
        if btf_pattern.search(desc):
            print(f"[DEBUG] Removing 'Brought Forward' transaction: {tx}")
        else:
            filtered_transactions.append(tx)
    final_data["Transactions"] = filtered_transactions

    # --- Adjust anomalous transaction dates using the statement period ---
    # Extract the start of the statement period from Personal Information.
    statement_period = personal_data.get("Statement Period Date", "")
    sp_start_date = None
    if statement_period:
        try:
            # Assuming the format is "25 MAY 2024 to 27 JUN 2024"
            sp_start_str, _ = statement_period.split("to")
            sp_start_str = sp_start_str.strip()
            sp_start_date = parse(sp_start_str, fuzzy=True, dayfirst=True)
            print(f"[DEBUG] Statement start date parsed as: {sp_start_date}")
        except Exception as e:
            print(f"[WARNING] Could not parse statement period start date: {e}")

    # Define helper function to parse a date.
    def parse_date(date_str):
        try:
            return parse(date_str, fuzzy=True, dayfirst=True)
        except Exception:
            return None

    if sp_start_date:
        for tx in final_data["Transactions"]:
            tx_date_str = tx.get("Date", "")
            dt = parse_date(tx_date_str) if tx_date_str else None
            # If the parsed date is significantly earlier than the statement period,
            # override it (this heuristic assumes the statement year should match).
            if dt and dt.year < sp_start_date.year:
                print(f"[DEBUG] Correcting anomalous transaction date for transaction: {tx}")
                tx["Date"] = sp_start_date.strftime("%d %b %Y")

    # --- Sorting logic ---
    def transaction_sort_key(tx):
        dt = parse_date(tx.get("Date", ""))
        return dt if dt is not None else datetime.max

    final_data["Transactions"].sort(key=transaction_sort_key)

    # Save the final merged JSON with literal non-ASCII characters.
    output_path = os.path.join(directory, output_file)
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(final_data, out, indent=4, ensure_ascii=False)

    print(f"[INFO] Final merged JSON written to {output_path}")

if __name__ == "__main__":
    merge_personal_and_transactions() 