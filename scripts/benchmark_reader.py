from __future__ import annotations

import argparse
import csv
import tempfile
import time
from pathlib import Path

from app.readers import DelimitedReader


def create_dataset(path: Path, rows: int) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ID", "Amount", "Status"])
        for index in range(1, rows + 1):
            writer.writerow([index, index * 1.25, "ACTIVE"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark reproducible delimited-file streaming")
    parser.add_argument("--rows", type=int, default=100_000)
    args = parser.parse_args()
    if args.rows < 1: raise SystemExit("--rows debe ser positivo")
    with tempfile.TemporaryDirectory(prefix="kiriox-benchmark-") as directory:
        path = Path(directory) / "transactions.csv"
        create_dataset(path, args.rows)
        started = time.perf_counter(); read = sum(1 for _ in DelimitedReader().rows(path, {})); elapsed = time.perf_counter() - started
    print(f"rows={read} seconds={elapsed:.3f} rows_per_second={read / elapsed:,.0f}")


if __name__ == "__main__":
    main()
