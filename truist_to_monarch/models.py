"""Data models for Truist statements and Monarch exports."""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class Transaction:
    """Represents a single parsed transaction."""
    date: date
    amount: float  # Positive for credits/deposits, negative for debits/checks
    description: str
    category_type: str  # 'DEBIT', 'CREDIT', 'CHECK'
    check_number: Optional[str] = None
    statement_file: str = ""


@dataclass
class StatementSummary:
    """Represents statement header balance & metadata information."""
    start_date: date
    end_date: date
    previous_balance: float
    new_balance: float
    total_checks: float
    total_debits: float
    total_credits: float
    account_name: str = ""
    account_number: str = ""


@dataclass
class ParsedStatement:
    """Represents a parsed statement containing summary and all transactions."""
    file_path: str
    summary: StatementSummary
    transactions: List[Transaction] = field(default_factory=list)
    reconciled: bool = True
    discrepancy: float = 0.0


@dataclass
class ExtractionResult:
    """Aggregated result across all parsed statements."""
    statements: List[ParsedStatement]
    overall_start_date: date
    overall_end_date: date
    all_transactions: List[Transaction]
    daily_balances: List[tuple]  # List of (date, balance)
    warnings: List[str] = field(default_factory=list)
