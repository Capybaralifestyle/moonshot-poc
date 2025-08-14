"""Dataset analysis CLI for Moonshot POC v3.

This script allows you to run the DatasetMLAgent directly from the command
line without invoking the other LLM-based agents.  It loads the dataset
specified by the DATASET_PATH environment variable (or a path provided via
--dataset), performs preprocessing and cross-validated training, and prints
evaluation metrics with colored output.

Usage:
    python src/cli_dataset.py --dataset path/to/dataset.arff

If no --dataset is provided, the script uses the DATASET_PATH environment
variable.  See DatasetMLAgent for supported formats and options.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict

from colorama import init, Fore, Style

from src.agents.dataset_ml_agent import DatasetMLAgent


def main(argv: list[str] | None = None) -> None:
    init(autoreset=True)
    parser = argparse.ArgumentParser(
        description=(
            "Run the dataset-based estimator on a dataset file and display metrics."
        )
    )
    parser.add_argument(
        "--dataset",
        help=(
            "Path to a CSV or ARFF file containing effort data. If omitted, the "
            "script uses the DATASET_PATH environment variable."
        ),
    )
    args = parser.parse_args(argv)

    if args.dataset:
        os.environ["DATASET_PATH"] = args.dataset
    agent = DatasetMLAgent()
    result: Dict[str, Any] = agent.analyze({})
    # Handle errors
    if "_error" in result:
        print(Fore.RED + f"Error: {result['_error']}")
        sys.exit(1)

    # Display summary in a readable, colorized format
    print(Fore.GREEN + "Dataset analysis completed successfully" + Style.RESET_ALL)
    print(Fore.WHITE + Style.BRIGHT + "===== Dataset Summary =====" + Style.RESET_ALL)
    # Path and target
    print(Fore.CYAN + f"Dataset path: {result.get('dataset_path')}")
    print(Fore.CYAN + f"Target column: {result.get('target_column')}")
    # Best model
    print(Fore.GREEN + f"\nBest model: {result.get('best_model')}")
    print(Fore.GREEN + f"  RMSE: {result.get('best_model_rmse'):.4f}")
    print(Fore.GREEN + f"  MAE: {result.get('best_model_mae'):.4f}")
    # Top features
    top_feats = result.get("top_features", {})
    if top_feats:
        print(Fore.MAGENTA + "\nTop 5 feature importances (best model):")
        for feat, val in top_feats.items():
            print(Fore.MAGENTA + f"  {feat}: {val:.4f}")
    # Prediction interval
    pred_int = result.get("prediction_interval")
    if pred_int:
        print(Fore.YELLOW + "\nEstimated prediction interval (residual quantiles):")
        print(Fore.YELLOW + f"  Lower quantile: {pred_int['lower_residual_quantile']:.4f}")
        print(Fore.YELLOW + f"  Upper quantile: {pred_int['upper_residual_quantile']:.4f}")
        print(Fore.YELLOW + f"  Interval width: {pred_int['interval_width']:.4f}")
    # Outliers
    outliers = result.get("outliers")
    if outliers:
        print(Fore.RED + "\nTop potential outliers:")
        for out in outliers:
            idx = out.get("row_index")
            score = out.get("score")
            eff = out.get("effort")
            dom = out.get("domain")
            line = f"  Index {idx}: score={score:.4f}, effort={eff:.4f}"
            if dom:
                line += f", domain={dom}"
            print(Fore.RED + line)
    # Domain‑specific models
    dom_res = result.get("domain_specific_models")
    if dom_res:
        print(Fore.CYAN + "\nDomain‑specific model summaries:")
        for dval, info in dom_res.items():
            print(Fore.CYAN + f"  Domain {dval} (n={info.get('count')}):")
            print(Fore.CYAN + f"    Best model: {info.get('best_model')}\n      RMSE: {info.get('best_rmse'):.4f}, MAE: {info.get('best_mae'):.4f}")
    # All models metrics
    all_models = result.get("all_models", {})
    if all_models:
        print(Fore.WHITE + Style.BRIGHT + "\nAll candidate models:")
        for name, metrics in all_models.items():
            print(Fore.WHITE + f"  {name}: RMSE={metrics['rmse']:.4f}, MAE={metrics['mae']:.4f}")


if __name__ == "__main__":
    main()