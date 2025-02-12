import json
import glob
import os

def merge_personal_and_transactions(
    personal_info_glob="*_personal_info.json",
    transactions_file="merged_statement_analysis.json",
    output_file="final_statement_data.json",
    directory="."
):
    """
    Merges the personal JSON data with the transactions JSON data
    into one final JSON file.

    The final JSON structure will be:
    {
        "Personal Information": { ... },
        "Transactions": [ ... ]
    }

    Args:
        personal_info_glob (str): Glob pattern to locate the personal info JSON file.
        transactions_file (str): Filename for the merged transactions JSON.
        output_file (str): Filename for the final merged JSON output.
        directory (str): Directory where the files are located.
    """
    # Locate the personal information JSON file.
    personal_files = glob.glob(os.path.join(directory, personal_info_glob))
    if not personal_files:
        print(f"[ERROR] No personal info files found with pattern {personal_info_glob}")
        return

    # Load the first matching personal info JSON file.
    with open(personal_files[0], "r", encoding="utf-8") as pf:
        personal_data = json.load(pf)

    # Ensure the transactions file exists.
    transactions_path = os.path.join(directory, transactions_file)
    if not os.path.exists(transactions_path):
        print(f"[ERROR] Transactions file not found: {transactions_file}")
        return

    # Load the merged transactions data.
    with open(transactions_path, "r", encoding="utf-8") as tf:
        transactions_data = json.load(tf)

    # Combine the data into a single structure.
    final_data = {
        "Personal Information": personal_data,
        "Transactions": transactions_data.get("Transactions", [])
    }

    # Save the final merged JSON with literal non-ASCII characters.
    output_path = os.path.join(directory, output_file)
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(final_data, out, indent=4, ensure_ascii=False)

    print(f"[INFO] Final merged JSON written to {output_path}")

if __name__ == "__main__":
    merge_personal_and_transactions() 