import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser(description="Genera transacciones sintéticas reproducibles sin guardar datasets en Git")
    parser.add_argument("--rows", type=int, default=10000); parser.add_argument("--output", type=Path, default=Path("work/transactions.csv")); parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(); random.seed(args.seed); args.output.parent.mkdir(parents=True, exist_ok=True)
    start = date(2025, 1, 1)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(["ID", "CustomerID", "BranchID", "Amount", "TransactionDate"])
        for i in range(1, args.rows + 1):
            amount = round(random.uniform(5, 2500), 2); customer = random.randint(1, 50000); branch = random.randint(1, 20); when = start + timedelta(days=random.randint(0, 364))
            if i % 997 == 0: amount = -amount
            if i % 991 == 0: amount = "ABC"
            if i % 983 == 0: customer = 999999
            if i % 977 == 0: writer.writerow([i - 1, customer, branch, amount, when.isoformat()])
            writer.writerow([i, customer, branch, amount, when.isoformat() if i % 953 else "not-a-date"])
    print(f"Generated {args.rows:,} requested rows at {args.output}")

if __name__ == "__main__": main()
