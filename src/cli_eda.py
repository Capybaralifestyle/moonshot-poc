"""Command‑line tool for exploratory data analysis (EDA) of a cost‑estimation dataset.

This script loads a tabular dataset (CSV or ARFF) and prints a concise summary
to the console, including dataset shape, column types, missing values, basic
statistics for numeric columns, top pairwise correlations, domain distribution
if a domain column is provided, and a simple outlier detection report using
IsolationForest.  Output sections are color‑coded using ``colorama`` for
improved readability on the command line.

Usage::

    python src/cli_eda.py /path/to/dataset.csv --domain-col Application_Group

If the dataset path is omitted, the script looks for the ``DATASET_PATH``
environment variable.  Similarly, the domain column can be provided via
``--domain-col`` or the ``DOMAIN_COLUMN`` environment variable.  Supported
file formats are ``.csv`` and ``.arff``.  The script exits gracefully if
any errors occur while loading or processing the data.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

import pandas as pd
from scipy.io import arff  # type: ignore
from colorama import Fore, Style, init as colorama_init

from sklearn.ensemble import IsolationForest


def load_dataset(path: str) -> Optional[pd.DataFrame]:
    """Load a dataset from CSV or ARFF into a DataFrame.

    :param path: Path to the dataset file.
    :return: DataFrame if successful, otherwise None.
    """
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".csv":
            return pd.read_csv(path)
        elif ext == ".arff":
            data, meta = arff.loadarff(path)
            df = pd.DataFrame(data)
            # decode bytes to strings for nominal features
            for col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].apply(lambda x: x.decode("utf-8") if isinstance(x, bytes) else x)
            return df
        else:
            return None
    except Exception:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Perform exploratory data analysis on a cost‑estimation dataset.")
    parser.add_argument(
        "dataset", nargs="?", default=None,
        help="Path to the dataset file (.csv or .arff). If omitted, DATASET_PATH env var is used."
    )
    parser.add_argument(
        "--domain-col", dest="domain_col", default=None,
        help="Optional name of a domain column for distribution analysis. Overrides DOMAIN_COLUMN env var."
    )
    args = parser.parse_args()

    # Determine dataset path
    dataset_path: Optional[str] = args.dataset or os.getenv("DATASET_PATH")
    if not dataset_path:
        print(Fore.RED + "No dataset path provided and DATASET_PATH environment variable is unset." + Style.RESET_ALL)
        sys.exit(1)
    # Load dataset
    df = load_dataset(dataset_path)
    if df is None or df.empty:
        print(Fore.RED + f"Failed to load dataset from {dataset_path}. Supported formats are CSV and ARFF." + Style.RESET_ALL)
        sys.exit(1)

    # Determine domain column
    domain_col: Optional[str] = args.domain_col or os.getenv("DOMAIN_COLUMN")
    if domain_col and domain_col not in df.columns:
        # warn and ignore
        print(Fore.YELLOW + f"Warning: specified domain column '{domain_col}' not found in dataset; ignoring." + Style.RESET_ALL)
        domain_col = None

    # Initialize color output
    colorama_init(autoreset=True)

    # Print dataset summary
    print(Fore.CYAN + f"Loaded dataset: {dataset_path}")
    print(Fore.CYAN + f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")

    # Column types
    print(Fore.CYAN + "Column types:")
    for col in df.columns:
        dtype = str(df[col].dtype)
        print(Fore.CYAN + f"  {col}: {dtype}")

    # Missing values
    missing = df.isnull().sum()
    if missing.any():
        print(Fore.MAGENTA + "Missing values per column:")
        for col in missing.index:
            if missing[col] > 0:
                print(Fore.MAGENTA + f"  {col}: {missing[col]}")
    else:
        print(Fore.MAGENTA + "No missing values detected.")

    # Numeric summary
    numeric_cols = df.select_dtypes(include=[float, int]).columns
    if len(numeric_cols) > 0:
        print(Fore.GREEN + "\nNumeric summary (mean ± std, min, max):")
        summary = df[numeric_cols].describe().T
        for col in numeric_cols:
            row = summary.loc[col]
            mean = row["mean"]
            std = row["std"]
            _min = row["min"]
            _max = row["max"]
            print(Fore.GREEN + f"  {col}: mean={mean:.3f}, std={std:.3f}, min={_min:.3f}, max={_max:.3f}")
    else:
        print(Fore.GREEN + "No numeric columns found for summary statistics.")

    # Correlation analysis
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr().abs()
        pairs: list[tuple[str, str, float]] = []
        for i, c1 in enumerate(numeric_cols):
            for c2 in numeric_cols[i+1:]:
                pairs.append((c1, c2, corr.loc[c1, c2]))
        pairs.sort(key=lambda x: x[2], reverse=True)
        print(Fore.YELLOW + "\nTop correlations:")
        for c1, c2, val in pairs[:5]:
            print(Fore.YELLOW + f"  {c1} vs {c2}: {val:.3f}")
    else:
        print(Fore.YELLOW + "Not enough numeric columns to compute correlations.")

    # Domain distribution
    if domain_col:
        print(Fore.CYAN + f"\nDomain distribution for '{domain_col}':")
        counts = df[domain_col].value_counts()
        for val, count in counts.items():
            print(Fore.CYAN + f"  {val}: {count}")

    # Outlier detection on numeric features
    if len(numeric_cols) > 0:
        try:
            iso = IsolationForest(random_state=42, contamination='auto')
            iso.fit(df[numeric_cols])
            scores = -iso.decision_function(df[numeric_cols])
            # indices of top 5 anomalies
            top_idx = scores.argsort()[-5:][::-1]
            print(Fore.RED + "\nTop 5 potential outliers (by index and anomaly score):")
            for idx in top_idx:
                score = scores[idx]
                print(Fore.RED + f"  Index {idx}: score={score:.4f}")
        except Exception as e:
            print(Fore.RED + f"Failed to run outlier detection: {e}")
    else:
        print(Fore.RED + "No numeric columns available for outlier detection.")


if __name__ == "__main__":
    main()