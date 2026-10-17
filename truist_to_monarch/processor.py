"""Processes directory of Truist statements, verifies continuity, and builds daily balance timelines."""

import glob
import os
from datetime import timedelta, date
from typing import List, Dict
from collections import defaultdict

from .models import ExtractionResult, ParsedStatement, Transaction
from .parser import parse_statement_pdf


def process_statements_directory(
    dir_path: str,
    strict_directory_check: bool = True
) -> ExtractionResult:
    """Read all statements in directory, verify continuity, and calculate daily balances.
    
    Args:
        dir_path: Path to folder containing Truist PDF statements.
        strict_directory_check: If True, warns/fails if non-PDF files exist in folder.
        
    Returns:
        ExtractionResult containing parsed statements, sorted transactions,
        continuous daily balances, and any continuity warnings.
    """
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(f"Directory not found: '{dir_path}'")
        
    all_entries = os.listdir(dir_path)
    pdf_files = [
        os.path.join(dir_path, f)
        for f in all_entries
        if f.lower().endswith(".pdf")
    ]
    
    warnings = []
    
    non_pdf = [
        f for f in all_entries
        if not f.lower().endswith(".pdf") and not f.startswith(".")
    ]
    if non_pdf and strict_directory_check:
        warnings.append(
            f"Found {len(non_pdf)} non-PDF files in folder (e.g., {non_pdf[:3]}). "
            "Truist statement directory should ideally contain only statements."
        )
        
    if not pdf_files:
        raise ValueError(f"No PDF statements found in directory: '{dir_path}'")
        
    parsed_statements: List[ParsedStatement] = []
    for pdf_path in pdf_files:
        stmt = parse_statement_pdf(pdf_path)
        if not stmt.reconciled:
            warnings.append(
                f"Reconciliation error in '{os.path.basename(pdf_path)}': "
                f"Discrepancy of ${stmt.discrepancy:+.2f}."
            )
        parsed_statements.append(stmt)
        
    # Sort statements chronologically by statement start date
    parsed_statements.sort(key=lambda s: s.summary.start_date)
    
    # Check statement-to-statement continuity
    for i in range(len(parsed_statements) - 1):
        curr_s = parsed_statements[i]
        next_s = parsed_statements[i + 1]
        
        # Check balance handoff
        bal_diff = round(next_s.summary.previous_balance - curr_s.summary.new_balance, 2)
        if abs(bal_diff) > 0.001:
            warnings.append(
                f"Balance gap between '{os.path.basename(curr_s.file_path)}' "
                f"(ended {curr_s.summary.end_date} with ${curr_s.summary.new_balance:,.2f}) "
                f"and '{os.path.basename(next_s.file_path)}' "
                f"(started {next_s.summary.start_date} with ${next_s.summary.previous_balance:,.2f}): "
                f"difference of ${bal_diff:+.2f}."
            )
            
        # Check date gap
        date_gap = (next_s.summary.start_date - curr_s.summary.end_date).days
        if date_gap > 1:
            warnings.append(
                f"Date gap between '{os.path.basename(curr_s.file_path)}' "
                f"({curr_s.summary.end_date}) and '{os.path.basename(next_s.file_path)}' "
                f"({next_s.summary.start_date}): {date_gap} days unaccounted for."
            )
            
    # Aggregate and sort all transactions
    all_transactions: List[Transaction] = []
    for stmt in parsed_statements:
        all_transactions.extend(stmt.transactions)
        
    all_transactions.sort(key=lambda tx: tx.date)
    
    # Build continuous daily balance history
    overall_start = parsed_statements[0].summary.start_date
    overall_end = parsed_statements[-1].summary.end_date
    
    tx_by_date: Dict[date, List[Transaction]] = defaultdict(list)
    for tx in all_transactions:
        tx_by_date[tx.date].append(tx)
        
    daily_balances = []
    running_balance = parsed_statements[0].summary.previous_balance
    
    # Store initial day balance
    curr_date = overall_start
    while curr_date <= overall_end:
        day_txs = tx_by_date.get(curr_date, [])
        if day_txs:
            net_change = sum(tx.amount for tx in day_txs)
            running_balance = round(running_balance + net_change, 2)
            
        daily_balances.append((curr_date, running_balance))
        curr_date += timedelta(days=1)
        
    return ExtractionResult(
        statements=parsed_statements,
        overall_start_date=overall_start,
        overall_end_date=overall_end,
        all_transactions=all_transactions,
        daily_balances=daily_balances,
        warnings=warnings,
    )
