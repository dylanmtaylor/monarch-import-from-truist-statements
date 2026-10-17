# Monarch Import from Truist Statements (`truist-to-monarch`)

Convert a folder of Truist (and BB&T) bank statement PDFs into **Monarch Money-compatible** transaction and continuous daily balance history CSV files.

---

## 🎯 The Problem

When you link a bank account to [Monarch Money](https://www.monarchmoney.com/) via Plaid, Finicity, or MX:
1. **Aggregators typically pull only 30 to 90 days of balance history**, even if they pull months or years of transactions.
2. Monarch stores **Transactions** and **Account Balance History** in separate databases. Adding past transactions does *not* automatically populate your net worth or account balance graphs.
3. Without historical balances, your past net worth chart will look flat, blank, or spike artificially on the day you linked the account.

This tool extracts every transaction from your Truist PDF statements, validates the balances down to the penny, and produces:
- **`truist_monarch_transactions.csv`**: Formatted for Monarch's transaction importer.
- **`truist_monarch_balance_history.csv`**: A continuous daily timeline with forward-filled balances for every single calendar day, giving you a smooth, accurate historical net worth chart in Monarch.

---

## ✨ Features

- **Automatic Multi-Year Ordering**: Point the tool at a folder of statements; it parses statement dates, determines the multi-year timeline, and sorts them chronologically.
- **Mathematical Reconciliation**: Every statement is verified down to the penny:
  $$\text{Previous Balance} - \text{Checks} - \text{Debits} + \text{Credits} = \text{Stated New Balance}$$
- **Statement Continuity Verification**: Automatically verifies seamless balance handoffs from statement to statement and warns if any monthly statement is missing.
- **Continuous Daily Balance History**: Generates daily balance snapshots (carrying forward balances on non-transaction days) to prevent chart spikes and gaps in Monarch.
- **100% Local & Private**: All parsing happens completely on your machine using Python. No network calls, no cloud services, and no data leaves your computer.

---

## 🚀 Installation

### Requirements
- Python 3.8 or higher
- `pypdf` (installed automatically)

### Install via pip / git
```bash
git clone https://github.com/<your-username>/monarch-import-from-truist-statements.git
cd monarch-import-from-truist-statements
pip install .
```

Or install in editable/development mode:
```bash
pip install -e ".[dev]"
```

---

## 💻 Usage

Run the CLI tool pointing to your folder of Truist statement PDFs:

```bash
truist-to-monarch "/path/to/Truist Statements" -o ./output -a "Truist Checking"
```

Or run via Python module:
```bash
python3 -m truist_to_monarch "/path/to/Truist Statements" -o ./output -a "Truist Checking"
```

### Options
| Option | Short | Default | Description |
|---|---|---|---|
| `STATEMENT_DIR` | (Positional) | Required | Path to the directory containing Truist PDF statements. |
| `--output-dir` | `-o` | `./output` | Destination directory for the generated CSV files. |
| `--account-name` | `-a` | `Truist Checking` | Account name as labeled in your Monarch Money workspace. |
| `--allow-non-pdf` | | `False` | Allow non-PDF files inside the statements directory without warning. |

### Example Output
```text
==========================================================
 Truist Statement to Monarch Money Converter
==========================================================
Input directory:  /home/user/Documents/Truist Statements
Output directory: /home/user/Downloads/truist_monarch_export
Monarch account:  Truist Checking
----------------------------------------------------------
✅ Successfully parsed 88 statements.
📅 Overall Date Range: 2019-05-20 -> 2026-09-22
💳 Total Transactions: 1893
📈 Total Daily Balance Snapshots: 2683

✨ All statement-to-statement balances and dates reconciled perfectly!

----------------------------------------------------------
🎉 Export complete! Generated Monarch files:
  1. Transactions:     ./output/truist_monarch_transactions.csv
  2. Balance History:  ./output/truist_monarch_balance_history.csv
----------------------------------------------------------
```

---

## 📥 How to Import into Monarch Money

Imports must be performed on the **Monarch Money Web App** (not mobile):

### Step 1: Import Balance History (Recommended First)
1. In Monarch, go to **Accounts** and select your Truist account.
2. Click **Edit** in the top-right corner of the account screen.
3. Select **"Upload balance history"** (or **"Import balance history"**).
4. Upload `truist_monarch_balance_history.csv`.
5. Confirm column mapping (`Date` and `Balance`), review the preview, and click **Import**.

### Step 2: Import Transactions
1. From the same account page, click **Edit** -> **"Upload transactions"** (or **"Import transactions"**).
2. Upload `truist_monarch_transactions.csv`.
3. Confirm the column mappings (`Date`, `Amount`, `Merchant`, `Account`, etc.).
4. Review and complete the import.

---

## 🧪 Testing

To run the test suite (using synthetic mock data with zero personal information):

```bash
python3 -m unittest discover -s tests
```

---

## 🔒 Security & Privacy

Your financial data is sensitive. 
- The repository `.gitignore` explicitly prevents PDF and CSV files from being tracked.
- Test suites contain strictly synthetic fixtures.
- Always review `git status` before committing to ensure no private bank statements or personal files are included.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
