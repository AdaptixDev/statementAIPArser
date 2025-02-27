"""Data processing utilities for merging and transforming financial data."""

import json
import csv
import os
import logging
from typing import Dict, Any, List, Optional

from backend.src.config.settings import Settings
from backend.src.utils.exceptions import DataProcessingError

logger = logging.getLogger(__name__)

class DataProcessor:
    """Class for processing and merging financial data."""
    
    @staticmethod
    def merge_transaction_files(
        transaction_files: List[str],
        output_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Merge multiple transaction JSON files into a single list of transactions.
        
        Args:
            transaction_files: List of paths to transaction JSON files
            output_file: Path to save the merged transactions (optional)
            
        Returns:
            List of merged transaction dictionaries
        """
        try:
            all_transactions = []
            
            # Process each file
            for file_path in transaction_files:
                logger.info(f"Processing file: {file_path}")
                
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                # Extract transactions from the file
                if isinstance(data, list):
                    # File contains a list of transactions
                    transactions = data
                elif isinstance(data, dict) and 'transactions' in data:
                    # File contains a dictionary with a 'transactions' key
                    transactions = data['transactions']
                else:
                    # Assume the entire object is a single transaction
                    transactions = [data]
                    
                logger.info(f"Found {len(transactions)} transactions in {file_path}")
                all_transactions.extend(transactions)
                
            # Sort transactions by date if they have a date field
            if all_transactions and 'Date' in all_transactions[0]:
                all_transactions.sort(key=lambda x: x.get('Date', ''))
                
            # Save to output file if specified
            if output_file and Settings.ENABLE_FILE_STORAGE:
                output_dir = os.path.dirname(output_file)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    
                with open(output_file, 'w') as f:
                    json.dump(all_transactions, f, indent=2)
                logger.info(f"Saved merged transactions to {output_file}")
                
            return all_transactions
            
        except Exception as e:
            logger.error(f"Error merging transaction files: {str(e)}")
            raise DataProcessingError(f"Error merging transaction files: {str(e)}")
            
    @staticmethod
    def merge_personal_and_transactions(
        personal_info: Dict[str, Any],
        transactions: List[Dict[str, Any]],
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Merge personal information with transaction data and calculate summary statistics.
        
        Args:
            personal_info: Dictionary containing personal information
            transactions: List of transaction dictionaries
            output_file: Path to save the merged data (optional)
            
        Returns:
            Dictionary containing merged data with summary statistics
        """
        try:
            # Create the merged data structure
            merged_data = {
                "personal_info": personal_info,
                "transactions": transactions,
                "summary": {}
            }
            
            # Calculate summary statistics
            total_in = 0
            total_out = 0
            categories_in = {}
            categories_out = {}
            
            for transaction in transactions:
                amount = float(transaction.get('Amount', 0))
                direction = transaction.get('Direction', '').lower()
                category = transaction.get('Category', 'Uncategorized')
                
                if direction in ['in', 'paid in', 'deposit']:
                    total_in += amount
                    categories_in[category] = categories_in.get(category, 0) + amount
                elif direction in ['out', 'withdrawn', 'payment']:
                    total_out += amount
                    categories_out[category] = categories_out.get(category, 0) + amount
                    
            # Add summary statistics
            merged_data['summary'] = {
                "total_in": total_in,
                "total_out": total_out,
                "net_change": total_in - total_out,
                "categories_in": categories_in,
                "categories_out": categories_out
            }
            
            # Add personal info summary if available
            if personal_info:
                # Add statement period
                if 'statement_period' in personal_info:
                    merged_data['summary']['statement_period'] = personal_info['statement_period']
                    
                # Add opening and closing balances
                if 'opening_balance' in personal_info:
                    merged_data['summary']['opening_balance'] = personal_info['opening_balance']
                    
                if 'closing_balance' in personal_info:
                    merged_data['summary']['closing_balance'] = personal_info['closing_balance']
                    
            # Save to output file if specified
            if output_file and Settings.ENABLE_FILE_STORAGE:
                output_dir = os.path.dirname(output_file)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    
                with open(output_file, 'w') as f:
                    json.dump(merged_data, f, indent=2)
                logger.info(f"Saved merged data to {output_file}")
                
            return merged_data
            
        except Exception as e:
            logger.error(f"Error merging personal info and transactions: {str(e)}")
            raise DataProcessingError(f"Error merging personal info and transactions: {str(e)}")
            
    @staticmethod
    def export_transactions_to_csv(
        transactions: List[Dict[str, Any]],
        output_file: str
    ) -> None:
        """
        Export transactions to a CSV file.
        
        Args:
            transactions: List of transaction dictionaries
            output_file: Path to save the CSV file
        """
        try:
            if not transactions:
                logger.warning("No transactions to export")
                return
                
            # Determine the fieldnames from the first transaction
            fieldnames = list(transactions[0].keys())
            
            # Create the directory if it doesn't exist
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # Write to CSV
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(transactions)
                
            logger.info(f"Exported {len(transactions)} transactions to {output_file}")
            
        except Exception as e:
            logger.error(f"Error exporting transactions to CSV: {str(e)}")
            raise DataProcessingError(f"Error exporting transactions to CSV: {str(e)}") 