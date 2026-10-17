"""monarch-import-from-truist-statements package."""

from .models import Transaction, StatementSummary, ParsedStatement, ExtractionResult
from .parser import parse_statement_pdf
from .processor import process_statements_directory
from .exporter import (
    export_monarch_transactions_csv,
    export_monarch_balance_history_csv,
    export_all,
)

__version__ = "0.1.0"
__all__ = [
    "Transaction",
    "StatementSummary",
    "ParsedStatement",
    "ExtractionResult",
    "parse_statement_pdf",
    "process_statements_directory",
    "export_monarch_transactions_csv",
    "export_monarch_balance_history_csv",
    "export_all",
]
