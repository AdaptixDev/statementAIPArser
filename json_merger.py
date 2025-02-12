import json
import glob
import os

def merge_transaction_files(
    json_pattern="statement_analysis_*.json",
    output_file="merged_statement_analysis.json",
    directory="."
):
    """
    Merges individual JSON files containing transaction lists into a single JSON file.

    Args:
        json_pattern (str): Glob pattern to match the JSON files.
        output_file (str): Output filename for the merged JSON file.
        directory (str): Directory to search for JSON files and output the merged file.
    """
    merged_transactions = []
    search_pattern = os.path.join(directory, json_pattern)
    print(f"[INFO] Searching for JSON files with pattern: {search_pattern}")
    
    json_files = glob.glob(search_pattern)
    print(f"[INFO] Found {len(json_files)} JSON file(s) to merge")
    
    for json_file in json_files:
        print(f"[INFO] Processing file: {json_file}")
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                print(f"[INFO] Loaded data from {json_file}")
                if isinstance(data, dict):
                    transactions = data.get("Transactions", [])
                    print(f"[INFO] Found {len(transactions)} transaction(s) in {json_file}")
                elif isinstance(data, list):
                    transactions = data
                    print(f"[INFO] Found {len(transactions)} transaction(s) in {json_file}")
                else:
                    transactions = []
                    print(f"[WARN] Unexpected data format in {json_file}; skipping transaction processing")
                merged_transactions.extend(transactions)
        except json.JSONDecodeError:
            print(f"[ERROR] Skipping invalid JSON file: {json_file}")
            continue

    merged_data = {"Transactions": merged_transactions}
    
    output_path = os.path.join(directory, output_file)
    with open(output_path, "w") as out:
        json.dump(merged_data, out, indent=4)
    
    print(f"[INFO] Merged transactions written to {output_path}")
    print(f"[INFO] Total merged transactions: {len(merged_transactions)}") 