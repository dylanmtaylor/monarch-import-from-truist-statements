"""Parser for Truist bank statement PDFs."""

import os
import re
from datetime import datetime, date
from typing import List, Tuple, Optional
import pypdf

from .models import Transaction, StatementSummary, ParsedStatement


def clean_amount(s: str) -> float:
    """Parse monetary string '$1,234.56' or '1,234.56' to float."""
    return float(s.replace(",", "").replace("$", "").strip())


def parse_statement_pdf(file_path: str) -> ParsedStatement:
    """Extract summary and transactions from a Truist bank statement PDF.
    
    Args:
        file_path: Path to the PDF file.
        
    Returns:
        ParsedStatement containing metadata, summary, and transaction list.
    """
    reader = pypdf.PdfReader(file_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    
    # 1. Summary parsing
    prev_m = re.search(
        r"Your previous balance as of\s+(\d{2}/\d{2}/\d{4})\s+\$?([0-9,]+\.[0-9]{2})",
        text
    )
    new_m = re.search(
        r"Your new balance as of\s+(\d{2}/\d{2}/\d{4})\s+=\s*\$?([0-9,]+\.[0-9]{2})",
        text
    )
    if not (prev_m and new_m):
        raise ValueError(
            f"Could not locate previous/new balance summary in '{os.path.basename(file_path)}'."
        )
    
    start_date = datetime.strptime(prev_m.group(1), "%m/%d/%Y").date()
    end_date = datetime.strptime(new_m.group(1), "%m/%d/%Y").date()
    prev_bal = clean_amount(prev_m.group(2))
    new_bal = clean_amount(new_m.group(2))
    
    # Stated totals in summary section
    checks_m = re.search(r"\n\s*Checks\s+-\s+([0-9,]+\.[0-9]{2})", text)
    debits_m = re.search(r"\n\s*Other withdrawals, debits and service charges\s+-\s+([0-9,]+\.[0-9]{2})", text)
    credits_m = re.search(r"\n\s*Deposits, credits and interest\s+\+\s+([0-9,]+\.[0-9]{2})", text)
    
    total_checks = clean_amount(checks_m.group(1)) if checks_m else 0.0
    total_debits = clean_amount(debits_m.group(1)) if debits_m else 0.0
    total_credits = clean_amount(credits_m.group(1)) if credits_m else 0.0
    
    # Account identification
    acct_m = re.search(r"[¡\*\-•]?\s*([A-Z0-9\-\s]+?(?:CHECKING|SAVINGS|GOLD-MM))\s+([0-9]{5,})", text)
    account_name = acct_m.group(1).strip() if acct_m else "Truist Account"
    account_number = acct_m.group(2).strip() if acct_m else ""
    
    summary = StatementSummary(
        start_date=start_date,
        end_date=end_date,
        previous_balance=prev_bal,
        new_balance=new_bal,
        total_checks=total_checks,
        total_debits=total_debits,
        total_credits=total_credits,
        account_name=account_name,
        account_number=account_number,
    )
    
    # 2. Extract transactions from tables
    summary_idx = text.find("Account summary")
    content = text[summary_idx:] if summary_idx != -1 else text
    
    def resolve_date(mmdd: str) -> date:
        month, day = map(int, mmdd.split("/"))
        if start_date.year == end_date.year:
            year = start_date.year
        else:
            if month >= start_date.month:
                year = start_date.year
            else:
                year = end_date.year
        return date(year, month, day)
    
    transactions: List[Transaction] = []
    fname = os.path.basename(file_path)
    
    # Checks table
    checks_sec = re.search(
        r"\n\s*Checks\s*\n.*?Total checks\s*=\s*\$?\s*([0-9,]+\.[0-9]{2})",
        content,
        re.DOTALL
    )
    if checks_sec:
        for line in checks_sec.group(0).splitlines():
            m = re.match(r"^\s*(\d{2}/\d{2})\s+[\*\s]*(\d+)\s+([0-9,]+\.[0-9]{2})$", line.strip())
            if m:
                tx_date = resolve_date(m.group(1))
                check_num = m.group(2)
                amt = -clean_amount(m.group(3))
                transactions.append(
                    Transaction(
                        date=tx_date,
                        amount=amt,
                        description=f"Check #{check_num}",
                        category_type="CHECK",
                        check_number=check_num,
                        statement_file=fname,
                    )
                )
                
    # Other withdrawals, debits, service charges
    debits_sec = re.search(
        r"\n\s*Other withdrawals, debits and service charges\s*\n.*?Total other withdrawals[^\n]*=\s*\$?\s*([0-9,]+\.[0-9]{2})",
        content,
        re.DOTALL
    )
    if debits_sec:
        for line in debits_sec.group(0).splitlines():
            m = re.match(r"^\s*(\d{2}/\d{2})\s+(.+?)\s+([0-9,]+\.[0-9]{2})$", line.strip())
            if m and not line.strip().startswith("Total"):
                tx_date = resolve_date(m.group(1))
                desc = m.group(2).strip()
                amt = -clean_amount(m.group(3))
                transactions.append(
                    Transaction(
                        date=tx_date,
                        amount=amt,
                        description=desc,
                        category_type="DEBIT",
                        statement_file=fname,
                    )
                )
                
    # Deposits, credits, and interest
    credits_sec = re.search(
        r"\n\s*Deposits, credits and interest\s*\n.*?Total deposits[^\n]*=\s*\$?\s*([0-9,]+\.[0-9]{2})",
        content,
        re.DOTALL
    )
    if credits_sec:
        for line in credits_sec.group(0).splitlines():
            m = re.match(r"^\s*(\d{2}/\d{2})\s+(.+?)\s+([0-9,]+\.[0-9]{2})$", line.strip())
            if m and not line.strip().startswith("Total"):
                tx_date = resolve_date(m.group(1))
                desc = m.group(2).strip()
                amt = clean_amount(m.group(3))
                transactions.append(
                    Transaction(
                        date=tx_date,
                        amount=amt,
                        description=desc,
                        category_type="CREDIT",
                        statement_file=fname,
                    )
                )
                
    # Reconcile calculations
    calc_ending = round(prev_bal + sum(tx.amount for tx in transactions), 2)
    discrepancy = round(calc_ending - new_bal, 2)
    reconciled = (abs(discrepancy) < 0.001)
    
    return ParsedStatement(
        file_path=file_path,
        summary=summary,
        transactions=transactions,
        reconciled=reconciled,
        discrepancy=discrepancy,
    )
