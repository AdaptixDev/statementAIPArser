
import json
import os
from datetime import datetime
from typing import List, Dict
import threading

class TransactionMerger:
    def __init__(self):
        self.transactions = []
        self._lock = threading.Lock()
        
    def parse_date(self, date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, "%d %b %Y")
        except ValueError:
            try:
                return datetime.strptime(f"{date_str} 2024", "%d %b %Y")
            except ValueError:
                return datetime.max
    
    def merge_json_file(self, json_path: str) -> None:
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            if not isinstance(data, dict) or 'Transactions' not in data:
                return
                
            with self._lock:
                self.transactions.extend(data['Transactions'])
                # Sort after each merge
                self.transactions.sort(
                    key=lambda x: self.parse_date(x.get('Date', ''))
                )
                
            # Write current state to combined file
            self.save_combined_json()
                
        except Exception as e:
            print(f"Error merging {json_path}: {str(e)}")
            
    def save_combined_json(self) -> None:
        output = {'Transactions': self.transactions}
        with open('combined_statement.json', 'w') as f:
            json.dump(output, f, indent=2)
