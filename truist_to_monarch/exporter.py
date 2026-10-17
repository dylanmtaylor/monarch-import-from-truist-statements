"""Exporters for Monarch Money formatted CSV files."""

import csv
import os
from datetime import date
from typing import List, Tuple

from .models import Transaction, ExtractionResult


def export_monarch_transactions_csv(
    transactions: List[Transaction],
    output_path: str,
    account_name: str = "Truist Checking"
) -> str:
    """Export transactions to Monarch-compatible CSV.
    
    Format:
        Date,Merchant,Category,Account,Original Statement,Notes,Amount
        
    Args:
        transactions: List of parsed Transaction objects.
        output_path: Target CSV file path.
        account_name: Name of the account as labeled in Monarch.
        
    Returns:
        The written file path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Date",
            "Merchant",
            "Category",
            "Account",
            "Original Statement",
            "Notes",
            "Amount",
        ])
        for tx in transactions:
            writer.writerow([
                tx.date.strftime("%Y-%m-%d"),
                tx.description,
                "",  # Leave category empty so Monarch auto-categorizes
                account_name,
                tx.description,
                f"Check #{tx.check_number}" if tx.check_number else "",
                f"{tx.amount:.2f}",
            ])
            
    return output_path


def export_monarch_balance_history_csv(
    daily_balances: List[Tuple[date, float]],
    output_path: str
) -> str:
    """Export daily balance snapshots to Monarch-compatible CSV.
    
    Format:
        Date,Balance
        
    Args:
        daily_balances: List of (date, balance) tuples.
        output_path: Target CSV file path.
        
    Returns:
        The written file path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Balance"])
        for d, bal in daily_balances:
            writer.writerow([
                d.strftime("%Y-%m-%d"),
                f"{bal:.2f}",
            ])
            
    return output_path


def export_all(
    result: ExtractionResult,
    output_dir: str,
    account_name: str = "Truist Checking"
) -> Tuple[str, str]:
    """Export both transactions and daily balance history to output directory.
    
    Args:
        result: ExtractionResult containing statements and daily balances.
        output_dir: Target output folder.
        account_name: Account label for Monarch.
        
    Returns:
        Tuple of (transactions_csv_path, balance_history_csv_path).
    """
    tx_file = os.path.join(output_dir, "truist_monarch_transactions.csv")
    bal_file = os.path.join(output_dir, "truist_monarch_balance_history.csv")
    
    export_monarch_transactions_csv(result.all_transactions, tx_file, account_name)
    export_monarch_balance_history_csv(result.daily_balances, bal_file)
    
    return tx_file, bal_file
