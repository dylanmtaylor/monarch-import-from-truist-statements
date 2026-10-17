"""Command-line interface for truist-to-monarch."""

import argparse
import os
import sys

from .processor import process_statements_directory
from .exporter import export_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="truist-to-monarch",
        description=(
            "Convert Truist PDF bank statements into Monarch Money formatted "
            "transaction and continuous daily balance history CSV files."
        ),
    )
    parser.add_argument(
        "input_dir",
        metavar="STATEMENT_DIR",
        help="Path to directory containing Truist PDF statements.",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="./output",
        help="Directory to save the resulting CSV files (default: './output').",
    )
    parser.add_argument(
        "-a", "--account-name",
        default="Truist Checking",
        help="Account label to use in Monarch (default: 'Truist Checking').",
    )
    parser.add_argument(
        "--allow-non-pdf",
        action="store_true",
        help="Permit non-PDF files in the statements directory without warning.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)

    print("==========================================================")
    print(" Truist Statement to Monarch Money Converter")
    print("==========================================================")
    print(f"Input directory:  {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Monarch account:  {args.account_name}")
    print("----------------------------------------------------------")

    try:
        result = process_statements_directory(
            input_dir,
            strict_directory_check=not args.allow_non_pdf,
        )
    except Exception as e:
        print(f"\n❌ Error processing statements: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Successfully parsed {len(result.statements)} statements.")
    print(f"📅 Overall Date Range: {result.overall_start_date} -> {result.overall_end_date}")
    print(f"💳 Total Transactions: {len(result.all_transactions)}")
    print(f"📈 Total Daily Balance Snapshots: {len(result.daily_balances)}")

    if result.warnings:
        print("\n⚠️ Warnings & Continuity Notices:")
        for w in result.warnings:
            print(f"  - {w}")
    else:
        print("\n✨ All statement-to-statement balances and dates reconciled perfectly!")

    tx_file, bal_file = export_all(result, output_dir, account_name=args.account_name)

    print("\n----------------------------------------------------------")
    print("🎉 Export complete! Generated Monarch files:")
    print(f"  1. Transactions:     {tx_file}")
    print(f"  2. Balance History:  {bal_file}")
    print("----------------------------------------------------------")
    print("Next Steps in Monarch Money (Web App):")
    print("  1. Import Transactions:")
    print("     Accounts -> Select Account -> Edit -> 'Upload transactions'")
    print(f"     (or upload {os.path.basename(tx_file)})")
    print("  2. Import Balance History:")
    print("     Accounts -> Select Account -> Edit -> 'Upload balance history'")
    print(f"     (upload {os.path.basename(bal_file)})")
    print("==========================================================")


if __name__ == "__main__":
    main()
