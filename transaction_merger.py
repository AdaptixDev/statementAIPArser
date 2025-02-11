
import json
import os
from datetime import datetime
from typing import List, Dict
import threading

class TransactionMerger:
    def __init__(self):
        self.transactions = []
        self._lock = threading.Lock()
        # Clear existing combined statement
        if os.path.exists('combined_statement.json'):
            os.remove('combined_statement.json')
        
    def parse_date(self, date_str: str) -> datetime:
        # Handle various date formats
        formats = [
            "%d %b %y",
            "%d %b %Y",
            "%d-%m-%y",
            "%d-%m-%Y",
            "%d %b",  # Current year assumed
        ]
        
        for fmt in formats:
            try:
                if len(date_str.split()) == 2:  # Missing year
                    date_str += " 24"  # Assume 2024
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return datetime.max
    
    def transaction_key(self, trans: Dict) -> str:
        """Create unique key for transaction"""
        return f"{trans.get('Date', '')}-{trans.get('Description', '')}-{trans.get('Amount', '')}-{trans.get('Direction', '')}"
    
    def merge_json_file(self, json_path: str) -> None:
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            if not isinstance(data, dict) or 'Transactions' not in data:
                return
                
            with self._lock:
                # Use dictionary to prevent duplicates
                trans_dict = {
                    self.transaction_key(t): t 
                    for t in self.transactions + data['Transactions']
                }
                
                # Convert back to list and sort
                self.transactions = sorted(
                    trans_dict.values(),
                    key=lambda x: (
                        self.parse_date(x.get('Date', '')),
                        float(x.get('Balance', 0))
                    ),
                    reverse=True  # Most recent first
                )
                
            # Write current state to combined file
            self.save_combined_json()
                
        except Exception as e:
            print(f"Error merging {json_path}: {str(e)}")
            
    def save_combined_json(self) -> None:
        output = {'Transactions': self.transactions}
        with open('combined_statement.json', 'w') as f:
            json.dump(output, f, indent=2)
