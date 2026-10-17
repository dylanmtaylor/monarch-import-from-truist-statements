"""Unit tests for truist_to_monarch package using synthetic/mock data only.
No real personal or financial data is included.
"""

import os
import tempfile
import csv
from datetime import date
import unittest

from truist_to_monarch.models import (
    Transaction,
    StatementSummary,
    ParsedStatement,
    ExtractionResult,
)
from truist_to_monarch.parser import clean_amount
from truist_to_monarch.exporter import (
    export_monarch_transactions_csv,
    export_monarch_balance_history_csv,
    export_all,
)


class TestParserHelpers(unittest.TestCase):
    """Test helper parsing functions."""

    def test_clean_amount(self):
        self.assertEqual(clean_amount("100.00"), 100.0)
        self.assertEqual(clean_amount("$1,234.56"), 1234.56)
        self.assertEqual(clean_amount(" 0.01 "), 0.01)


class TestExporters(unittest.TestCase):
    """Test Monarch CSV export functions."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def test_export_monarch_transactions_csv(self):
        txs = [
            Transaction(
                date=date(2024, 1, 15),
                amount=-50.25,
                description="SAMPLE GROCERY STORE",
                category_type="DEBIT",
            ),
            Transaction(
                date=date(2024, 1, 16),
                amount=1500.00,
                description="SAMPLE PAYROLL DIRECT DEP",
                category_type="CREDIT",
            ),
            Transaction(
                date=date(2024, 1, 17),
                amount=-100.00,
                description="Check #101",
                category_type="CHECK",
                check_number="101",
            ),
        ]
        out_csv = os.path.join(self.test_dir, "test_tx.csv")
        export_monarch_transactions_csv(txs, out_csv, account_name="Test Checking")

        with open(out_csv, "r", encoding="utf-8") as f:
            reader = list(csv.reader(f))

        # Check headers
        self.assertEqual(
            reader[0],
            ["Date", "Merchant", "Category", "Account", "Original Statement", "Notes", "Amount"]
        )
        self.assertEqual(len(reader), 4)
        self.assertEqual(reader[1][0], "2024-01-15")
        self.assertEqual(reader[1][6], "-50.25")
        self.assertEqual(reader[2][6], "1500.00")
        self.assertEqual(reader[3][5], "Check #101")

    def test_export_monarch_balance_history_csv(self):
        balances = [
            (date(2024, 1, 1), 1000.00),
            (date(2024, 1, 2), 950.00),
            (date(2024, 1, 3), 950.00),
        ]
        out_csv = os.path.join(self.test_dir, "test_bal.csv")
        export_monarch_balance_history_csv(balances, out_csv)

        with open(out_csv, "r", encoding="utf-8") as f:
            reader = list(csv.reader(f))

        self.assertEqual(reader[0], ["Date", "Balance"])
        self.assertEqual(len(reader), 4)
        self.assertEqual(reader[1], ["2024-01-01", "1000.00"])
        self.assertEqual(reader[2], ["2024-01-02", "950.00"])
        self.assertEqual(reader[3], ["2024-01-03", "950.00"])


if __name__ == "__main__":
    unittest.main()
